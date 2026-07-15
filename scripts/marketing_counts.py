"""Conteo de equipo de marketing por dominio (GetLeads, GRATIS) → list_companies.

Espejo de scripts/sales_counts.py. Para cada dominio de un niche cuenta contactos
etiquetados marketing (marketing_count), calcula marketing_bucket y hace upsert a
Supabase. Idempotente: salta dominios que ya tienen marketing_count (resume tras
corte). El conteo de GetLeads es 0 créditos (creditsRemaining no baja).

Uso:
  python scripts/marketing_counts.py --niche distribuidores-industriales-mx [--relevance A] \
      [--limit N]
  python scripts/marketing_counts.py --all-with-sales [--relevance A]   # todo el universo ya contado en ventas

Buckets (por marketing_count): 0→0-sin-señal, 1-2, 3-10, 11-50, 51+→50+.
Mismos buckets que ventas para que la matriz ventas × marketing sea directa.
Solo escribe marketing_count + marketing_bucket (columnas reales de list_companies).
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

GETLEADS = os.path.join(os.path.dirname(__file__), "getleads.py")
MKT_FN = ["Advertising & Marketing"]


def bucket(n):
    if n is None:
        return None
    if n == 0:
        return "0-sin-señal"
    if n <= 2:
        return "1-2"
    if n <= 10:
        return "3-10"
    if n <= 50:
        return "11-50"
    return "50+"


def gl_count(filters):
    with open("/tmp/_gl_mkt_f.json", "w") as fh:
        json.dump({"filters": filters}, fh)
    for _ in range(4):
        out = subprocess.run(["python3", GETLEADS, "count", "--filters", "/tmp/_gl_mkt_f.json"],
                             capture_output=True, text=True, timeout=90)
        try:
            d = json.loads(out.stdout)
            if d.get("ok"):
                return d.get("total_matching")
        except Exception:
            pass
        time.sleep(3)
    return None


def sb_get(base, key, path):
    r = urllib.request.Request(base + path, headers={
        "apikey": key, "Authorization": f"Bearer {key}", "User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(r, timeout=60) as resp:
        return json.loads(resp.read().decode())


def sb_patch(base, key, niche, domain, body):
    url = (f"{base}/rest/v1/list_companies?niche=eq.{urllib.parse.quote(niche)}"
           f"&domain=eq.{urllib.parse.quote(domain)}")
    r = urllib.request.Request(url, data=json.dumps(body).encode(), method="PATCH", headers={
        "apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "Prefer": "return=minimal", "User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(r, timeout=60) as resp:
        return resp.status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche")
    ap.add_argument("--all-with-sales", action="store_true",
                    help="procesa todo dominio con sales_count ya poblado (A-cut primero)")
    ap.add_argument("--relevance")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()

    base = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

    q = "/rest/v1/list_companies?marketing_count=is.null&select=niche,domain,relevance"
    if a.all_with_sales:
        q += "&sales_count=not.is.null"
    elif a.niche:
        q += f"&niche=eq.{urllib.parse.quote(a.niche)}"
    else:
        print("ERROR: da --niche o --all-with-sales", file=sys.stderr)
        sys.exit(2)
    if a.relevance:
        q += f"&relevance=eq.{a.relevance}"
    # relevance.asc → A antes que B/C; nulls al final (prioriza el corte limpio)
    q += "&order=relevance.asc,niche.asc&limit=100000"
    rows = sb_get(base, key, q)
    targets = [(r["niche"], r["domain"]) for r in rows if r.get("domain")]
    if a.limit:
        targets = targets[:a.limit]
    scope = "all-with-sales" if a.all_with_sales else a.niche
    print(f"pendientes: {len(targets)} dominios (scope={scope} relevance={a.relevance or 'todas'})",
          flush=True)

    done = 0
    for niche, dom in targets:
        mkt = gl_count({"domains": [dom], "job_functions": MKT_FN})
        body = {"marketing_count": mkt, "marketing_bucket": bucket(mkt)}
        try:
            sb_patch(base, key, niche, dom, body)
        except Exception as e:
            print(f"  PATCH falló {dom}: {e}", file=sys.stderr)
        done += 1
        if done % 50 == 0:
            print(f"  {done}/{len(targets)} | último {dom}: mkt={mkt} bucket={bucket(mkt)}", flush=True)
        time.sleep(0.65)  # ~90 req/min (un count por dominio)

    print(f"LISTO scope={scope}: {done} dominios con marketing_count", flush=True)


if __name__ == "__main__":
    main()
