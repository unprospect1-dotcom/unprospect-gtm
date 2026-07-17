#!/usr/bin/env python3
"""gtm-web-crawler — dado un dominio, navega solo las secciones de alto valor y
extrae markdown limpio para personalización de cold email.

Motor: crawl4ai (render JS + markdown + deep-crawl priorizado). Un solo camino,
robusto: rinde SPAs, navega secciones (nosotros/servicios/aviso de privacidad),
$0 y self-host. Ver BENCHMARK.md para por qué este y no trafilatura/scrapy.

Uso:
  python crawl.py DOMINIO [DOMINIO...]           # uno o varios dominios
  python crawl.py --input dominios.txt           # archivo (un dominio por linea, o CSV con col 'domain')
  python crawl.py paya.com.mx --out salida --max-pages 6 --depth 1 --concurrency 4

Salida: <out>/<dominio>.json con raw/fit recuperable, evidencia visual y clean_text compacto.
Reanuda solo (--resume por defecto): si ya existe <dominio>.json, lo salta.
"""
import argparse, asyncio, csv, hashlib, json, os, re, sys, time
from urllib.parse import urlparse
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

def build_run_config(domain, depth, max_pages):
    from crawl4ai import CrawlerRunConfig, CacheMode
    from crawl4ai.deep_crawling import (BestFirstCrawlingStrategy, FilterChain,
                                        DomainFilter, KeywordRelevanceScorer)
    from crawl4ai.content_filter_strategy import PruningContentFilter
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    strat = BestFirstCrawlingStrategy(
        max_depth=depth, max_pages=max_pages,
        url_scorer=KeywordRelevanceScorer(keywords=HIGH_VALUE_KW, weight=1.0),
        filter_chain=FilterChain([DomainFilter(allowed_domains=[domain])]),
    )
    # filtro de densidad: tira menús/footers/boilerplate de baja densidad (-> fit_markdown)
    mdgen = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed"))
    return CrawlerRunConfig(
        deep_crawl_strategy=strat, cache_mode=CacheMode.BYPASS,
        markdown_generator=mdgen,
        wait_until="domcontentloaded", delay_before_return_html=3.0,
        page_timeout=45000, scan_full_page=True, verbose=False, stream=False,
    )


def build_home_config():
    from crawl4ai import CrawlerRunConfig, CacheMode
    from crawl4ai.content_filter_strategy import PruningContentFilter
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed")
        ),
        wait_until="domcontentloaded", delay_before_return_html=1.5,
        page_timeout=20000, scan_full_page=True, verbose=False,
    )


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


async def crawl_one(crawler, domain, depth, max_pages):
    t0 = time.time()
    try:
        results = await crawler.arun(f"https://{domain}", config=build_run_config(domain, depth, max_pages))
        if not isinstance(results, list):
            results = [results]
        pages, seen_paths, seen_content = [], set(), set()
        for r in results:
            page = _page_from_result(r)
            if not page:
                continue
            key = page["path"]
            # Dedupe estable sobre TODO el contenido. Los primeros 500 chars suelen ser el
            # mismo header y antes podían tirar páginas distintas con información útil.
            normalized = " ".join(page["markdown"].split())
            sig = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            if key in seen_paths or sig in seen_content:
                continue
            seen_paths.add(key); seen_content.add(sig)
            pages.append(page)
        return _finalize(domain, pages, t0)
    except Exception as e:
        return {"domain": domain, "ok": False, "n_pages": 0,
                "secs": round(time.time() - t0, 1), "error": str(e)[:200],
                "pages": [], "combined_markdown": ""}


