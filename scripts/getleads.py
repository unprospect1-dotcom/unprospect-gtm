"""Cliente CLI de GetLeads.io para el skill gtm-getleads.

Los defaults espejean config/providers.yaml (sección getleads) — el skill lee la
config y pasa overrides por flag; este script no lee YAML.

Uso:
  python scripts/getleads.py health
  python scripts/getleads.py credits
  python scripts/getleads.py count  --filters filters.json
  python scripts/getleads.py search --filters filters.json --limit 25 [--offset 0] [--max-per-company 2]
  python scripts/getleads.py export --filters filters.json [--max-rows 5000]
  python scripts/getleads.py export-status --export-id <id>
  python scripts/getleads.py decision-makers --domain acme.com --limit 10
  python scripts/getleads.py colleagues --email-domain acme.com --limit 100 [--offset 0]
  python scripts/getleads.py enrich-email    --values-file emails.txt      (máx 100 por corrida)
  python scripts/getleads.py enrich-linkedin --values-file urls.txt        (máx 100 por corrida)
  python scripts/getleads.py enrich-person   --items items.json            (máx 100 ítems)
  python scripts/getleads.py filter-values --field industries
  python scripts/getleads.py signals --kind funding --params "limit=20&has_amount=true"

Auth: Authorization Bearer con $GETLEADS_API (cambiable con --key-env).
Salida: JSON crudo a stdout (el skill lo interpreta).

Economía (verificada 2026-07): 1 crédito por registro devuelto / ítem exitoso;
0 si no hay match. GRATIS: health, count, filter-values. Los responses de count
traen creditsRemaining — por eso `credits` es un count trivial (gratis).
Rate limit: 100 req/min global — 429 al excederse (el script reintenta).
Docs: no públicas; extraídas en reference/getleads-api.md.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "https://app.getleads.io/api/v1"


def call(method, url, key, body=None, retries=4):
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                time.sleep(2 ** (attempt + 1))
                continue
            sys.exit(f"HTTP {e.code} {url}: {e.read().decode()[:500]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["health", "credits", "count", "search", "export",
                                    "export-status", "decision-makers", "colleagues",
                                    "enrich-email", "enrich-linkedin", "enrich-person",
                                    "filter-values", "signals"])
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--key-env", default="GETLEADS_API")
    ap.add_argument("--filters", help="archivo JSON: {filters: {...}} o filtros planos")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--max-per-company", type=int)
    ap.add_argument("--max-rows", type=int)
    ap.add_argument("--export-id")
    ap.add_argument("--domain")
    ap.add_argument("--email-domain")
    ap.add_argument("--values-file", help="un valor por línea, máx 100")
    ap.add_argument("--items", help="archivo JSON con lista de ítems (enrich-person)")
    ap.add_argument("--field", help="campo para filter-values (industries, seniority, ...)")
    ap.add_argument("--kind", choices=["funding", "acquisitions"])
    ap.add_argument("--params", default="", help="query string para signals")
    ap.add_argument("--path", help="override del path del endpoint")
    a = ap.parse_args()

    key = os.environ.get(a.key_env) or sys.exit(f"falta la env var {a.key_env}")
    raw = json.load(open(a.filters)) if a.filters else {}
    filters = raw if "filters" in raw else {"filters": raw} if raw else {}

    if a.cmd == "health":
        out = call("GET", a.base_url + (a.path or "/contacts/health"), key)
    elif a.cmd == "credits":
        # count es gratis y su response trae creditsRemaining
        body = {"filters": {"domains": ["dominio-inexistente.invalid"]}}
        r = call("POST", a.base_url + "/contacts/search/count", key, body)
        out = {"creditsRemaining": r.get("creditsRemaining")}
    elif a.cmd == "count":
        out = call("POST", a.base_url + (a.path or "/contacts/search/count"), key, filters)
    elif a.cmd == "search":
        body = dict(filters)
        if a.limit is not None:
            body["limit"] = a.limit
        if a.offset:
            body["offset"] = a.offset
        if a.max_per_company is not None:
            body["max_per_company"] = a.max_per_company
        out = call("POST", a.base_url + (a.path or "/contacts/search"), key, body)
    elif a.cmd == "export":
        body = dict(filters)
        if a.max_rows is not None:
            body["max_rows"] = a.max_rows
        out = call("POST", a.base_url + (a.path or "/contacts/search/export"), key, body)
    elif a.cmd == "export-status":
        out = call("GET", a.base_url + (a.path or f"/contacts/search/export/{a.export_id}"), key)
    elif a.cmd == "decision-makers":
        body = {"domain": a.domain, "limit": a.limit or 10, "offset": a.offset}
        out = call("POST", a.base_url + (a.path or "/contacts/lookup/decision-makers"), key, body)
    elif a.cmd == "colleagues":
        body = {"email_domain": a.email_domain, "limit_per_item": a.limit or 100,
                "offset": a.offset}
        out = call("POST", a.base_url + (a.path or "/contacts/lookup/colleagues"), key, body)
    elif a.cmd == "enrich-email":
        values = [v.strip() for v in open(a.values_file) if v.strip()][:100]
        body = {"items": [{"email": v} for v in values]}
        out = call("POST", a.base_url + (a.path or "/enrich/from-email"), key, body)
    elif a.cmd == "enrich-linkedin":
        values = [v.strip() for v in open(a.values_file) if v.strip()][:100]
        body = {"items": [{"linkedin_url": v} for v in values]}
        out = call("POST", a.base_url + (a.path or "/enrich/from-linkedin"), key, body)
    elif a.cmd == "enrich-person":
        body = {"items": json.load(open(a.items))[:100]}
        out = call("POST", a.base_url + (a.path or "/enrich/from-person"), key, body)
    elif a.cmd == "filter-values":
        out = call("GET", a.base_url + (a.path or f"/contacts/filter-values?field={a.field}"), key)
    elif a.cmd == "signals":
        qs = f"?{a.params}" if a.params else ""
        out = call("GET", a.base_url + (a.path or f"/{a.kind}/signals{qs}"), key)

    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
