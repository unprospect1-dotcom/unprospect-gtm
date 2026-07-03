"""Cliente CLI de Ocean.io para el skill gtm-ocean.

Los defaults espejean config/providers.yaml (sección ocean) — el skill lee la
config y pasa overrides por flag; este script no lee YAML.

Endpoints (paths verificados contra api.ocean.io — responden 403 sin token, no 404):
  GET  /v2/credits/balance      saldo de créditos + dailyLimitRateLeft
  POST /v2/warmup/companies     valida seeds / dispara crawl de dominios faltantes (GRATIS)
  POST /v3/search/companies     búsqueda por filtros o lookalikeDomains (1 crédito/resultado)
  POST /v3/search/people        búsqueda de personas (1 crédito/resultado; guardar `id` para reveal)
  POST /v2/reveal/emails        emails por person ids, async (1 crédito/email verificado)
  POST /v2/enrich/company       enriquecer por dominio (201 = aún no está en su DB, crawl
                                disparado sin costo — reintentar en 2-5 min)

Uso:
  python scripts/ocean.py balance
  python scripts/ocean.py warmup   --domains cliente1.com,cliente2.com
  python scripts/ocean.py companies --filters filters.json --size 10 [--search-after CURSOR]
  python scripts/ocean.py people    --filters filters.json --size 10 [--search-after CURSOR]
  python scripts/ocean.py reveal-emails --ids-file person_ids.txt [--webhook URL]
  python scripts/ocean.py enrich-company --domain empresa.com

Auth: header x-api-token con $OCEAN_KEY (cambiable con --key-env).
Rate limit self-serve: 60 req/min y 1,000 req/día — el script duerme 1s entre llamadas.
El body de search: {"size": N, "searchAfter": cursor, "companiesFilters": {...},
"peopleFilters": {...}} — el JSON de --filters se mezcla tal cual.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "https://api.ocean.io"


def call(method, url, key, body=None, retries=4):
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, method=method, headers={
            "x-api-token": key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                time.sleep(1.0)  # 60 req/min
                out = json.loads(r.read().decode() or "{}")
                out.setdefault("_http_status", r.status)
                return out
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                time.sleep(15 * (attempt + 1))
                continue
            sys.exit(f"HTTP {e.code} {url}: {e.read().decode()[:500]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["balance", "warmup", "companies", "people",
                                    "reveal-emails", "enrich-company"])
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--key-env", default="OCEAN_KEY")
    ap.add_argument("--filters", help="JSON con companiesFilters/peopleFilters")
    ap.add_argument("--size", type=int, default=10)
    ap.add_argument("--search-after", help="cursor de paginación de la respuesta previa")
    ap.add_argument("--domains", help="dominios separados por coma (warmup)")
    ap.add_argument("--domain", help="dominio único (enrich-company)")
    ap.add_argument("--ids-file", help="person ids, uno por línea (reveal-emails)")
    ap.add_argument("--webhook", help="webhookUrl para resultados async del reveal")
    ap.add_argument("--path", help="override del path del endpoint")
    a = ap.parse_args()

    key = os.environ.get(a.key_env) or sys.exit(f"falta la env var {a.key_env}")

    if a.cmd == "balance":
        out = call("GET", a.base_url + (a.path or "/v2/credits/balance"), key)
    elif a.cmd == "warmup":
        domains = [d.strip() for d in a.domains.split(",") if d.strip()]
        out = call("POST", a.base_url + (a.path or "/v2/warmup/companies"), key,
                   {"domains": domains})
    elif a.cmd in ("companies", "people"):
        body = {"size": a.size, **json.load(open(a.filters))}
        if a.search_after:
            body["searchAfter"] = a.search_after
        out = call("POST", a.base_url + (a.path or f"/v3/search/{a.cmd}"), key, body)
    elif a.cmd == "reveal-emails":
        ids = [i.strip() for i in open(a.ids_file) if i.strip()]
        body = {"ids": ids}
        if a.webhook:
            body["webhookUrl"] = a.webhook
        out = call("POST", a.base_url + (a.path or "/v2/reveal/emails"), key, body)
    elif a.cmd == "enrich-company":
        out = call("POST", a.base_url + (a.path or "/v2/enrich/company"), key,
                   {"domain": a.domain})
        if out.get("_http_status") == 201:
            out["_note"] = "201: dominio aún no está en Ocean; crawl disparado sin costo. Reintentar en 2-5 min."

    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
