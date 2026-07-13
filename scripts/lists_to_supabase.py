"""Sube una lista de empresas (CSV) a Supabase `list_companies`, con su nicho.

Regla del GTM OS: toda lista generada por los skills de list building se upserta
aquí — el CSV local es artefacto de trabajo, Supabase es el registro durable.

Uso:
  python scripts/lists_to_supabase.py --csv lists/ws/2026-07-14-lista.csv \
      --niche instaladores-solares-mx --source ocean [--domain-col domain]

- Crea la tabla si no existe (DDL de supabase/migrations/005_list_companies.sql,
  via Management API con $SUPABASE_TOKEN; si no está la env var, asume que ya existe).
- Upsert por (niche, domain) via PostgREST con $SUPABASE_SERVICE_ROLE_KEY.
- Filas sin dominio se saltan (se reportan) — el CSV sigue siendo el registro completo.
- Columnas conocidas se mapean a campos; el resto va a `meta` (jsonb).
"""
import argparse
import csv
import json
import os
import sys
import urllib.request

KNOWN = {"domain", "name", "source", "source_id", "relevance", "company_size",
         "staff_linkedin", "sales_count", "sales_bucket"}
ALIASES = {"staff_autoreportado": "company_size"}
INTS = {"staff_linkedin", "sales_count"}


def req(url, body, headers, method="POST"):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), method=method,
                               headers={"Content-Type": "application/json",
                                        "User-Agent": "curl/8.5.0", **headers})
    with urllib.request.urlopen(r, timeout=180) as resp:
        return resp.status, resp.read().decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--niche", required=True)
    ap.add_argument("--source", required=True)
    ap.add_argument("--domain-col", default="domain")
    ap.add_argument("--batch", type=int, default=500)
    a = ap.parse_args()

    base = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

    mgmt = os.environ.get("SUPABASE_TOKEN")
    if mgmt:
        ddl = open(os.path.join(os.path.dirname(__file__), "..",
                                "supabase/migrations/005_list_companies.sql")).read()
        ref = base.split("//")[1].split(".")[0]
        st, _ = req(f"https://api.supabase.com/v1/projects/{ref}/database/query",
                    {"query": ddl}, {"Authorization": f"Bearer {mgmt}"})
        print(f"DDL list_companies -> {st}")

    rows, skipped = [], 0
    with open(a.csv) as f:
        for r in csv.DictReader(f):
            dom = (r.get(a.domain_col) or "").lower().strip().removeprefix("www.")
            if not dom or "." not in dom:
                skipped += 1
                continue
            out = {"niche": a.niche, "domain": dom, "source": r.get("source") or a.source}
            meta = {}
            for k, v in r.items():
                if k == a.domain_col or not v:
                    continue
                k2 = ALIASES.get(k, k)
                if k2 in KNOWN and k2 != "domain":
                    if k2 in INTS:
                        try:
                            out[k2] = int(v)
                        except ValueError:
                            meta[k] = v
                    else:
                        out[k2] = v
                else:
                    meta[k] = v
            if meta:
                out["meta"] = meta
            rows.append(out)

    # dedupe interno por (niche, domain) — PostgREST no acepta dupes en el mismo batch
    uniq = {}
    for r in rows:
        uniq[r["domain"]] = r
    rows = list(uniq.values())

    # PostgREST (PGRST102) exige llaves idénticas en todas las filas del batch:
    # normaliza al union de llaves, faltantes en null
    all_keys = set()
    for r in rows:
        all_keys.update(r)
    rows = [{k: r.get(k) for k in all_keys} for r in rows]

    hdr = {"apikey": key, "Authorization": f"Bearer {key}",
           "Prefer": "resolution=merge-duplicates"}
    url = f"{base}/rest/v1/list_companies?on_conflict=niche,domain"
    done = 0
    for i in range(0, len(rows), a.batch):
        st, _ = req(url, rows[i:i + a.batch], hdr)
        done += len(rows[i:i + a.batch])
        print(f"upsert {done}/{len(rows)} -> {st}", flush=True)
    print(f"LISTO niche={a.niche}: {len(rows)} upserted, {skipped} sin dominio (solo en CSV)")


if __name__ == "__main__":
    main()
