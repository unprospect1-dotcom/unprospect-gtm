#!/usr/bin/env python3
"""Baja clean_text de Supabase para que un subagente lo lea. Agnóstico al harness (stdlib + requests).

  python fetch_ct.py dom1.com dom2.mx ...      # dominios sueltos
  python fetch_ct.py --batch batches/batch_03.txt   # un archivo con un dominio por línea
  python fetch_ct.py --batch ... --outdir /ruta --maxchars 8000

Escribe <outdir>/ct_<dominio>.txt (truncado a --maxchars). Por defecto outdir = el mismo
directorio del archivo batch, o el cwd si son dominios sueltos.
"""
import os, sys, argparse, requests

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("domains", nargs="*")
    ap.add_argument("--batch")
    ap.add_argument("--outdir")
    ap.add_argument("--maxchars", type=int, default=8000)
    a = ap.parse_args()

    U = os.environ["SUPABASE_URL"].rstrip("/"); K = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    H = {"apikey": K, "authorization": f"Bearer {K}"}

    doms = list(a.domains)
    if a.batch:
        doms += [l.strip() for l in open(a.batch, encoding="utf-8") if l.strip()]
    outdir = a.outdir or (os.path.dirname(os.path.abspath(a.batch)) if a.batch else os.getcwd())
    os.makedirs(outdir, exist_ok=True)

    for dom in doms:
        r = requests.get(f"{U}/rest/v1/site_crawls",
                         params={"select": "clean_text", "domain": f"eq.{dom}"}, headers=H, timeout=60)
        js = r.json()
        ct = (js[0]["clean_text"] if js and js[0].get("clean_text") else "") or ""
        open(f"{outdir}/ct_{dom}.txt", "w", encoding="utf-8").write(ct[:a.maxchars])
        print(f"{dom}: {len(ct)} ch -> ct_{dom}.txt ({'VACIO' if not ct else 'ok'})")

if __name__ == "__main__":
    main()
