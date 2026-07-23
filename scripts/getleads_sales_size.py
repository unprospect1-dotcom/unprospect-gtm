"""Rellena el tamaño del equipo COMERCIAL (ventas) por empresa usando GetLeads count.

GetLeads /contacts/search/count es GRATIS (0 créditos): cuenta los contactos de
función ventas por dominio = tamaño del equipo comercial. Escribe el resultado en
company.sales_count / company.sales_bucket.

Target por defecto: empresas de la canónica `company` con sales_count NULL (las que
nunca corrieron GetLeads). Idempotente y reanudable (checkpoint JSON).

Uso:
  python scripts/getleads_sales_size.py --limit 50        # prueba chica
  python scripts/getleads_sales_size.py                   # toda la cola pendiente
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SALES_FUNCTION = "Sales & Business Development"   # enum GetLeads job_functions
CKPT = os.path.join(tempfile.gettempdir(), "getleads_sales_size_ckpt.json")


def sql(query):
    base = os.environ["SUPABASE_URL"].rstrip("/")
    tok = os.environ["SUPABASE_TOKEN"]
    ref = base.split("//")[1].split(".")[0]
    url = f"https://api.supabase.com/v1/projects/{ref}/database/query"
    req = urllib.request.Request(
        url, data=json.dumps({"query": query}).encode(), method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {tok}", "User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())


def gl_count(domain):
    """Devuelve el # de contactos de ventas del dominio (0 créditos). None si error."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"domains": [domain], "job_functions": [SALES_FUNCTION]}, f)
        path = f.name
    try:
        out = subprocess.run([sys.executable, os.path.join(HERE, "getleads.py"),
                              "count", "--filters", path],
                             capture_output=True, text=True, timeout=120)
        if out.returncode != 0:
            return None
        return json.loads(out.stdout).get("total_matching")
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return None
    finally:
        os.unlink(path)


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


def flush(results):
    """UPDATE company.sales_count/sales_bucket desde un lote de resultados."""
    if not results:
        return
    values = ",".join(
        f"('{d}',{c},'{bucket(c)}')" for d, c in results if c is not None)
    if not values:
        return
    sql(f"""
      update company c set
        sales_count = v.sc, sales_bucket = v.sb, updated_at = now()
      from (values {values}) as v(domain, sc, sb)
      where c.domain = v.domain;
    """)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="máximo de dominios a procesar")
    ap.add_argument("--flush-every", type=int, default=100)
    a = ap.parse_args()

    done = set()
    if os.path.exists(CKPT):
        done = set(json.load(open(CKPT)).get("done", []))
        print(f"checkpoint: {len(done)} ya procesados", flush=True)

    rows = sql("select domain from company where sales_count is null "
               "and domain like '%.%' order by domain")
    todo = [r["domain"] for r in rows if r["domain"] not in done]
    if a.limit:
        todo = todo[:a.limit]
    print(f"pendientes: {len(todo)} dominios (equipo comercial via GetLeads, 0 créditos)",
          flush=True)

    batch, processed = [], 0
    for dom in todo:
        n = gl_count(dom)
        batch.append((dom, n))
        done.add(dom)
        processed += 1
        if len(batch) >= a.flush_every:
            flush(batch)
            json.dump({"done": sorted(done)}, open(CKPT, "w"))
            got = sum(1 for _, c in batch if c)
            print(f"  {processed}/{len(todo)} — lote escrito ({got} con equipo)", flush=True)
            batch = []
    flush(batch)
    json.dump({"done": sorted(done)}, open(CKPT, "w"))
    print(f"LISTO: {processed} dominios procesados.", flush=True)


if __name__ == "__main__":
    main()
