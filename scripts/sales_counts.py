"""Conteo de equipo comercial por dominio (GetLeads, GRATIS) → list_companies.

Para cada dominio de un niche cuenta contactos etiquetados ventas (sales_count) y
totales (total_count), calcula sales_bucket y hace upsert a Supabase. Idempotente:
salta dominios que ya tienen sales_count (resume tras corte). El conteo de GetLeads
es 0 créditos (creditsRemaining no baja).

Uso:
  python scripts/sales_counts.py --niche distribuidores-industriales-mx [--relevance A] \
      [--limit N]

Buckets (por sales_count): 0→0-sin-señal, 1-2, 3-10, 11-50, 51+→50+.
Solo escribe sales_count + sales_bucket (columnas reales de list_companies).
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

GETLEADS = os.path.join(os.path.dirname(__file__), "getleads.py")
SALES_FN = ["Sales & Business Development"]


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
    with open("/tmp/_gl_f.json", "w") as fh:
        json.dump({"filters": filters}, fh)
    for _ in range(4):
        out = subprocess.run(["python3", GETLEADS, "count", "--filters", "/tmp/_gl_f.json"],
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
    url = f"{base}/rest/v1/list_companies?niche=eq.{niche}&domain=eq.{domain}"
    r = urllib.request.Request(url, data=json.dumps(body).encode(), method="PATCH", headers={
        "apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "Prefer": "return=minimal", "User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(r, timeout=60) as resp:
        return resp.status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche", required=True)
    ap.add_argument("--relevance")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()

    base = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

    q = f"/rest/v1/list_companies?niche=eq.{a.niche}&sales_count=is.null&select=domain,relevance"
    if a.relevance:
        q += f"&relevance=eq.{a.relevance}"
    q += "&order=relevance.asc&limit=100000"
    rows = sb_get(base, key, q)
    domains = [r["domain"] for r in rows if r.get("domain")]
    if a.limit:
        domains = domains[:a.limit]
    print(f"pendientes: {len(domains)} dominios (niche={a.niche} relevance={a.relevance or 'todas'})", flush=True)

    done = 0
    for dom in domains:
        sales = gl_count({"domains": [dom], "job_functions": SALES_FN})
        body = {"sales_count": sales, "sales_bucket": bucket(sales)}
        try:
            sb_patch(base, key, a.niche, dom, body)
        except Exception as e:
            print(f"  PATCH falló {dom}: {e}", file=sys.stderr)
        done += 1
        if done % 50 == 0:
            print(f"  {done}/{len(domains)} | último {dom}: sales={sales} bucket={bucket(sales)}", flush=True)
        time.sleep(0.65)  # ~90 req/min (un count por dominio)

    print(f"LISTO niche={a.niche}: {done} dominios con sales_count", flush=True)


if __name__ == "__main__":
    main()
