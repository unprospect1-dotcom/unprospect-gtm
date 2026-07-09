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

Salida: <out>/<dominio>.json con {domain, ok, n_pages, pages:[{url,path,chars,markdown}], combined_markdown}
Reanuda solo (--resume por defecto): si ya existe <dominio>.json, lo salta.
"""
import argparse, asyncio, json, os, sys, time, csv
import sandbox_browser as sb

# Palabras que suben el score de un link -> a esas secciones vamos primero.
HIGH_VALUE_KW = [
    "nosotros", "quienes-somos", "about", "empresa", "compania", "company",
    "servicios", "productos", "soluciones", "services", "products",
    "aviso", "privacidad", "legal", "terminos", "privacy", "terms",
    "contacto", "contact", "clientes", "sectores", "industrias",
]

def read_domains(args):
    doms = []
    if args.input:
        with open(args.input) as f:
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
    strat = BestFirstCrawlingStrategy(
        max_depth=depth, max_pages=max_pages,
        url_scorer=KeywordRelevanceScorer(keywords=HIGH_VALUE_KW, weight=1.0),
        filter_chain=FilterChain([DomainFilter(allowed_domains=[domain])]),
    )
    return CrawlerRunConfig(
        deep_crawl_strategy=strat, cache_mode=CacheMode.BYPASS,
        wait_until="domcontentloaded", delay_before_return_html=3.0,
        page_timeout=45000, scan_full_page=True, verbose=False, stream=False,
    )

async def crawl_one(crawler, domain, depth, max_pages):
    t0 = time.time()
    try:
        results = await crawler.arun(f"https://{domain}", config=build_run_config(domain, depth, max_pages))
        if not isinstance(results, list):
            results = [results]
        pages, seen_paths, seen_content = [], set(), set()
        for r in results:
            if not r.success:
                continue
            md = r.markdown.raw_markdown if hasattr(r.markdown, "raw_markdown") else str(r.markdown)
            path = r.url.replace("https://", "").replace("http://", "").replace("www.", "")
            path = "/" + path.split("/", 1)[1] if "/" in path.split("//")[-1] else "/"
            key = path.rstrip("/") or "/"
            # dedupe por path Y por contenido (SPAs sirven el mismo home en varias rutas)
            sig = hash(" ".join((md or "").split())[:500])
            if key in seen_paths or sig in seen_content or not md or len(md) < 80:
                continue
            seen_paths.add(key); seen_content.add(sig)
            pages.append({"url": r.url, "path": key, "chars": len(md), "markdown": md})
        combined = "\n\n---\n\n".join(f"# {p['path']}\n{p['markdown']}" for p in pages)
        out = {"domain": domain, "ok": bool(pages), "n_pages": len(pages),
               "secs": round(time.time() - t0, 1), "pages": pages,
               "combined_markdown": combined}
        if not pages:
            # navego pero no salio contenido util: challenge/bot-protection o sitio muerto.
            out["reason"] = "sin_contenido_util__escalar_a_capa_B_agentica"
        return out
    except Exception as e:
        return {"domain": domain, "ok": False, "n_pages": 0,
                "secs": round(time.time() - t0, 1), "error": str(e)[:200],
                "pages": [], "combined_markdown": ""}

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("domains", nargs="*")
    ap.add_argument("--input")
    ap.add_argument("--out", default="crawl_out")
    ap.add_argument("--max-pages", type=int, default=6)
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--no-resume", action="store_true")
    args = ap.parse_args()

    domains = read_domains(args)
    if not domains:
        print("Sin dominios. Usa: python crawl.py DOMINIO  |  --input archivo", file=sys.stderr)
        sys.exit(2)
    os.makedirs(args.out, exist_ok=True)

    sb.bootstrap_nss()
    sb.patch_crawl4ai()
    from crawl4ai import AsyncWebCrawler, BrowserConfig
    from crawl4ai.async_configs import ProxyConfig

    todo = [d for d in domains if args.no_resume or
            not os.path.exists(os.path.join(args.out, f"{d}.json"))]
    print(f"{len(domains)} dominios ({len(domains)-len(todo)} ya hechos, {len(todo)} por crawl-ear)", flush=True)

    bc = BrowserConfig(headless=True, proxy_config=ProxyConfig(server=sb.PROXY))
    sem = asyncio.Semaphore(args.concurrency)
    ok = fail = 0
    async with AsyncWebCrawler(config=bc) as crawler:
        async def worker(d):
            nonlocal ok, fail
            async with sem:
                res = await crawl_one(crawler, d, args.depth, args.max_pages)
            json.dump(res, open(os.path.join(args.out, f"{d}.json"), "w"),
                      indent=2, ensure_ascii=False)
            if res["ok"]:
                ok += 1
            else:
                fail += 1
            print(f"  {'OK ' if res['ok'] else 'XX '}{d:32} {res['n_pages']}p  {res['secs']}s"
                  + (f"  ERR {res.get('error','')[:60]}" if not res['ok'] else ""), flush=True)
        await asyncio.gather(*(worker(d) for d in todo))
    print(f"\nHecho: {ok} ok / {fail} fallidos. Salida en {args.out}/", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
