#!/usr/bin/env python3
"""Prepara los lotes de dominios para despachar subagentes clasificadores. Agnóstico al harness.

Saca de Supabase los dominios con crawl útil (site_crawls.ok, clean_text no nulo) que
todavía NO están clasificados en b2b_classification, y los parte en lotes de --size.
Escribe <outdir>/batch_NN.txt (un dominio por línea) e imprime el plan de despacho.

  python make_batches.py --size 40 --outdir batches
  python make_batches.py --size 40 --outdir batches --reclassify   # incluye ya clasificados

Luego: el orquestador lanza UN subagente por batch_NN.txt (ver SKILL.md). Es resumible:
al re-correr, ya no incluye los que quedaron en b2b_classification.
"""
import os, sys, argparse, math, requests

def get_all(url, headers, params):
    # pagina en bloques de 1000 (límite por defecto de PostgREST)
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
    ap.add_argument("--size", type=int, default=40)
    ap.add_argument("--outdir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "batches"))
    ap.add_argument("--reclassify", action="store_true")
    a = ap.parse_args()

    U = os.environ["SUPABASE_URL"].rstrip("/"); K = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    H = {"apikey": K, "authorization": f"Bearer {K}"}

    crawled = {x["domain"] for x in get_all(f"{U}/rest/v1/site_crawls", H,
               {"select": "domain", "ok": "eq.true", "clean_text": "not.is.null"})}
    done = set()
    if not a.reclassify:
        done = {x["domain"] for x in get_all(f"{U}/rest/v1/b2b_classification", H, {"select": "domain"})}
    todo = sorted(crawled - done)

    os.makedirs(a.outdir, exist_ok=True)
    # limpia batches viejos
    for f in os.listdir(a.outdir):
        if f.startswith("batch_") and f.endswith(".txt"): os.remove(os.path.join(a.outdir, f))

    n = math.ceil(len(todo) / a.size) if todo else 0
    for i in range(n):
        chunk = todo[i*a.size:(i+1)*a.size]
        open(f"{a.outdir}/batch_{i:02d}.txt", "w", encoding="utf-8").write("\n".join(chunk) + "\n")

    print(f"crawleados útiles: {len(crawled)} | ya clasificados: {len(done)} | por clasificar: {len(todo)}")
    print(f"lotes de {a.size}: {n}  ->  {a.outdir}/batch_00.txt .. batch_{max(n-1,0):02d}.txt")
    if n:
        print(f"\nDespacha {n} subagentes (modelo más barato del harness), uno por lote. Cada uno:")
        print(f"  1) python3 {os.path.join(os.path.dirname(os.path.abspath(__file__)),'fetch_ct.py')} --batch <batch_NN.txt>")
        print(f"  2) leer cada ct_<dom>.txt, clasificar con PROMPT.md")
        print(f"  3) escribir cls_<NN>.jsonl (una línea JSON por dominio)")

if __name__ == "__main__":
    main()
