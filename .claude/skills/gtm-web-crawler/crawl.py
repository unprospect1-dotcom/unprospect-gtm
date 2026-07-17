#!/usr/bin/env python3
"""gtm-web-crawler — dado un dominio, navega solo las secciones de alto valor y
extrae markdown limpio para personalización de cold email.

Motor: Crawl4AI 0.9.2. Primero usa su crawler HTTP; abre Chromium sólo para
SPAs/JS o señales faltantes y navega directamente las secciones de mayor valor.
$0 y self-host. Ver BENCHMARK.md para las mediciones y decisiones.

Uso:
  python crawl.py DOMINIO [DOMINIO...]           # uno o varios dominios
  python crawl.py --input dominios.txt           # archivo (un dominio por linea, o CSV con col 'domain')
  python crawl.py paya.com.mx --out salida --max-pages 6 --depth 1 --concurrency 4

Salida: <out>/<dominio>.json con raw/fit recuperable, evidencia visual y clean_text compacto.
Reanuda solo: salta éxitos y rescata una vez los fallos previos.
"""
import argparse, asyncio, csv, hashlib, json, os, re, sys, time
from urllib.parse import urljoin, urlparse
import sandbox_browser as sb
from clean_markdown import build_segmentation_context, extract_evidence_links, extract_visual_assets


BROWSER_FATAL_MARKERS = (
    "target page, context or browser has been closed",
    "targetclosederror",
    "browser has been closed",
    "browser closed",
    "playwright connection closed",
    "connection closed while reading from the driver",
)


class BrowserUnavailable(RuntimeError):
    """Chrome completo murio; el supervisor debe reiniciar sin marcar el dominio."""


class SupabaseUnavailable(RuntimeError):
    """El resultado no se marca completo hasta confirmar su upsert."""


def select_shard(domains, shard_count=1, shard_index=0):
    """Divide una lista de forma estable para que varios procesos no se dupliquen."""
    if shard_count < 1:
        raise ValueError("shard_count debe ser >= 1")
    if not 0 <= shard_index < shard_count:
        raise ValueError("shard_index debe estar entre 0 y shard_count - 1")
    return [domain for index, domain in enumerate(domains)
            if index % shard_count == shard_index]


def browser_is_unavailable(result):
    error = str((result or {}).get("error") or "").lower()
    return any(marker in error for marker in BROWSER_FATAL_MARKERS)

# Palabras que suben el score de un link -> a esas secciones vamos primero.
HIGH_VALUE_KW = [
    "nosotros", "quienes-somos", "about", "empresa", "compania", "company",
    "servicios", "productos", "soluciones", "services", "products",
    "clientes", "customer", "casos", "case-studies", "testimonios", "testimonial",
    "sectores", "industrias", "industries", "contacto", "contact",
]

HIGH_VALUE_WEIGHTS = {
    "casos": 120, "case-studies": 120, "case-study": 120,
    "clientes": 110, "customers": 110, "testimonios": 105, "testimonials": 105,
    "servicios": 95, "services": 95, "productos": 95, "products": 95,
    "soluciones": 95, "solutions": 95, "industrias": 85, "industries": 85,
    "sectores": 85, "nosotros": 75, "quienes-somos": 75, "about": 75,
    "empresa": 65, "company": 65, "contacto": 20, "contact": 20,
}

SKIP_LINK_SUFFIXES = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
    ".css", ".js", ".zip", ".rar", ".mp3", ".mp4", ".avi", ".mov",
)

def read_domains(args):
    doms = []
    if args.input:
        with open(args.input, encoding="utf-8-sig") as f:
            head = f.readline()
            if "," in head and "domain" in head.lower():           # CSV con header
                f.seek(0)
                for row in csv.DictReader(f):
                    d = (row.get("domain") or "").strip()
                    if d:
                        doms.append(d)
            else:
                if head.strip():
                    doms.append(head.strip())
                doms += [l.strip() for l in f if l.strip()]
    doms += args.domains
    # normaliza: sin esquema, sin www, sin barra final
    out, seen = [], set()
    for d in doms:
        d = d.replace("https://", "").replace("http://", "").replace("www.", "").strip().strip("/")
        d = d.split("/")[0]
        if d and d not in seen:
            seen.add(d); out.append(d)
    return out

def _markdown_generator():
    from crawl4ai.content_filter_strategy import PruningContentFilter
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    return DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed")
    )


