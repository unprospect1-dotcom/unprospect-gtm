"""Flag de Google Ads por dominio via Apify Google Ads Transparency Center.

Detecta si una empresa corre Google Ads (y formato + recencia) usando el actor
`silva95gustavo/google-ads-scraper` sobre el Transparency Center. Con resultsLimit=1
solo confirma el binario anuncia/no (lo que importa para el A/B del PLAYBOOK §8).

Economía (medida 2026-07-15): $0.0019 por anuncio + $0.00005 por arranque. Los dominios
que NO anuncian cuestan $0. ~$0.0004/dominio efectivo. Las cuentas Apify FREE topan a
~$5/mes → este script ROTA entre varios tokens (env vars) cuando uno agota su límite.

Uso:
  # desde un niche de list_companies (resume por ads_checked null; persiste el flag)
  python scripts/ads_transparency.py --niche fintech-b2b-mx
  # desde un archivo de dominios (uno por línea), sin Supabase, a stdout JSON
  python scripts/ads_transparency.py --domains-file doms.txt --no-persist

Flags: --region (default mx), --chunk (default 1500), --results-limit (default 1),
  --tokens-env (default "APIFY_TOKEN2,APIFYTOKEN3"). Persiste a list_companies:
  ads_checked (bool), ads_runs (bool), ads_last_shown (date), ads_formats (text).
Columnas: se crean con `alter table ... add column if not exists` (requiere SUPABASE_TOKEN),
  si no, se asumen existentes.
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict

ACTOR = "silva95gustavo~google-ads-scraper"


def api(url, data=None, method="GET"):
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=60) as x:
        return json.loads(x.read().decode())


def sb(base, key, path, body=None, method="GET", prefer=None):
    h = {"apikey": key, "Authorization": f"Bearer {key}", "User-Agent": "curl/8.5.0"}
    if body is not None:
        h["Content-Type"] = "application/json"
    if prefer:
        h["Prefer"] = prefer
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 method=method, headers=h)
    for _ in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as x:
                return x.status, x.read().decode(), x.headers
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(3); continue
            raise
    raise RuntimeError("supabase retries agotados")


def run_chunk(doms, tok, region, rlimit):
    urls = [{"url": f"https://adstransparency.google.com/?region={region}&domain={d}"} for d in doms]
    inp = {"startUrls": urls, "resultsLimit": rlimit, "skipDetails": True,
           "shouldDownloadAssets": False, "proxyConfiguration": {"useApifyProxy": True}}
    run = api(f"https://api.apify.com/v2/acts/{ACTOR}/runs?token={tok}",
              data=json.dumps(inp).encode(), method="POST")["data"]
    while True:
        d = api(f"https://api.apify.com/v2/actor-runs/{run['id']}?token={tok}")["data"]
        if d["status"] in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            break
        time.sleep(20)
    items = []
    if d["status"] == "SUCCEEDED":
        off = 0
        while True:
            c = api(f"https://api.apify.com/v2/datasets/{run['defaultDatasetId']}/items?token={tok}&limit=1000&offset={off}")
            if not c:
                break
            items += c; off += 1000
    return d, items


def persist(base, key, doms, items):
    byd = defaultdict(list)
    for it in items:
        byd[(it.get("startUrl", "").split("domain=")[-1]).lower()].append(it)
    adv = [d for d in doms if byd.get(d)]
    non = [d for d in doms if not byd.get(d)]
    for d in adv:
        ads = byd[d]
        last = max((a.get("lastShown") or "")[:10] for a in ads if a.get("lastShown")) or None
        fmts = ",".join(sorted(set(a.get("format") for a in ads if a.get("format"))))
        sb(base, key, f"/rest/v1/list_companies?domain=eq.{urllib.parse.quote(d)}",
           {"ads_checked": True, "ads_runs": True, "ads_last_shown": last, "ads_formats": fmts},
           "PATCH", "return=minimal")
    for i in range(0, len(non), 80):
        inl = ",".join(urllib.parse.quote(x) for x in non[i:i + 80])
        sb(base, key, f"/rest/v1/list_companies?domain=in.({inl})",
           {"ads_checked": True, "ads_runs": False}, "PATCH", "return=minimal")
    return len(adv)


# Columnas requeridas en list_companies (crear una vez si no existen):
#   ads_checked boolean, ads_runs boolean, ads_last_shown date, ads_formats text
# (via Supabase Management API con SUPABASE_TOKEN, o SQL manual.)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche")
    ap.add_argument("--domains-file")
    ap.add_argument("--region", default="mx")
    ap.add_argument("--chunk", type=int, default=1500)
    ap.add_argument("--results-limit", type=int, default=1)
    ap.add_argument("--tokens-env", default="APIFY_TOKEN2,APIFYTOKEN3")
    ap.add_argument("--no-persist", action="store_true")
    ap.add_argument("--budget-secs", type=int, default=2700)
    a = ap.parse_args()

    tokens = [os.environ[t] for t in a.tokens_env.split(",") if os.environ.get(t)]
    base = os.environ.get("SUPABASE_URL"); key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    def remaining():
        if a.domains_file:
            return sorted(set(l.strip().lower() for l in open(a.domains_file) if l.strip()))
        doms = []; off = 0
        while True:
            _, txt, _ = sb(base, key, f"/rest/v1/list_companies?niche=eq.{a.niche}&ads_checked=is.null&select=domain&limit=1000&offset={off}")
            rows = json.loads(txt)
            if not rows:
                break
            doms += [(r.get("domain") or "").lower().strip() for r in rows if r.get("domain")]
            off += 1000
        return sorted(set(d for d in doms if "." in d))

    ti = 0; t0 = time.time(); tot = 0
    while time.time() - t0 < a.budget_secs:
        doms = remaining()
        if not doms:
            print("ADS DONE"); break
        chunk = doms[:a.chunk]
        if ti >= len(tokens):
            print(f"TOKENS AGOTADOS — faltan {len(doms)}"); break
        try:
            d, items = run_chunk(chunk, tokens[ti], a.region, a.results_limit)
        except urllib.error.HTTPError as e:
            if e.code == 403 and "hard limit" in e.read().decode():
                print(f"token {ti} agotado, rotando"); ti += 1; continue
            raise
        if d["status"] == "SUCCEEDED":
            if a.no_persist or not base:
                adv = sum(1 for dd in chunk if any(it.get("startUrl", "").endswith(dd) for it in items))
                print(json.dumps({"chunk": len(chunk), "ads": adv, "cost": d.get("usageTotalUsd")}))
            else:
                adv = persist(base, key, chunk, items)
            tot += adv
            print(f"chunk {len(chunk)} OK (tok{ti}): {adv} anuncian | ${d.get('usageTotalUsd')} | quedan ~{len(doms) - len(chunk)}", flush=True)
        else:
            print(f"chunk {d['status']}: {d.get('statusMessage')}", flush=True)
            if "hard limit" in str(d.get("statusMessage", "")):
                ti += 1
            time.sleep(20)
    print(f"advertisers detectados esta corrida: {tot}")


if __name__ == "__main__":
    main()
