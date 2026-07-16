"""Rescate de blind-spots de GetLeads con AI Ark (people search master_sales).

Para dominios donde GetLeads dio ventas=0 pero LinkedIn muestra equipo (>50),
consulta AI Ark `master_sales` acotado al dominio (`size:1` → `totalElements`) y
guarda el conteo en `aiark_sales_count`. Costo: 0.5 cr por empresa CON perfiles
(0 si AI Ark tampoco tiene). Idempotente: salta dominios que ya tienen el dato.

Uso:
  python scripts/aiark_rescue.py --domains-file /tmp/suspects.json

No sobrescribe sales_count/sales_bucket — solo llena aiark_sales_count. El max()
y el re-bucketing se hace en un paso aparte (revisable) tras ver los huecos.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

AIARK = os.path.join(os.path.dirname(__file__), "aiark.py")
GLK = os.environ.get("AI_ARK_API")
SB_BASE = os.environ["SUPABASE_URL"]
SB_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
AIARK_BASE = "https://api.ai-ark.com/api/developer-portal/v1"


def aiark_sales(domain):
    body = {"page": 0, "size": 1,
            "account": {"domain": {"any": {"include": [domain]}}},
            "contact": {"departmentAndFunction": {"any": {"include": ["master_sales"]}}}}
    data = json.dumps(body).encode()
    for attempt in range(5):
        req = urllib.request.Request(AIARK_BASE + "/people", data=data, method="POST", headers={
            "X-TOKEN": GLK, "Content-Type": "application/json", "Accept": "application/json",
            "User-Agent": "curl/8.5.0"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode() or "{}").get("totalElements")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 ** (attempt + 1)); continue
            return None
        except Exception:
            time.sleep(2)
    return None


def sb_get(qs):
    r = urllib.request.Request(SB_BASE + "/rest/v1/list_companies?" + qs,
                               headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                                        "User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(r, timeout=60) as x:
        return json.loads(x.read().decode())


def sb_patch(domain, body):
    url = f"{SB_BASE}/rest/v1/list_companies?domain=eq.{urllib.parse.quote(domain)}"
    r = urllib.request.Request(url, data=json.dumps(body).encode(), method="PATCH", headers={
        "apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}", "Content-Type": "application/json",
        "Prefer": "return=minimal", "User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(r, timeout=60) as x:
        return x.status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains-file", required=True)
    a = ap.parse_args()
    if not GLK:
        sys.exit("falta AI_ARK_API")
    doms = json.load(open(a.domains_file))
    # idempotente: salta los que ya tienen aiark_sales_count
    done_rows = sb_get("select=domain&aiark_sales_count=not.is.null&sales_bucket=eq.0-sin-se%C3%B1al&limit=100000")
    done = {r["domain"] for r in done_rows}
    todo = [d for d in doms if d not in done]
    print(f"sospechosos: {len(doms)} | ya hechos: {len(done)} | por hacer: {len(todo)}", flush=True)

    rescued = 0; spent_calls = 0
    for i, dom in enumerate(todo, 1):
        n = aiark_sales(dom)
        try:
            sb_patch(dom, {"aiark_sales_count": n})
        except Exception as e:
            print(f"  PATCH falló {dom}: {e}", file=sys.stderr)
        if n and n > 0:
            rescued += 1; spent_calls += 1
        if i % 25 == 0:
            print(f"  {i}/{len(todo)} | rescatados {rescued} | último {dom}={n}", flush=True)
        time.sleep(0.3)  # ~200/min bajo el límite de 300 rpm
    print(f"LISTO: {len(todo)} consultados, {rescued} con equipo en AI Ark (~{spent_calls*0.5:.0f} cr)", flush=True)


if __name__ == "__main__":
    main()
