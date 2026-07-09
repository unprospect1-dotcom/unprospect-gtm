"""Bake-off resiliente: una etapa por proceso, escribe JSON incremental por dominio.
Uso: python bakeoff2.py <trafilatura|playwright|crawl4ai>
"""
import sys, time, json, os, asyncio
import sandbox_browser as sb

OUT = "bakeoff_results.json"
DOMAINS = ["paya.com.mx","a55.com.mx","aspiria.mx","factoring.mx",
           "blucapital.mx","apoyosofom.com","alcanacapital.com","ion.com.mx"]

def load():
    return json.load(open(OUT)) if os.path.exists(OUT) else {d: {} for d in DOMAINS}

def save(r):
    json.dump(r, open(OUT, "w"), indent=2, ensure_ascii=False)

def stage_trafilatura():
    import trafilatura, requests
    r = load()
    hdr = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
    for d in DOMAINS:
        t0 = time.time()
        try:
            try:
                html = requests.get(f"https://{d}", headers=hdr, timeout=25).text
            except Exception:
                html = None
            txt = trafilatura.extract(html, include_comments=False) if html else None
            r[d]["trafilatura"] = {"chars": len(txt or ""), "ok": bool(txt and len(txt) > 200),
                                    "secs": round(time.time()-t0, 1)}
        except Exception as e:
            r[d]["trafilatura"] = {"chars": 0, "ok": False, "err": str(e)[:60]}
        print("trafi", d, r[d]["trafilatura"]["chars"], flush=True); save(r)

def stage_playwright():
    import html2text
    from playwright.sync_api import sync_playwright
    h2t = html2text.HTML2Text(); h2t.ignore_links = True; h2t.ignore_images = True
    r = load()
    with sync_playwright() as p:
        b = p.chromium.launch(**sb.launch_kwargs())
        for d in DOMAINS:
            t0 = time.time()
            try:
                pg = b.new_page()
                pg.goto(f"https://{d}", timeout=45000, wait_until="domcontentloaded")
                pg.wait_for_timeout(3500)
                links = pg.eval_on_selector_all("a[href]", "els=>els.map(e=>e.href)")
                internal = set(l for l in links if d in l)
                vis = pg.evaluate("document.body?document.body.innerText:''")
                r[d]["playwright"] = {"chars": len(vis or ""), "ok": bool(vis and len(vis) > 200),
                                       "internal_links": len(internal), "secs": round(time.time()-t0, 1)}
                pg.close()
            except Exception as e:
                r[d]["playwright"] = {"chars": 0, "ok": False, "err": str(e)[:60]}
            print("pw", d, r[d]["playwright"].get("chars"), flush=True); save(r)
        b.close()

def stage_crawl4ai():
    sb.patch_crawl4ai()
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.async_configs import ProxyConfig
    async def run():
        r = load()
        bc = BrowserConfig(headless=True, proxy_config=ProxyConfig(server=sb.PROXY))
        cfg = CrawlerRunConfig(page_timeout=50000, wait_until="domcontentloaded",
                               delay_before_return_html=3.5, scan_full_page=True)
        async with AsyncWebCrawler(config=bc) as c:
            for d in DOMAINS:
                t0 = time.time()
                try:
                    res = await c.arun(f"https://{d}", config=cfg)
                    md = res.markdown.raw_markdown if hasattr(res.markdown, "raw_markdown") else str(res.markdown)
                    nlinks = len(res.links.get("internal", [])) if res.links else 0
                    r[d]["crawl4ai"] = {"chars": len(md or ""), "ok": bool(md and len(md) > 200),
                                         "internal_links": nlinks, "secs": round(time.time()-t0, 1)}
                except Exception as e:
                    r[d]["crawl4ai"] = {"chars": 0, "ok": False, "err": str(e)[:60]}
                print("c4ai", d, r[d]["crawl4ai"].get("chars"), flush=True); save(r)
    asyncio.run(run())

if __name__ == "__main__":
    sb.bootstrap_nss()
    {"trafilatura": stage_trafilatura, "playwright": stage_playwright,
     "crawl4ai": stage_crawl4ai}[sys.argv[1]]()
