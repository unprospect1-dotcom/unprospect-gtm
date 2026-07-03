"""Cliente CLI de Prospeo para el skill gtm-prospeo.

Los defaults espejean config/providers.yaml (sección prospeo) — el skill lee la
config y pasa overrides por flag; este script no lee YAML.

Uso:
  python scripts/prospeo.py search --filters filters.json --page 1
  python scripts/prospeo.py search --filters filters.json --all-pages --max-pages 1000 --out results.jsonl
  python scripts/prospeo.py enrich --data '{"linkedin_url": "..."}' [--mobile]
  python scripts/prospeo.py enrich-bulk --data-file leads.jsonl [--mobile]   # máx 50 por request
  python scripts/prospeo.py account

Auth: header X-KEY con el valor de $PROSPEO_KEY (cambiable con --key-env).
Costos: 1 crédito por email verificado; mobile 10 créditos; NO_MATCH gratis;
re-enrich gratis por 90 días. 1 crédito por búsqueda con ≥1 resultado.

NOTA: paths de bulk/account no confirmados en docs públicos — ante 404 usar
--path y registrar el correcto en el LEARNINGS del skill.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "https://api.prospeo.io"


def call(url, key, body, rps=2.0, retries=4):
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers={
            "X-KEY": key,
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                time.sleep(1.0 / rps)
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                time.sleep(2 ** (attempt + 2))
                continue
            body_txt = e.read().decode()[:500]
            if e.code == 400 and "NO_MATCH" in body_txt:
                return {"error": True, "message": "NO_MATCH"}
            sys.exit(f"HTTP {e.code} {url}: {body_txt}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["search", "enrich", "enrich-bulk", "account"])
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--key-env", default="PROSPEO_KEY")
    ap.add_argument("--filters", help="archivo JSON con los filtros de search-person")
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--all-pages", action="store_true")
    ap.add_argument("--max-pages", type=int, default=1000)
    ap.add_argument("--out", help="con --all-pages: JSONL de salida")
    ap.add_argument("--data", help="JSON inline del lead a enriquecer")
    ap.add_argument("--data-file", help="JSONL, un lead por línea (máx 50 para bulk)")
    ap.add_argument("--mobile", action="store_true", help="enrich_mobile=true (10 créditos c/u)")
    ap.add_argument("--rps", type=float, default=2.0)
    ap.add_argument("--path", help="override del path del endpoint")
    a = ap.parse_args()

    key = os.environ.get(a.key_env) or sys.exit(f"falta la env var {a.key_env}")

    if a.cmd == "search":
        filters = json.load(open(a.filters))
        url = a.base_url + (a.path or "/search-person")
        if not a.all_pages:
            out = call(url, key, {"page": a.page, "filters": filters}, a.rps)
        else:
            fh = open(a.out, "w", encoding="utf-8") if a.out else sys.stdout
            page, total = a.page, None
            while page <= a.max_pages:
                r = call(url, key, {"page": page, "filters": filters}, a.rps)
                results = r.get("results") or []
                for item in results:
                    fh.write(json.dumps(item, ensure_ascii=False) + "\n")
                pg = r.get("pagination") or {}
                total = pg.get("total_count", total)
                if page >= pg.get("total_page", page) or not results:
                    break
                page += 1
            out = {"done": True, "pages": page, "total_count": total, "out": a.out}
    elif a.cmd == "enrich":
        body = {"data": json.loads(a.data), "only_verified_email": True}
        if a.mobile:
            body["enrich_mobile"] = True
        out = call(a.base_url + (a.path or "/enrich-person"), key, body, a.rps)
    elif a.cmd == "enrich-bulk":
        leads = [json.loads(l) for l in open(a.data_file) if l.strip()][:50]
        body = {"data": leads, "only_verified_email": True}
        if a.mobile:
            body["enrich_mobile"] = True
        out = call(a.base_url + (a.path or "/bulk-enrich-person"), key, body, a.rps)
    elif a.cmd == "account":
        out = call(a.base_url + (a.path or "/account-information"), key, {}, a.rps)

    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
