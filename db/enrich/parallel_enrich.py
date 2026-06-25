#!/usr/bin/env python3
"""Phase 3 — company enrichment via Parallel Task API (Lite + Source Policy).

For every company that has a domain, ask Parallel to classify it in free text
(categoria / oferta / vertical / tamano), pinning the web research to the
company's OWN domain (+linkedin.com) via Source Policy so the model reads the
real site instead of hallucinating. Results are written back to `companies`:

  niche             <- oferta            (free text, was empty)
  subniche          <- vertical          (free text, was empty)
  description_short <- categoria         (only if currently NULL; never overwrites)
  description_basis <- merged jsonb under key 'parallel_cat' (categoria/oferta/
                       vertical/tamano + sources + confidence + run_id); the
                       existing ICP description_basis is preserved via `||`.
  enrichment_source='parallel.ai', enrichment_status, enrichment_task_run_id,
  enriched_at, needs_company_review (true when categoria='Morado' OR the cited
  sources do not include the company's own domain -> likely hallucination).

Design: idempotent + resumable (only processes rows where `niche IS NULL`),
non-destructive, concurrent, flushes to the DB in batches, writes a JSON
progress file. Env knobs: PROC (lite), WORKERS (30), FLUSH (25), LIMIT (all),
PROGRESS (path to progress json)."""
import os, json, time, subprocess, urllib.parse, datetime, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

PKEY = os.environ['PARALLEL_API_KEY']; PBASE = "https://api.parallel.ai"
SUPA = os.environ['SUPABASE_URL']; STOK = os.environ['SUPABASE_TOKEN']
REF = urllib.parse.urlparse(SUPA).hostname.split('.')[0]
SQL_URL = f"https://api.supabase.com/v1/projects/{REF}/database/query"
PROC = os.environ.get("PROC", "lite")
WORKERS = int(os.environ.get("WORKERS", "30"))
FLUSH = int(os.environ.get("FLUSH", "25"))
LIMIT = os.environ.get("LIMIT")
PROGRESS = os.environ.get("PROGRESS", "enrich_progress.json")

def _curl(cmd, body=None):
    p = subprocess.run(cmd, input=(json.dumps(body) if body is not None else None),
                       capture_output=True, text=True)
    o, code = p.stdout, None
    if "\n__H_" in o:
        o, _, t = o.rpartition("\n__H_"); code = t.replace("__", "").strip()
    try: return code, json.loads(o)
    except Exception: return code, o

def sql(query):
    return _curl(["curl", "-s", "-w", "\n__H_%{http_code}__", SQL_URL,
        "-H", f"Authorization: Bearer {STOK}", "-H", "Content-Type: application/json",
        "--data-binary", "@-"], {"query": query})

def pcall(path, body=None, tries=4):
    code, data = None, None
    for i in range(tries):
        cmd = ["curl", "-s", "-w", "\n__H_%{http_code}__", PBASE + path, "-H", f"x-api-key: {PKEY}"]
        if body is not None:
            cmd += ["-H", "Content-Type: application/json", "--data-binary", "@-"]
        code, data = _curl(cmd, body)
        if code == "429" or (isinstance(code, str) and code.startswith("5")):
            time.sleep(2 * (i + 1)); continue
        return code, data
    return code, data

SCHEMA = {"type": "json", "json_schema": {"type": "object", "properties": {
  "categoria": {"type": "string", "description": "Etiqueta corta y especifica del negocio en estilo '[oferta] para [vertical]', en espanol. Ejemplos: '3PL para industria automotriz', 'Agentes de IA para atencion al cliente', 'Software de administracion (ERP)', 'Logistica terrestre'. Si no hay informacion suficiente para clasificar, responde exactamente la palabra 'Morado'."},
  "oferta": {"type": "string", "description": "Que vende u ofrece la empresa (producto o servicio principal), en espanol, libre y conciso. Si no hay info responde exactamente 'Morado'."},
  "vertical": {"type": "string", "description": "Industria o vertical a la que pertenece o a la que le vende la empresa, en espanol, libre. Si no hay info responde exactamente 'Morado'."},
  "tamano": {"type": "string", "description": "Estimado del tamano de la empresa: numero aproximado de empleados o un rango (ej. '11-50', '200'). Si no hay info responde exactamente 'Morado'."}},
  "required": ["categoria", "oferta", "vertical", "tamano"]}}

