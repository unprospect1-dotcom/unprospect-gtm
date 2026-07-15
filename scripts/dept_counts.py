"""Conteo unificado de tamaño de VENTAS + MARKETING por empresa (GetLeads, GRATIS)
sobre TODO el universo de list_companies. Deduplica por dominio: cuenta cada dominio
único una sola vez y escribe el resultado a todas sus filas de nicho (un dominio puede
estar en varios nichos). Idempotente/resumible: recalcula lo pendiente en cada corrida
desde Supabase, así que retoma tras un corte sin repetir conteos ya hechos.

Prioridad de conteo: A-cut (relevance A) → autotransporte (universo sin A/B/C) →
B-cut → C-cut. Así el corte extraíble termina primero.

Economía: el count de GetLeads es 0 créditos. Límite 100 req/min → ritmo ~95/min.
Buckets (por conteo): 0→0-sin-señal, 1-2, 3-10, 11-50, 51+→50+ (idénticos ventas/mkt).

Uso:
  python scripts/dept_counts.py                 # ventas+marketing, universo entero
  python scripts/dept_counts.py --only marketing
  python scripts/dept_counts.py --only sales
  python scripts/dept_counts.py --niche logistics-tech-mx   # limitar a un nicho
  python scripts/dept_counts.py --plan          # solo estima trabajo pendiente y sale
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

GL_BASE = "https://app.getleads.io/api/v1"
GL_KEY = os.environ.get("GETLEADS_API")
SB_BASE = os.environ["SUPABASE_URL"]
SB_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
FN = {"sales": ["Sales & Business Development"], "marketing": ["Advertising & Marketing"]}
REL_PRIORITY = {"A": 0, None: 1, "B": 2, "C": 3}  # A-cut primero, autotransporte (None) después


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


def gl_count(domain, kind):
    body = {"filters": {"domains": [domain], "job_functions": FN[kind]}}
    data = json.dumps(body).encode()
    for attempt in range(5):
        req = urllib.request.Request(GL_BASE + "/contacts/search/count", data=data, method="POST",
                                     headers={"Authorization": f"Bearer {GL_KEY}",
                                              "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode() or "{}").get("total_matching")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 ** (attempt + 1))
                continue
            time.sleep(2)
        except Exception:
            time.sleep(2)
    return None


def sb_get_all(select, extra=""):
    rows, off = [], 0
    while True:
        url = f"{SB_BASE}/rest/v1/list_companies?select={select}{extra}"
        req = urllib.request.Request(url, headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                                                   "User-Agent": "curl/8.5.0", "Range": f"{off}-{off+999}"})
        with urllib.request.urlopen(req, timeout=120) as r:
            chunk = json.loads(r.read().decode())
        rows += chunk
        off += 1000
        if len(chunk) < 1000:
            return rows


def sb_patch_domain(domain, body):
    url = f"{SB_BASE}/rest/v1/list_companies?domain=eq.{urllib.parse.quote(domain)}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="PATCH",
                                 headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                                          "Content-Type": "application/json", "Prefer": "return=minimal",
                                          "User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["sales", "marketing"], help="una sola dimensión")
    ap.add_argument("--niche", help="limitar a un nicho")
    ap.add_argument("--plan", action="store_true", help="solo estimar y salir")
    a = ap.parse_args()
    kinds = [a.only] if a.only else ["sales", "marketing"]
    if not GL_KEY:
        sys.exit("falta GETLEADS_API")

    extra = f"&niche=eq.{urllib.parse.quote(a.niche)}" if a.niche else ""
    rows = sb_get_all("niche,domain,relevance,sales_count,marketing_count", extra)

    # Agrupar por dominio: qué falta, valor ya conocido (para copiar sin contar), y prioridad.
    doms = {}
    for r in rows:
        d = r.get("domain")
        if not d:
            continue
        e = doms.setdefault(d, {"prio": 9, "sales_known": None, "mkt_known": None,
                                "sales_null": False, "mkt_null": False})
        e["prio"] = min(e["prio"], REL_PRIORITY.get(r.get("relevance"), 4))
        if r.get("sales_count") is not None:
            e["sales_known"] = r["sales_count"]
        else:
            e["sales_null"] = True
        if r.get("marketing_count") is not None:
            e["mkt_known"] = r["marketing_count"]
        else:
            e["mkt_null"] = True

    # Trabajo: por dominio, para cada kind pedido, ¿necesita API (todas sus filas null) o solo copiar?
    need_api = {"sales": 0, "marketing": 0}
    need_copy = {"sales": 0, "marketing": 0}
    work = []
    for d, e in doms.items():
        todo = {}
        for k in kinds:
            null_flag = e["sales_null"] if k == "sales" else e["mkt_null"]
            known = e["sales_known"] if k == "sales" else e["mkt_known"]
            if not null_flag:
                continue  # ya completo en todas las filas
            if known is not None:
                todo[k] = ("copy", known)
                need_copy[k] += 1
            else:
                todo[k] = ("api", None)
                need_api[k] += 1
        if todo:
            work.append((e["prio"], d, todo))
    work.sort(key=lambda x: x[0])

    total_api = need_api["sales"] + need_api["marketing"]
    eta_min = total_api / 95.0
    print(f"dominios únicos: {len(doms)} | con trabajo pendiente: {len(work)}")
    print(f"  API sales: {need_api['sales']}  API marketing: {need_api['marketing']}  "
          f"(copiar sin contar: sales {need_copy['sales']}, mkt {need_copy['marketing']})")
    print(f"  llamadas GetLeads: {total_api} → ETA ~{eta_min:.0f} min (~{eta_min/60:.1f} h) a 95/min",
          flush=True)
    if a.plan:
        return

    done, api_calls = 0, 0
    for prio, dom, todo in work:
        body = {}
        for k, (mode, val) in todo.items():
            n = val if mode == "copy" else gl_count(dom, k)
            if mode == "api":
                api_calls += 1
                time.sleep(0.63)  # ~95/min bajo el límite de 100
            col = "sales_count" if k == "sales" else "marketing_count"
            bcol = "sales_bucket" if k == "sales" else "marketing_bucket"
            body[col] = n
            body[bcol] = bucket(n)
        try:
            sb_patch_domain(dom, body)
        except Exception as ex:
            print(f"  PATCH falló {dom}: {ex}", file=sys.stderr)
        done += 1
        if done % 100 == 0:
            print(f"  {done}/{len(work)} dominios | {api_calls} API | último {dom}: {body}", flush=True)
    print(f"LISTO: {done} dominios procesados, {api_calls} llamadas GetLeads", flush=True)


if __name__ == "__main__":
    main()
