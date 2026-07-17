#!/usr/bin/env python3
"""Freeze the current Supabase GTM profiling queue into deterministic batches."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

SIGNAL_WORDS = (
    "servicio", "soluci", "producto", "empresa", "cliente", "industr", "sector",
    "negocio", "plataforma", "software", "equipo", "distribu", "fabric", "caso",
    "proyecto", "contact", "ventas", "corpor", "mayoreo", "b2b", "para ti",
)


def headers(key: str) -> dict[str, str]:
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def get_json(url: str, request_headers: dict[str, str], params: dict[str, str] | None = None, timeout: int = 120):
    query = f"?{urlencode(params)}" if params else ""
    request = Request(f"{url}{query}", headers=request_headers, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        return error.code, {"error": body[:500]}
    except URLError as error:
        raise RuntimeError(f"Network error for {url}: {error.reason}") from error


def service_key(base_url: str) -> str:
    configured = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if configured:
        status, _ = get_json(
            f"{base_url.rstrip('/')}/rest/v1/site_crawls",
            headers(configured),
            {"select": "domain", "limit": "1"},
            timeout=30,
        )
        if status < 400:
            return configured

    token = os.environ.get("SUPABASE_TOKEN", "")
    project_ref = urlparse(base_url).hostname.split(".")[0] if urlparse(base_url).hostname else ""
    if not token or not project_ref:
        raise RuntimeError("No valid Supabase server-side credential is available")
    status, payload = get_json(
        f"https://api.supabase.com/v1/projects/{project_ref}/api-keys",
        {"Authorization": f"Bearer {token}"},
        {"reveal": "true"},
        timeout=60,
    )
    if status >= 400 or not isinstance(payload, list):
        raise RuntimeError("Could not retrieve a current Supabase server-side key")
    for item in payload:
        if item.get("type") != "secret" and item.get("name") != "service_role":
            continue
        candidate = item.get("api_key", "")
        test_status, _ = get_json(
            f"{base_url.rstrip('/')}/rest/v1/site_crawls",
            headers(candidate),
            {"select": "domain", "limit": "1"},
            timeout=30,
        )
        if test_status < 400:
            return candidate
    raise RuntimeError("No current server-side Supabase key was accepted")


def fetch_all(base_url: str, key: str, table: str, params: dict[str, str], page_size: int = 500) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        page_params = dict(params)
        page_params.update({"limit": str(page_size), "offset": str(offset)})
        status, page = get_json(
            f"{base_url.rstrip('/')}/rest/v1/{table}",
            headers(key),
            page_params,
            timeout=120,
        )
        if status >= 400:
            raise RuntimeError(f"Supabase returned HTTP {status} for {table}")
        if not isinstance(page, list):
            raise RuntimeError(f"Unexpected {table} response")
        rows.extend(page)
        if len(page) < page_size:
            return rows
        offset += page_size


def compact_text(text: str, limit: int = 8_000) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text

    head_budget = 5_000
    signal_budget = 2_300
    tail_budget = limit - head_budget - signal_budget - 2
    head = text[:head_budget].rstrip()
    remainder = text[head_budget:]
    selected: list[str] = []
    used = 0
    for line in remainder.splitlines():
        clean = " ".join(line.split())
        if not clean or not any(word in clean.casefold() for word in SIGNAL_WORDS):
            continue
        if clean in head or clean in selected:
            continue
        addition = clean[:600]
        if used + len(addition) + 1 > signal_budget:
            break
        selected.append(addition)
        used += len(addition) + 1
    middle = "\n".join(selected)
    tail = text[-tail_budget:].lstrip()
    return f"{head}\n{middle}\n{tail}"[:limit]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--size", type=int, default=8)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.size < 1 or args.size > 10:
        parser.error("--size must be between 1 and 10")

    url = os.environ["SUPABASE_URL"]
    key = service_key(url)

    queue_rows = fetch_all(
        url,
        key,
        "company_gtm_profiles",
        {
            "select": "domain,current_source_hash,source_clean_chars,profile_status",
            "profile_status": "in.(pending,stale,failed)",
            "order": "domain.asc",
        },
    )
    queue = {row["domain"]: row for row in queue_rows}

    crawl_rows = fetch_all(
        url,
        key,
        "site_crawls",
        {
            "select": "domain,ok,clean_text,crawled_at",
            "clean_text": "not.is.null",
            "order": "domain.asc",
        },
        page_size=250,
    )

    companies: list[dict] = []
    skipped: list[dict] = []
    for crawl in crawl_rows:
        domain = crawl["domain"]
        expected = queue.get(domain)
        if not expected:
            continue
        clean_text = crawl.get("clean_text") or ""
        source_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()
        if source_hash != expected.get("current_source_hash"):
            skipped.append({"domain": domain, "reason": "source_hash_changed"})
            continue
        context = compact_text(clean_text)
        companies.append(
            {
                "domain": domain,
                "clean_text": context,
                "source_hash": source_hash,
                "source_chars": len(clean_text.strip()),
                "context_chars": len(context),
                "source_crawl_ok": bool(crawl.get("ok")),
                "source_crawled_at": crawl.get("crawled_at"),
            }
        )

    companies.sort(key=lambda item: item["domain"])
    if args.limit is not None:
        companies = companies[: args.limit]

    args.outdir.mkdir(parents=True, exist_ok=True)
    manifest = args.outdir / "manifest.jsonl"
    manifest.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in companies),
        encoding="utf-8",
    )
    write_json(args.outdir / "skipped.json", skipped)

    batches_dir = args.outdir / "batches"
    batches_dir.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(companies), args.size):
        batch_number = start // args.size + 1
        write_json(
            batches_dir / f"batch_{batch_number:05d}.json",
            {"companies": companies[start : start + args.size]},
        )

    summary = {
        "queue_rows": len(queue_rows),
        "companies": len(companies),
        "batches": (len(companies) + args.size - 1) // args.size,
        "skipped_source_changes": len(skipped),
        "batch_size": args.size,
        "max_context_chars": 8_000,
    }
    write_json(args.outdir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