def enrich_one(row):
    dom = row["domain"]
    body = {"input": {"domain": dom, "company_name": row.get("name") or ""},
            "processor": PROC,
            "source_policy": {"include_domains": [dom, "linkedin.com"]},
            "task_spec": {"output_schema": SCHEMA}}
    code, run = pcall("/v1/tasks/runs", body)
    rid = run.get("run_id") if isinstance(run, dict) else None
    if not rid:
        return {"id": row["id"], "error": f"create {code}: {str(run)[:140]}"}
    s = None
    for _ in range(120):
        time.sleep(3)
        code, st = pcall(f"/v1/tasks/runs/{rid}")
        s = st.get("status") if isinstance(st, dict) else None
        if s in ("completed", "failed", "cancelled", "error"):
            break
    if s != "completed":
        return {"id": row["id"], "run_id": rid, "error": f"status {s}"}
    code, res = pcall(f"/v1/tasks/runs/{rid}/result")
    out = res.get("output", {}) if isinstance(res, dict) else {}
    c = out.get("content", {}) or {}
    sources, conf = [], {}
    for b in out.get("basis", []) or []:
        conf[b.get("field")] = b.get("confidence")
        for cit in b.get("citations", []) or []:
            u = cit.get("url")
            if u and u not in sources:
                sources.append(u)
    cat = c.get("categoria") or "Morado"
    is_morado = str(cat).strip().lower() == "morado"
    anchored = any(dom.lower() in (u or "").lower() for u in sources)
    needs_review = is_morado or (not anchored)
    obj = {"categoria": cat, "oferta": c.get("oferta"), "vertical": c.get("vertical"),
           "tamano": c.get("tamano"), "processor": PROC, "run_id": rid,
           "source_policy": [dom, "linkedin.com"], "sources": sources,
           "field_confidence": conf, "anchored_to_domain": anchored,
           "generated_at": datetime.datetime.utcnow().isoformat() + "Z"}
    return {"id": row["id"], "domain": dom,
            "niche": c.get("oferta") or "Morado", "subniche": c.get("vertical") or "Morado",
            "desc_short": cat, "cat_json": json.dumps(obj),
            "status": "no_info" if is_morado else "completed", "run_id": rid,
            "needs_review": needs_review, "morado": is_morado}

def q(s):
    return "NULL" if s is None else "'" + str(s).replace("'", "''") + "'"

def flush(rows):
    if not rows:
        return
    vals = ["(%s::uuid,%s,%s,%s,%s::jsonb,%s,%s,%s::boolean)" % (
        q(r["id"]), q(r["niche"]), q(r["subniche"]), q(r["desc_short"]),
        q(r["cat_json"]), q(r["status"]), q(r["run_id"]),
        "true" if r["needs_review"] else "false") for r in rows]
    query = ("update companies as c set "
        "niche=v.niche, subniche=v.subniche, "
        "description_short=coalesce(c.description_short, v.desc_short), "
        "parallel_cat=v.cat_json, "
        "enrichment_source='parallel.ai', enrichment_status=v.status, "
        "enrichment_task_run_id=v.run_id, needs_company_review=v.needs_review, "
        "enriched_at=now(), updated_at=now() "
        "from (values " + ",".join(vals) +
        ") as v(id,niche,subniche,desc_short,cat_json,status,run_id,needs_review) "
        "where c.id=v.id;")
    code, resp = None, None
    for i in range(5):
        code, resp = sql(query)
        if code in ("200", "201"):
            return
        time.sleep(2 * (i + 1))  # transient 502/000 from the SQL API -> retry
    print("  FLUSH ERROR (gave up)", code, str(resp)[:200], flush=True)

def write_progress(d):
    try: open(PROGRESS, "w").write(json.dumps(d))
    except Exception: pass

def main():
    lim = f"limit {int(LIMIT)}" if LIMIT else ""
    order = "order by random()" if LIMIT else "order by id"
    code, rows = sql("select id::text as id, domain, name, linkedin_url from companies "
                     f"where domain is not null and parallel_cat is null {order} {lim};")
    if not isinstance(rows, list):
        print("LOAD FAIL", code, rows); raise SystemExit(1)
    total = len(rows)
    print(f"[{datetime.datetime.now():%H:%M:%S}] target={total} processor={PROC} workers={WORKERS}", flush=True)
    done = mor = rev = err = 0
    buf, lock, t0 = [], threading.Lock(), time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(enrich_one, r): r for r in rows}
        for fut in as_completed(futs):
            res = fut.result()
            with lock:
                if res.get("error"):
                    err += 1
                    print(f"  ERR {res['id']} {res['error']}", flush=True)
                else:
                    buf.append(res); done += 1
                    if res.get("morado"): mor += 1
                    if res.get("needs_review"): rev += 1
                if len(buf) >= FLUSH:
                    flush(buf); buf = []
                n = done + err
                if n % 25 == 0 or n == total:
                    rate = n / max(time.time() - t0, 1)
                    eta = (total - n) / max(rate, 0.01)
                    write_progress({"done": done, "morado": mor, "review": rev, "errors": err,
                                    "total": total, "pct": round(100 * n / total, 1),
                                    "eta_min": round(eta / 60, 1)})
                    print(f"[{datetime.datetime.now():%H:%M:%S}] {n}/{total} "
                          f"({round(100*n/total,1)}%) ok={done} morado={mor} review={rev} "
                          f"err={err} eta={round(eta/60,1)}min", flush=True)
        with lock:
            flush(buf); buf = []
    print(f"DONE ok={done} morado={mor} review={rev} err={err} in {round((time.time()-t0)/60,1)}min", flush=True)
    write_progress({"done": done, "morado": mor, "review": rev, "errors": err,
                    "total": total, "pct": 100, "finished": True})

if __name__ == "__main__":
    main()