async def crawl_home(crawler, domain, fallback):
    t0 = time.time()
    errors = []
    for scheme in ("https", "http"):
        try:
            result = await crawler.arun(f"{scheme}://{domain}", config=build_home_config())
            results = result if isinstance(result, list) else [result]
            pages = [page for page in (_page_from_result(item) for item in results) if page]
            if pages:
                out = _finalize(domain, pages[:1], t0, fallback=fallback)
                out["home_scheme"] = scheme
                return out
        except Exception as exc:
            errors.append(str(exc)[:100])
    out = _finalize(domain, [], t0, fallback=fallback)
    if errors:
        out["error"] = " | ".join(errors)[:200]
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

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("domains", nargs="*")
    ap.add_argument("--input")
    ap.add_argument("--out", default="crawl_out")
    ap.add_argument("--max-pages", type=int, default=6)
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--domain-timeout", type=int, default=180,
                    help="segundos máximos por dominio completo (def 180).")
    ap.add_argument("--shard-count", type=int, default=1,
                    help="número total de workers con listas separadas (def 1).")
    ap.add_argument("--shard-index", type=int, default=0,
                    help="índice de este worker, desde 0 (def 0).")
    ap.add_argument("--cycle-size", type=int, default=0,
                    help="cerrar Chrome tras N dominios; 0 procesa todos (def 0).")
    ap.add_argument("--no-resume", action="store_true")
    ap.add_argument("--supabase", action="store_true",
                    help="persistir cada resultado a la tabla site_crawls (requiere SUPABASE_*).")
    ap.add_argument("--skip-ensure-table", action="store_true",
                    help=argparse.SUPPRESS)
    args = ap.parse_args()

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
    from crawl4ai import AsyncWebCrawler, BrowserConfig
    from crawl4ai.async_configs import ProxyConfig

    all_todo = [d for d in domains if args.no_resume or
                not os.path.exists(os.path.join(args.out, f"{d}.json"))]
    more_after_cycle = args.cycle_size > 0 and len(all_todo) > args.cycle_size
    todo = all_todo[:args.cycle_size] if args.cycle_size > 0 else all_todo
    print(
        f"{len(domains)} dominios ({len(domains)-len(all_todo)} ya hechos, "
        f"{len(all_todo)} pendientes; lote actual {len(todo)})",
        flush=True,
    )

    browser_kwargs = {
        "headless": True,
        "extra_args": sb.LAUNCH_ARGS,
        "light_mode": True,
        "memory_saving_mode": True,
        # El reciclado interno de crawl4ai 0.9.1 deja procesos Chrome huérfanos
        # en Windows. El supervisor recicla el proceso completo por lotes.
        "max_pages_before_recycle": 0,
    }
    if sb.PROXY:
        browser_kwargs["proxy_config"] = ProxyConfig(server=sb.PROXY)
    bc = BrowserConfig(**browser_kwargs)
    sem = asyncio.Semaphore(args.concurrency)
    ok = fail = 0
    async with AsyncWebCrawler(config=bc) as crawler:
        async def worker(d):
            nonlocal ok, fail
            async with sem:
                try:
                    home = await asyncio.wait_for(crawl_home(crawler, d, None), timeout=30)
                except asyncio.TimeoutError:
                    home = {"domain": d, "ok": False, "n_pages": 0, "pages": [],
                            "combined_markdown": "", "clean_text": "",
                            "reason": "home_timeout"}
                if browser_is_unavailable(home):
                    raise BrowserUnavailable(
                        f"Chrome no disponible mientras se procesaba {d}: "
                        f"{home.get('error', '')[:120]}"
                    )
                if args.max_pages <= 1 or _home_is_enough(home):
                    res = home
                    res["crawl_mode"] = "home_sufficient" if home.get("ok") else "home_only"
                else:
                    try:
                        deep = await asyncio.wait_for(
                            crawl_one(crawler, d, args.depth, args.max_pages),
                            timeout=args.domain_timeout,
                        )
                    except asyncio.TimeoutError:
                        deep = {"domain": d, "ok": False, "n_pages": 0,
                                "secs": float(args.domain_timeout), "pages": [],
                                "combined_markdown": "", "clean_text": "",
                                "clean_meta": {"version": "2.1", "input_chars": 0,
                                               "context_chars": 0,
                                               "context_categories": []},
                                "reason": "deep_timeout"}
                    if browser_is_unavailable(deep):
                        raise BrowserUnavailable(
                            f"Chrome no disponible mientras se procesaba {d}: "
                            f"{deep.get('error', '')[:120]}"
                        )
                    if deep.get("ok"):
                        res = deep
                        res["crawl_mode"] = "deep_for_missing_signals"
                    elif home.get("ok"):
                        res = home
                        res["fallback"] = "home_after_deep_failure"
                        res["crawl_mode"] = "home_fallback"
                    else:
                        res = deep
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