def build_http_config():
    from crawl4ai import CrawlerRunConfig, CacheMode
    from crawl4ai.async_configs import ProxyConfig
    kwargs = {
        "cache_mode": CacheMode.BYPASS,
        "markdown_generator": _markdown_generator(),
        "page_timeout": 15000,
        "verbose": False,
        "stream": False,
    }
    if sb.PROXY:
        kwargs["proxy_config"] = ProxyConfig(server=sb.PROXY)
    return CrawlerRunConfig(**kwargs)


def build_browser_config(slow=False):
    from crawl4ai import CrawlerRunConfig, CacheMode
    from crawl4ai.async_configs import ProxyConfig
    kwargs = dict(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=_markdown_generator(),
        wait_until="domcontentloaded",
        delay_before_return_html=1.5 if slow else 0.4,
        page_timeout=30000 if slow else 20000,
        scan_full_page=bool(slow),
        max_scroll_steps=6 if slow else None,
        scroll_delay=0.05,
        verbose=False,
        stream=False,
    )
    if sb.PROXY:
        kwargs["proxy_config"] = ProxyConfig(server=sb.PROXY)
    return CrawlerRunConfig(**kwargs)


def _page_from_result(result):
    if not result.success:
        return None
    if hasattr(result.markdown, "raw_markdown"):
        raw_md = getattr(result.markdown, "raw_markdown", "") or ""
        fit_md = getattr(result.markdown, "fit_markdown", "") or ""
    else:
        raw_md = str(result.markdown or "")
        fit_md = ""
    md = fit_md or raw_md
    short_but_useful = bool(re.search(
        r"@|\+?\d[\d\s().-]{7,}|ISO\s?\d+|servicio|producto|soluci[oó]n|cliente|caso",
        md or "", re.IGNORECASE))
    if not md or (len(md) < 80 and not short_but_useful):
        return None
    parsed_url = urlparse(result.url)
    path = (parsed_url.path or "/").rstrip("/") or "/"
    evidence_source = raw_md or md
    return {
        "url": result.url,
        "path": path,
        "chars": len(md),
        "markdown": md,
        "raw_markdown": raw_md if raw_md and raw_md != md else None,
        "visual_assets": extract_visual_assets(evidence_source, path)[:30],
        "evidence_links": extract_evidence_links(evidence_source, path)[:30],
    }


def _finalize(domain, pages, started_at, fallback=None):
    combined = "\n\n---\n\n".join(f"# {p['path']}\n{p['markdown']}" for p in pages)
    analysis = build_segmentation_context(combined)
    summary_keys = {
        "version", "input_chars", "clean_chars", "context_chars", "clean_items",
        "context_items", "categories", "context_categories", "dropped",
        "entity_recall_clean", "entity_recall_context",
    }
    out = {"domain": domain, "ok": bool(pages), "n_pages": len(pages),
           "secs": round(time.time() - started_at, 1), "pages": pages,
           "combined_markdown": combined, "clean_text": analysis["text"],
           "clean_meta": {key: value for key, value in analysis["meta"].items()
                          if key in summary_keys}}
    if fallback:
        out["fallback"] = fallback
    if not pages:
        out["reason"] = "sin_contenido_util__escalar_a_capa_B_agentica"
    return out


def _normalized_host(value):
    return (value or "").lower().split(":")[0].removeprefix("www.")


def select_high_value_links(result, domain, limit):
    """Elige pocas páginas útiles sin volver a recorrer el home ni salir del sitio."""
    if limit <= 0:
        return []
    links = (getattr(result, "links", None) or {}).get("internal", [])
    result_url = getattr(result, "url", "") or f"https://{domain}"
    allowed_hosts = {
        _normalized_host(domain),
        _normalized_host(urlparse(result_url).hostname),
    }
    scored, seen = [], set()
    for item in links:
        if isinstance(item, str):
            href, text = item, ""
        else:
            href = (item or {}).get("href") or ""
            text = " ".join(str((item or {}).get(key) or "")
                            for key in ("text", "title", "base_domain"))
        if not href:
            continue
        href = urljoin(result_url, href).split("#", 1)[0]
        parsed = urlparse(href)
        if parsed.scheme not in {"http", "https"}:
            continue
        if _normalized_host(parsed.hostname) not in allowed_hosts:
            continue
        lowered_path = (parsed.path or "/").lower().rstrip("/") or "/"
        if lowered_path == "/" or lowered_path.endswith(SKIP_LINK_SUFFIXES):
            continue
        canonical = f"{parsed.scheme}://{parsed.netloc}{lowered_path}"
        if canonical in seen:
            continue
        haystack = f"{lowered_path} {text.lower()}"
        score = sum(weight for keyword, weight in HIGH_VALUE_WEIGHTS.items()
                    if keyword in haystack)
        if score <= 0:
            continue
        # A igualdad de señal, preferimos URLs simples y páginas HTML.
        score -= lowered_path.count("/")
        if lowered_path.endswith(".pdf"):
            score -= 40
        seen.add(canonical)
        scored.append((score, href))
    scored.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    return [href for _, href in scored[:limit]]


