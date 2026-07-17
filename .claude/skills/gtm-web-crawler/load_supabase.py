#!/usr/bin/env python3
"""Carga los resultados del crawl a Supabase (tabla site_crawls).

- Crea la tabla si no existe (DDL via Management API con SUPABASE_TOKEN=sbp_...).
- Upsert por dominio via PostgREST (SUPABASE_SERVICE_ROLE_KEY), en lotes.

Fuente: un dir de .json (crawl_out/) o el jsonl.gz consolidado.
Uso:
  python load_supabase.py --in crawl_out
  python load_supabase.py --in data/sofoms_crawls.jsonl.gz
"""
import os, sys, json, glob, gzip, argparse, time, re
from datetime import datetime, timezone
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clean_markdown import CLEAN_VERSION, attach_evidence_to_pages, build_segmentation_context
from supabase_auth import resolve_service_key

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
MGMT_TOKEN = os.environ.get("SUPABASE_TOKEN", "")
SERVICE_KEY = resolve_service_key(SUPABASE_URL,
                                  os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
                                  MGMT_TOKEN)
REF = re.search(r"https://([a-z0-9]+)\.supabase", SUPABASE_URL).group(1)

DDL = """
create table if not exists site_crawls (
  domain text primary key,
  ok boolean not null default false,
  n_pages int not null default 0,
  secs numeric,
  reason text,
  http_status text,
  pages jsonb,
  combined_markdown text,
  clean_text text,
  crawled_at timestamptz not null default now()
);
alter table site_crawls add column if not exists clean_text text;
alter table site_crawls enable row level security;
grant select, insert, update on table site_crawls to service_role;
create index if not exists site_crawls_ok_idx on site_crawls(ok);
"""

def _post(url, body, headers):
    r = requests.post(url, json=body, headers=headers, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code}: {r.text[:200]}")
    return r.status_code, r.text

def mgmt_sql(sql):
    return _post(f"https://api.supabase.com/v1/projects/{REF}/database/query",
                 {"query": sql},
                 {"Authorization": f"Bearer {MGMT_TOKEN}", "Content-Type": "application/json"})

def ensure_table():
    st, body = mgmt_sql(DDL)
    print(f"DDL site_crawls -> {st}")

def upsert(rows):
    hdr = {"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}",
           "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"}
    for attempt in range(4):
        try:
            st, _ = _post(f"{SUPABASE_URL}/rest/v1/site_crawls", rows, hdr)
            return st
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def to_row(d):
    raw = d.get("combined_markdown") or ""
    clean_meta = d.get("clean_meta") or {}
    pages = d.get("pages") or None
    if d.get("clean_text") and clean_meta.get("version") == CLEAN_VERSION:
        compact = d["clean_text"]
    else:
        analysis = build_segmentation_context(raw)
        compact = analysis["text"]
        pages = attach_evidence_to_pages(pages, analysis["meta"])
    return {"domain": d["domain"], "ok": d["ok"], "n_pages": d.get("n_pages", 0),
            "secs": d.get("secs"), "reason": d.get("reason"),
            "pages": pages,
            "combined_markdown": raw or None,
            "clean_text": compact or None,
            # Postgres defaults only run on INSERT. Set this explicitly so an
            # upsert records the latest crawl instead of keeping an old date.
            "crawled_at": d.get("crawled_at") or datetime.now(timezone.utc).isoformat()}

def read_records(path):
    if os.path.isdir(path):
        for f in glob.glob(os.path.join(path, "*.json")):
            with open(f, encoding="utf-8") as handle:
                yield json.load(handle)
    elif path.endswith(".gz"):
        for line in gzip.open(path, "rt", encoding="utf-8"):
            if line.strip():
                yield json.loads(line)
    else:
        with open(path, encoding="utf-8-sig") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--batch", type=int, default=50)
    args = ap.parse_args()

    ensure_table()
    batch, total, done = [], 0, 0
    for d in read_records(args.inp):
        batch.append(to_row(d))
        total += 1
        if len(batch) >= args.batch:
            upsert(batch); done += len(batch); batch = []
            print(f"  upserted {done}", flush=True)
    if batch:
        upsert(batch); done += len(batch)
    print(f"OK: {done}/{total} filas en site_crawls")

if __name__ == "__main__":
    main()
