"""Cliente CLI de AI Ark para el skill gtm-lists-aiark.

Los defaults espejean config/providers.yaml (sección aiark) — el skill lee la
config y pasa overrides por flag; este script no lee YAML.

Uso:
  python scripts/aiark.py credit
  python scripts/aiark.py companies --filters filters.json --page 0 --size 25
  python scripts/aiark.py people    --filters filters.json --page 0 --size 25
  python scripts/aiark.py export    --filters filters.json --size 1000
  python scripts/aiark.py export-stats   --track-id <uuid>
  python scripts/aiark.py export-results --track-id <uuid> --page 0 --size 100
  python scripts/aiark.py exclude-list --type company_id --values-file domains.txt [--list-id <uuid>]

Auth: header X-TOKEN con el valor de $AI_ARK_API (cambiable con --key-env).
Salida: JSON crudo a stdout (el skill lo interpreta).

OJO (verificado 2026-07-13): el search cobra 0.5 créditos POR PERFIL DEVUELTO —
sondear totales con --size 1 y nunca pedir páginas que no se van a usar.
Paths de credit y people search verificados en vivo; stats/results de export
siguen sin confirmar — si dan 404, usar --path y registrar en LEARNINGS.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = "https://api.ai-ark.com/api/developer-portal/v1"


def call(method, url, key, body=None, retries=4):
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, method=method, headers={
            "X-TOKEN": key,
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
    ap.add_argument("cmd", choices=["credit", "companies", "people", "export",
                                    "export-stats", "export-results", "exclude-list"])
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--key-env", default="AI_ARK_API")
    ap.add_argument("--filters", help="archivo JSON con account/contact/lists/lookalikeDomains")
    ap.add_argument("--page", type=int, default=0)
    ap.add_argument("--size", type=int, default=25)
    ap.add_argument("--track-id")
    ap.add_argument("--type", choices=["people_id", "company_id"])
    ap.add_argument("--values-file", help="un valor por línea, máx 10000")
    ap.add_argument("--list-id")
    ap.add_argument("--path", help="override del path del endpoint (para ajustar 404s)")
    a = ap.parse_args()

    key = os.environ.get(a.key_env) or sys.exit(f"falta la env var {a.key_env}")
    filters = json.load(open(a.filters)) if a.filters else {}

    if a.cmd == "credit":
        # path verificado 2026-07-13 (/credit da 401)
        out = call("GET", a.base_url + (a.path or "/payments/credits"), key)
    elif a.cmd in ("companies", "people"):
        body = {"page": a.page, "size": a.size, **filters}
        out = call("POST", a.base_url + (a.path or f"/{a.cmd}"), key, body)
    elif a.cmd == "export":
        body = {"page": 0, "size": a.size, **filters}
        out = call("POST", a.base_url + (a.path or "/people/export"), key, body)
    elif a.cmd == "export-stats":
        out = call("GET", a.base_url + (a.path or f"/people/export/{a.track_id}/statistics"), key)
    elif a.cmd == "export-results":
        out = call("GET", a.base_url + (a.path or
                   f"/people/export/{a.track_id}/results?page={a.page}&size={a.size}"), key)
    elif a.cmd == "exclude-list":
        values = [v.strip() for v in open(a.values_file) if v.strip()][:10000]
        body = {"type": a.type, "values": values, "mode": "APPEND"}
        if a.list_id:
            body["id"] = a.list_id
        out = call("POST", a.base_url + (a.path or "/lists"), key, body)

    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