def _append_unique_page(pages, page, seen_paths, seen_content):
    if not page:
        return False
    normalized = " ".join(page["markdown"].split())
    signature = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    if page["path"] in seen_paths or signature in seen_content:
        return False
    seen_paths.add(page["path"])
    seen_content.add(signature)
    pages.append(page)
    return True


async def crawl_site(crawler, domain, config, max_pages, fallback=None):
    """Home una sola vez; sólo abre páginas internas si faltan señales de segmentación."""
    started_at = time.time()
    pages, seen_paths, seen_content, errors = [], set(), set(), []
    candidates, home_scheme = [], None
    for scheme in ("https", "http"):
        try:
            raw_result = await crawler.arun(f"{scheme}://{domain}", config=config)
            results = raw_result if isinstance(raw_result, list) else [raw_result]
            for result in results:
                if not getattr(result, "success", False):
                    error = getattr(result, "error_message", "") or "crawl_failed"
                    errors.append(str(error)[:160])
                    continue
                page = _page_from_result(result)
                if _append_unique_page(pages, page, seen_paths, seen_content):
                    candidates = select_high_value_links(
                        result, domain, max(0, max_pages - 1)
                    )
                    home_scheme = scheme
                    break
                errors.append("no_usable_content")
            if pages:
                break
        except Exception as exc:
            errors.append(str(exc)[:160])

    interim = _finalize(domain, pages, started_at, fallback=fallback)
    if pages and max_pages > 1 and not _home_is_enough(interim):
        for href in candidates:
            if len(pages) >= max_pages:
                break
            try:
                raw_result = await crawler.arun(href, config=config)
                results = raw_result if isinstance(raw_result, list) else [raw_result]
                for result in results:
                    if getattr(result, "success", False):
                        _append_unique_page(
                            pages, _page_from_result(result), seen_paths, seen_content
                        )
                    else:
                        errors.append(str(getattr(result, "error_message", ""))[:160])
            except Exception as exc:
                errors.append(str(exc)[:160])

    out = _finalize(domain, pages, started_at, fallback=fallback)
    if home_scheme:
        out["home_scheme"] = home_scheme
    if errors and not pages:
        out["error"] = " | ".join(error for error in errors if error)[:400]
    return out


def _home_is_enough(result):
    if not result.get("ok") or len(result.get("clean_text") or "") < 300:
        return False
    categories = set((result.get("clean_meta") or {}).get("context_categories") or [])
    return (
        "offer" in categories
        and bool(categories & {"audience", "b2b"})
        and bool(categories & {"identity", "industry", "proof"})
    )


def resume_state(path, no_resume=False, max_attempts=2):
    """Los éxitos se saltan; un fallo viejo recibe un único intento de rescate."""
    if no_resume or not os.path.exists(path):
        return True, 0
    try:
        with open(path, encoding="utf-8") as handle:
            previous = json.load(handle)
    except (OSError, ValueError):
        return True, 0
    attempts = max(1, int(previous.get("crawl_attempts") or 1))
    if previous.get("ok"):
        return False, attempts
    return attempts < max_attempts, attempts


