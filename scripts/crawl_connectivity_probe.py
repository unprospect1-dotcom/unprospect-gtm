"""Diagnóstico de conectividad ($0) de los dominios con crawl fallido (site_crawls.ok=false).
NO baja contenido — solo resuelve DNS y prueba http/https para clasificar por qué falló:

  dead-dns        -> el dominio no resuelve (caducado/no existe) -> re-buscar por nombre/LinkedIn
  alive-https     -> https responde 2xx/3xx -> el crawler debería haber jalado (reintentable)
  alive-http-only -> solo http responde (el crawler probó https) -> RECUPERABLE con re-crawl http
  wrong-domain    -> redirige a OTRO dominio -> el sitio real es otro
  resolves-down   -> resuelve pero ni http ni https responden bien (5xx/timeout/refused)

Escribe resultado a company (columnas nuevas conn_status / conn_final_url) y un resumen.
Uso: python scripts/crawl_connectivity_probe.py [--limit N] [--workers 30]
"""
import argparse
import json
import os
import socket
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from collections import Counter

socket.setdefaulttimeout(5)


def sql(query):
    base = os.environ["SUPABASE_URL"].rstrip("/")
    tok = os.environ["SUPABASE_TOKEN"]
    ref = base.split("//")[1].split(".")[0]
    url = f"https://api.supabase.com/v1/projects/{ref}/database/query"
    req = urllib.request.Request(
        url, data=json.dumps({"query": query}).encode(), method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {tok}", "User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode())


def curl(url):
    """(http_code, url_effective). code '000' = no respuesta."""
    try:
        out = subprocess.run(
            ["curl", "-sSL", "--max-time", "10", "-o", "/dev/null",
             "-w", "%{http_code}|%{url_effective}", url],
            capture_output=True, text=True, timeout=15).stdout
        code, _, eff = out.partition("|")
        return code.strip(), eff.strip()
    except (subprocess.TimeoutExpired, Exception):
        return "000", ""


def base_domain(url):
    u = url.lower().replace("https://", "").replace("http://", "").replace("www.", "")
    return u.split("/")[0].split(":")[0]


def classify(domain):
    # 1) DNS
    try:
        socket.gethostbyname(domain)
    except Exception:
        return domain, "dead-dns", ""
    # 2) https
    code, eff = curl(f"https://{domain}")
    if code and code[0] in "23":
        if eff and base_domain(eff) != domain and domain not in base_domain(eff):
            return domain, "wrong-domain", eff
        return domain, "alive-https", eff
    # 3) http fallback
    code2, eff2 = curl(f"http://{domain}")
    if code2 and code2[0] in "23":
        if eff2 and base_domain(eff2) != domain and domain not in base_domain(eff2):
            return domain, "wrong-domain", eff2
        return domain, "alive-http-only", eff2
    return domain, "resolves-down", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=30)
    a = ap.parse_args()

    # columnas de diagnóstico (idempotente)
    sql("alter table company add column if not exists conn_status text;"
        "alter table company add column if not exists conn_final_url text;")

    rows = sql("""select c.domain from company c join site_crawls s on s.domain=c.domain
      where s.ok=false and c.conn_status is null order by c.domain""")
    doms = [r["domain"] for r in rows]
    if a.limit:
        doms = doms[:a.limit]
    print(f"diagnóstico de {len(doms)} dominios con crawl fallido…", flush=True)

    tally = Counter()
    buf, done = [], 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for domain, status, eff in ex.map(classify, doms):
            tally[status] += 1
            buf.append((domain, status, eff))
            done += 1
            if len(buf) >= 200:
                vals = ",".join(
                    "('%s','%s',%s)" % (d, s, "'%s'" % u.replace("'", "") if u else "null")
                    for d, s, u in buf)
                sql(f"""update company c set conn_status=v.st, conn_final_url=v.fu
                        from (values {vals}) as v(domain,st,fu) where c.domain=v.domain;""")
                buf = []
                print(f"  {done}/{len(doms)}  {dict(tally)}", flush=True)
    if buf:
        vals = ",".join(
            "('%s','%s',%s)" % (d, s, "'%s'" % u.replace("'", "") if u else "null")
            for d, s, u in buf)
        sql(f"""update company c set conn_status=v.st, conn_final_url=v.fu
                from (values {vals}) as v(domain,st,fu) where c.domain=v.domain;""")

    print("\n== RESULTADO ==")
    tot = sum(tally.values())
    for k, n in tally.most_common():
        print(f"  {k:16} {n:6}  ({n/tot*100:.0f}%)")
    print(f"  {'TOTAL':16} {tot}")


if __name__ == "__main__":
    main()
