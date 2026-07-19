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
  python3 make_context.py --profile-pending        # company_gtm_profiles pending con crawl
  python3 make_context.py --domains-file lista.txt # lista explícita

Opciones: --size 12 (NO subir de 15: ver LEARNINGS), --maxchars 8000 (NO bajar de 7000),
--outdir batches, --skip N / --limit N para trocear corridas grandes (el número de lote
arranca en skip/size, así corridas por tramos no chocan). Resumible.
"""
import os, sys, argparse, math, requests

CHUNK = 100  # dominios por request al pedir clean_text con in.() (URL acotada)


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
    src.add_argument("--profile-pending", action="store_true")
    src.add_argument("--domains-file")
    ap.add_argument("--size", type=int, default=12)
    ap.add_argument("--maxchars", type=int, default=8000)
    ap.add_argument("--skip", type=int, default=0, help="salta los primeros N dominios (tramos)")
    ap.add_argument("--limit", type=int, default=0, help="máximo de dominios en esta corrida (0 = todos)")
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
    elif a.profile_pending:
        rows = get_all(f"{U}/rest/v1/company_gtm_profiles", H,
                       {"select": "domain", "profile_status": "eq.pending",
                        "source_crawl_ok": "eq.true", "source_clean_chars": "gt.500"})
        todo = sorted(x["domain"] for x in rows)
    else:
        crawled = {x["domain"] for x in get_all(f"{U}/rest/v1/site_crawls", H,
                   {"select": "domain", "ok": "eq.true", "clean_text": "not.is.null"})}
        done = {x["domain"] for x in get_all(f"{U}/rest/v1/b2b_classification", H, {"select": "domain"})}
        todo = sorted(crawled - done)

    total = len(todo)
    lot0 = a.skip // a.size
    todo = todo[a.skip:a.skip + a.limit if a.limit else None]

    texts = fetch_texts(U, H, todo, a.maxchars)
    os.makedirs(a.outdir, exist_ok=True)
    if a.skip == 0:  # corrida desde cero: limpia lotes viejos para no mezclar numeraciones
        for f in os.listdir(a.outdir):
            if (f.startswith(("re_", "ctx_")) and f.endswith(".txt")):
                os.remove(os.path.join(a.outdir, f))
    n = math.ceil(len(todo) / a.size) if todo else 0
    empty = 0
    for i in range(n):
        nn = lot0 + i
        chunk = todo[i * a.size:(i + 1) * a.size]
        open(f"{a.outdir}/re_{nn:04d}.txt", "w", encoding="utf-8").write("\n".join(chunk) + "\n")
        blocks = []
        for dom in chunk:
            ct = texts.get(dom, "")
            if not ct:
                empty += 1
            blocks.append(f"=== {dom} ===\n{ct}\n")
        open(f"{a.outdir}/ctx_{nn:04d}.txt", "w", encoding="utf-8").write("\n".join(blocks))

    print(f"universo: {total} | este tramo: {len(todo)} (skip {a.skip}) | lotes de {a.size}: {n} "
          f"| sin clean_text (van a unclear): {empty}")
    if n:
        print(f"-> {a.outdir}/re_{lot0:04d}.txt + ctx_{lot0:04d}.txt .. re_{lot0+n-1:04d}.txt + ctx_{lot0+n-1:04d}.txt")
        print("Despacha 1 worker barato por lote (Claude Code: agente gtm-classifier; "
              "Codex: lane gtm_classifier), en oleadas paralelas de ~10.")


if __name__ == "__main__":
    main()