def should_try_slow_browser(result):
    error = str((result or {}).get("error") or "").lower()
    return not result.get("ok") and (not error or any(marker in error for marker in (
        "anti-bot", "script_heavy", "minimal_text", "no_content", "no_usable_content",
        "timeout", "acs-goto", "navigation", "crawl_failed",
    )))

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("domains", nargs="*")
    ap.add_argument("--input")
    ap.add_argument("--out", default="crawl_out")
    ap.add_argument("--max-pages", type=int, default=2)
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--http-concurrency", type=int, default=12,
                    help="requests HTTP ligeros en paralelo (def 12).")
    ap.add_argument("--domain-timeout", type=int, default=60,
                    help="segundos máximos por etapa de un dominio (def 60).")
    ap.add_argument("--shard-count", type=int, default=1,
                    help="número total de workers con listas separadas (def 1).")
    ap.add_argument("--shard-index", type=int, default=0,
                    help="índice de este worker, desde 0 (def 0).")
    ap.add_argument("--cycle-size", type=int, default=0,
                    help="cerrar Chrome tras N dominios; 0 procesa todos (def 0).")
    ap.add_argument("--max-attempts", type=int, default=2,
                    help="intentos totales por dominio fallido (def 2).")
    ap.add_argument("--http-only", action="store_true",
                    help="no abrir Chrome; útil para medir la primera capa.")
    ap.add_argument("--no-resume", action="store_true")
    ap.add_argument("--supabase", action="store_true",
                    help="persistir cada resultado a la tabla site_crawls (requiere SUPABASE_*).")
    ap.add_argument("--skip-ensure-table", action="store_true",
                    help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.max_pages < 1:
        ap.error("--max-pages debe ser >= 1")
    if args.concurrency < 1 or args.http_concurrency < 1:
        ap.error("--concurrency y --http-concurrency deben ser >= 1")
    if args.max_attempts < 1:
        ap.error("--max-attempts debe ser >= 1")

    sink = None
    if args.supabase:
        import load_supabase as sink
        if not args.skip_ensure_table:
            sink.ensure_table()

    try:
        domains = select_shard(read_domains(args), args.shard_count, args.shard_index)
    except ValueError as exc:
        ap.error(str(exc))
    if not domains:
        print(f"Worker {args.shard_index + 1}/{args.shard_count}: sin dominios asignados.",
              flush=True)
        return
    os.makedirs(args.out, exist_ok=True)

    sb.bootstrap_nss()
    sb.patch_crawl4ai()
    from crawl4ai import AsyncWebCrawler, BrowserConfig, HTTPCrawlerConfig
    from crawl4ai.async_configs import ProxyConfig
    from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
    from crawl4ai.__version__ import __version__ as crawl4ai_version

    resume = {}
    for domain in domains:
        output_path = os.path.join(args.out, f"{domain}.json")
        resume[domain] = resume_state(
            output_path, no_resume=args.no_resume, max_attempts=args.max_attempts
        )
    all_todo = [domain for domain, (should_run, _) in resume.items() if should_run]
    more_after_cycle = args.cycle_size > 0 and len(all_todo) > args.cycle_size
    todo = all_todo[:args.cycle_size] if args.cycle_size > 0 else all_todo
    print(
        f"{len(domains)} dominios ({len(domains)-len(all_todo)} ya hechos, "
        f"{len(all_todo)} pendientes; lote actual {len(todo)})",
        flush=True,
    )
    if not todo:
        return 0

    browser_kwargs = {
        "headless": True,
        "extra_args": sb.LAUNCH_ARGS,
        "light_mode": True,
        "avoid_css": True,
        "avoid_ads": True,
        "memory_saving_mode": True,
        # El supervisor recicla el proceso completo por lotes. La mayoría de los
        # sitios ya no toca Chrome porque se resuelve en la capa HTTP.
        "max_pages_before_recycle": 0,
    }
    if sb.PROXY:
        browser_kwargs["proxy_config"] = ProxyConfig(server=sb.PROXY)
    bc = BrowserConfig(**browser_kwargs)
    http_strategy = AsyncHTTPCrawlerStrategy(
        browser_config=HTTPCrawlerConfig(verify_ssl=False, follow_redirects=True),
        max_connections=max(args.http_concurrency, 4),
    )
    http_config = build_http_config()
    browser_config = build_browser_config(slow=False)
    slow_browser_config = build_browser_config(slow=True)
    http_sem = asyncio.Semaphore(args.http_concurrency)
    browser_sem = asyncio.Semaphore(args.concurrency)
    ok = fail = 0
    async with AsyncWebCrawler(crawler_strategy=http_strategy) as http_crawler, \
            AsyncWebCrawler(config=bc) as browser_crawler:
        async def worker(d):
            nonlocal ok, fail
            total_started = time.time()
            previous_attempts = resume[d][1]
            async with http_sem:
                try:
                    http_result = await asyncio.wait_for(
                        crawl_site(http_crawler, d, http_config, args.max_pages),
                        timeout=args.domain_timeout,
                    )
                except asyncio.TimeoutError:
                    http_result = _finalize(d, [], total_started, fallback="http_timeout")
                    http_result["error"] = "http_timeout"

            if _home_is_enough(http_result):
                res = http_result
                res["crawl_mode"] = "http_sufficient"
            elif args.http_only:
                res = http_result
                res["crawl_mode"] = "http_only"
            else:
                async with browser_sem:
                    try:
                        browser_result = await asyncio.wait_for(
                            crawl_site(
                                browser_crawler, d, browser_config, args.max_pages,
                                fallback="browser_after_http",
                            ),
                            timeout=args.domain_timeout,
                        )
                    except asyncio.TimeoutError:
                        browser_result = _finalize(
                            d, [], total_started, fallback="browser_fast_timeout"
                        )
                        browser_result["error"] = "browser_fast_timeout"
                    if browser_is_unavailable(browser_result):
                        raise BrowserUnavailable(
                            f"Chrome no disponible mientras se procesaba {d}: "
                            f"{browser_result.get('error', '')[:120]}"
                        )

                    slow_result = None
                    if (not http_result.get("ok")
                            and should_try_slow_browser(browser_result)):
                        try:
                            slow_result = await asyncio.wait_for(
                                crawl_site(
                                    browser_crawler, d, slow_browser_config,
                                    args.max_pages, fallback="slow_browser_retry",
                                ),
                                timeout=args.domain_timeout,
                            )
                        except asyncio.TimeoutError:
                            slow_result = _finalize(
                                d, [], total_started, fallback="browser_slow_timeout"
                            )
                            slow_result["error"] = "browser_slow_timeout"
                        if browser_is_unavailable(slow_result):
                            raise BrowserUnavailable(
                                f"Chrome no disponible mientras se procesaba {d}: "
                                f"{slow_result.get('error', '')[:120]}"
                            )

                if browser_result.get("ok"):
                    res = browser_result
                    res["crawl_mode"] = "browser_for_js_or_missing_signals"
                elif slow_result and slow_result.get("ok"):
                    res = slow_result
                    res["crawl_mode"] = "browser_slow_retry"
                elif http_result.get("ok"):
                    res = http_result
                    res["fallback"] = "http_after_browser_failure"
                    res["crawl_mode"] = "http_partial_fallback"
                else:
                    res = slow_result or browser_result
                    res["crawl_mode"] = "failed_after_cascade"
                    res["fallback_errors"] = {
                        "http": http_result.get("error"),
                        "browser": browser_result.get("error"),
                    }

            res["secs"] = round(time.time() - total_started, 1)
            res["crawl_attempts"] = previous_attempts + 1
            res["crawl_engine"] = f"crawl4ai-{crawl4ai_version}"
            output_path = os.path.join(args.out, f"{d}.json")
            temp_path = f"{output_path}.{os.getpid()}.tmp"
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(res, handle, indent=2, ensure_ascii=False)
            if sink:
                try:
                    sink.upsert([sink.to_row(res)])
                except Exception as e:
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                    raise SupabaseUnavailable(
                        f"Supabase no confirmo {d}: {str(e)[:120]}"
                    ) from e
            os.replace(temp_path, output_path)
            if res["ok"]:
                ok += 1
            else:
                fail += 1
            print(f"  {'OK ' if res['ok'] else 'XX '}{d:32} {res['n_pages']}p  {res['secs']}s"
                  + (f"  ERR {res.get('error','')[:60]}" if not res['ok'] else ""), flush=True)
        await asyncio.gather(*(worker(d) for d in todo))
    print(f"\nHecho: {ok} ok / {fail} fallidos. Salida en {args.out}/", flush=True)
    if more_after_cycle:
        print("CYCLE_COMPLETE: cerrando Chrome para liberar memoria.", flush=True)
        return 80
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        if exit_code:
            sys.exit(exit_code)
    except BrowserUnavailable as exc:
        print(f"RESTART_REQUIRED: {exc}", file=sys.stderr, flush=True)
        sys.exit(75)
    except SupabaseUnavailable as exc:
        print(f"RESTART_REQUIRED: {exc}", file=sys.stderr, flush=True)
        sys.exit(76)
