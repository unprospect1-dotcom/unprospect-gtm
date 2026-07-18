#!/usr/bin/env python3
"""Materializa lotes + contexto para los subagentes clasificadores. Agnóstico al harness.

Reemplaza el patrón viejo (cada worker corre fetch_ct.py y lee 12 archivos = 12 requests
HTTP y 12 turnos de lectura POR WORKER) por una sola descarga masiva del orquestador:

  - <outdir>/re_NN.txt   lista de dominios del lote (uno por línea)
  - <outdir>/ctx_NN.txt  UN archivo con el clean_text de todo el lote, en bloques
                         "=== dominio ===" truncados a --maxchars (default 8000)

El worker solo hace: Read ctx_NN.txt -> clasificar -> Write rcls_NN.jsonl. Cero red,
cero Bash, mínimo de turnos.

Fuentes de dominios:
  python3 make_context.py --pending                # crawleados sin clasificar (default)
  python3 make_context.py --unverified             # b2b_classification.verified=false
                                                   # (re-run de los lotes-40 sesgados)
  python3 make_context.py --domains-file lista.txt # lista explícita

Opciones: --size 12 (NO subir de 15: ver LEARNINGS), --maxchars 8000 (NO bajar de 7000),
--outdir batches. Resumible: --pending excluye lo ya clasificado al re-correr.
"""
import os, sys, argparse, math, requests

CHUNK = 40  # dominios por request al pedir clean_text con in.() (URL acotada)


def get_all(url, headers, params):
    out, off = [], 0
    while True:
        p = dict(params); p["limit"] = "1000"; p["offset"] = str(off)
        r = requests.get(url, params=p, headers=headers, timeout=120)
        js = r.json()
        if not isinstance(js, list) or not js:
            break
        out += js
        if len(js) < 1000:
            break
        off += 1000
    return out


def fetch_texts(base, headers, domains, maxchars):
    texts = {}
    for i in range(0, len(domains), CHUNK):
        chunk = domains[i:i + CHUNK]
        quoted = ",".join('"%s"' % d for d in chunk)
        r = requests.get(f"{base}/rest/v1/site_crawls",
                         params={"select": "domain,clean_text", "domain": f"in.({quoted})"},
                         headers=headers, timeout=120)
        for row in r.json():
            texts[row["domain"]] = (row.get("clean_text") or "")[:maxchars]
    return texts


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--pending", action="store_true")
    src.add_argument("--unverified", action="store_true")
    src.add_argument("--domains-file")
    ap.add_argument("--size", type=int, default=12)
    ap.add_argument("--maxchars", type=int, default=8000)
    ap.add_argument("--outdir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "batches"))
    a = ap.parse_args()
    if a.size > 15:
        sys.exit("--size > 15 degrada al clasificador barato (sesgo b2b, ver LEARNINGS.md)")
    if a.maxchars < 7000:
        sys.exit("--maxchars < 7000 trunca el hero real (regla 2 de LEARNINGS.md)")

    U = os.environ["SUPABASE_URL"].rstrip("/"); K = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    H = {"apikey": K, "authorization": f"Bearer {K}"}

    if a.domains_file:
        todo = sorted({l.strip() for l in open(a.domains_file, encoding="utf-8") if l.strip()})
    elif a.unverified:
        rows = get_all(f"{U}/rest/v1/b2b_classification", H, {"select": "domain,verified"})
        todo = sorted(x["domain"] for x in rows if not x["verified"])
    else:
        crawled = {x["domain"] for x in get_all(f"{U}/rest/v1/site_crawls", H,
                   {"select": "domain", "ok": "eq.true", "clean_text": "not.is.null"})}
        done = {x["domain"] for x in get_all(f"{U}/rest/v1/b2b_classification", H, {"select": "domain"})}
        todo = sorted(crawled - done)

    texts = fetch_texts(U, H, todo, a.maxchars)
    os.makedirs(a.outdir, exist_ok=True)
    n = math.ceil(len(todo) / a.size) if todo else 0
    empty = 0
    for i in range(n):
        chunk = todo[i * a.size:(i + 1) * a.size]
        open(f"{a.outdir}/re_{i:02d}.txt", "w", encoding="utf-8").write("\n".join(chunk) + "\n")
        blocks = []
        for dom in chunk:
            ct = texts.get(dom, "")
            if not ct:
                empty += 1
            blocks.append(f"=== {dom} ===\n{ct}\n")
        open(f"{a.outdir}/ctx_{i:02d}.txt", "w", encoding="utf-8").write("\n".join(blocks))

    print(f"dominios: {len(todo)} | lotes de {a.size}: {n} | sin clean_text (van a unclear): {empty}")
    if n:
        print(f"-> {a.outdir}/re_00.txt + ctx_00.txt .. re_{n-1:02d}.txt + ctx_{n-1:02d}.txt")
        print("Despacha 1 worker barato por lote (Claude Code: agente gtm-classifier; "
              "Codex: lane gtm_classifier), en oleadas paralelas de ~10.")


if __name__ == "__main__":
    main()
