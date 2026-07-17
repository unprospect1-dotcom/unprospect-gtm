#!/usr/bin/env python3
"""Prepara faltantes y re-limpia site_crawls sin volver a visitar sitios."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlparse

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clean_markdown import attach_evidence_to_pages, build_segmentation_context
from supabase_auth import resolve_service_key


URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = resolve_service_key(URL, os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
                          os.environ.get("SUPABASE_TOKEN", ""))
REST = f"{URL}/rest/v1"
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
DOMAIN_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.[a-z0-9-]{2,63}$")


def normalize_domain(value: str | None) -> str | None:
    value = (value or "").strip().lower()
    if not value:
        return None
    candidate = value if "://" in value else "https://" + value
    try:
        host = (urlparse(candidate).hostname or "").removeprefix("www.").rstrip(".")
        host = host.encode("idna").decode("ascii")
    except (UnicodeError, ValueError):
        return None
    return host if DOMAIN_RE.fullmatch(host) else None


def fetch_rows(table: str, select: str, filters: dict | None = None,
               page_size: int = 1000):
    offset = 0
    params = {"select": select, **(filters or {})}
    while True:
        headers = {**HEADERS, "Range": f"{offset}-{offset + page_size - 1}"}
        response = requests.get(f"{REST}/{table}", params=params, headers=headers, timeout=120)
        response.raise_for_status()
        rows = response.json()
        yield from rows
        if len(rows) < page_size:
            break
        offset += page_size


def export_missing(path: Path) -> int:
    targets: set[str] = set()
    for row in fetch_rows("list_companies", "domain", {"order": "id.asc"}):
        if domain := normalize_domain(row.get("domain")):
            targets.add(domain)
    for row in fetch_rows("companies", "domain,website", {"order": "id.asc"}):
        if domain := normalize_domain(row.get("domain") or row.get("website")):
            targets.add(domain)
    for row in fetch_rows("sofoms", "domain", {"discarded": "eq.false", "order": "id.asc"}):
        if domain := normalize_domain(row.get("domain")):
            targets.add(domain)

    crawled = {
        domain for row in fetch_rows("site_crawls", "domain", {"order": "domain.asc"})
        if (domain := normalize_domain(row.get("domain")))
    }
    missing = sorted(targets - crawled)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(missing) + ("\n" if missing else ""), encoding="utf-8")
    print(json.dumps({"targets": len(targets), "crawled": len(crawled),
                      "missing": len(missing), "output": str(path)}, ensure_ascii=False))
    return len(missing)


def post_rows(rows: list[dict]) -> None:
    headers = {**HEADERS, "Content-Type": "application/json",
               "Prefer": "resolution=merge-duplicates,return=minimal"}
    last_error: requests.RequestException | None = None
    for attempt in range(4):
        try:
            response = requests.post(f"{REST}/site_crawls", json=rows,
                                     headers=headers, timeout=180)
            response.raise_for_status()
            return
        except requests.RequestException as exc:
            last_error = exc
            if attempt == 3:
                break
            time.sleep(2 ** attempt)
    if len(rows) > 1:
        middle = len(rows) // 2
        post_rows(rows[:middle])
        post_rows(rows[middle:])
        return
    row = rows[0]
    if "pages" in row:
        slim = {key: value for key, value in row.items() if key != "pages"}
        print(json.dumps({"warning": "pages_jsonb_not_updated", "domain": row["domain"]},
                         ensure_ascii=False), file=sys.stderr, flush=True)
        post_rows([slim])
        return
    raise last_error or RuntimeError("upsert falló sin detalle")


def reclean(checkpoint: Path, page_size: int, batch_size: int,
            limit: int | None, dry_run: bool) -> int:
    done = set()
    if checkpoint.exists():
        done = {line.strip() for line in checkpoint.read_text(encoding="utf-8").splitlines()
                if line.strip()}
    processed = 0
    pending: list[dict] = []
    pending_domains: list[str] = []

    def flush():
        nonlocal pending, pending_domains
        if not pending:
            return
        if not dry_run:
            post_rows(pending)
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            with checkpoint.open("a", encoding="utf-8") as handle:
                handle.write("\n".join(pending_domains) + "\n")
        pending, pending_domains = [], []

    filters = {"ok": "eq.true", "combined_markdown": "not.is.null", "order": "domain.asc"}
    for row in fetch_rows("site_crawls", "domain,pages,combined_markdown", filters, page_size):
        domain = row["domain"]
        if domain in done:
            continue
        analysis = build_segmentation_context(row.get("combined_markdown") or "")
        pages = attach_evidence_to_pages(row.get("pages"), analysis["meta"])
        pending.append({"domain": domain, "pages": pages, "clean_text": analysis["text"]})
        pending_domains.append(domain)
        processed += 1
        if len(pending) >= batch_size:
            flush()
            print(json.dumps({"processed_this_run": processed,
                              "checkpoint_total_before": len(done)}, ensure_ascii=False), flush=True)
        if limit and processed >= limit:
            break
    flush()
    print(json.dumps({"processed": processed, "dry_run": dry_run,
                      "checkpoint": str(checkpoint)}, ensure_ascii=False))
    return processed


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    missing = sub.add_parser("export-missing")
    missing.add_argument("--out", type=Path, required=True)
    clean = sub.add_parser("reclean")
    clean.add_argument("--checkpoint", type=Path, required=True)
    clean.add_argument("--page-size", type=int, default=25)
    clean.add_argument("--batch-size", type=int, default=10)
    clean.add_argument("--limit", type=int)
    clean.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command == "export-missing":
        export_missing(args.out)
    else:
        reclean(args.checkpoint, args.page_size, args.batch_size, args.limit, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
