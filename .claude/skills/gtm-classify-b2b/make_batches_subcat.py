#!/usr/bin/env python3
"""Prepara lotes PENDIENTES de subcategorización para un niche de list_companies.

Resumible por diseño: saca de Supabase los dominios del niche que (a) tienen crawl útil
en site_crawls y (b) aún NO tienen subcat en list_companies, y los parte en lotes de --size.

  python3 make_batches_subcat.py --niche autotransporte-mx --size 12 --outdir batches-transporte

Luego: un subagente (modelo más barato del harness) por lote, con WORKER_SUBCAT_TRANSPORTE.md.
Cargar resultados: python3 scripts/subcat_to_supabase.py --classify "…/subcat_*.jsonl" --niche <niche>
"""
import os, argparse, requests

def get_all(url, headers, params):
    out, off = [], 0
    while True:
        p = dict(params); p["limit"] = "1000"; p["offset"] = str(off)
        r = requests.get(url, params=p, headers=headers, timeout=120)
        js = r.json()
        if not isinstance(js, list) or not js: break
        out += js
        if len(js) < 1000: break
        off += 1000
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche", required=True)
    ap.add_argument("--size", type=int, default=12)
    ap.add_argument("--outdir", default="batches-subcat")
    a = ap.parse_args()

    U = os.environ["SUPABASE_URL"].rstrip("/"); K = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    H = {"apikey": K, "authorization": f"Bearer {K}"}

    pend = {r["domain"] for r in get_all(f"{U}/rest/v1/list_companies", H,
            {"select": "domain", "niche": f"eq.{a.niche}", "subcat": "is.null"})}
    crawled = {r["domain"] for r in get_all(f"{U}/rest/v1/site_crawls", H,
               {"select": "domain", "ok": "eq.true"})}
    doms = sorted(pend & crawled)

    os.makedirs(a.outdir, exist_ok=True)
    n = 0
    for i in range(0, len(doms), a.size):
        with open(os.path.join(a.outdir, f"batch_{i//a.size:03d}.txt"), "w") as f:
            f.write("\n".join(doms[i:i + a.size]))
        n = i // a.size + 1
    print(f"{len(doms)} dominios pendientes -> {n} lotes de {a.size} en {a.outdir}/")
    print(f"(sin crawl útil / fuera de site_crawls: {len(pend) - len(doms)} — se quedan sin subcat)")

if __name__ == "__main__":
    main()
