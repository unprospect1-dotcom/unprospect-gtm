#!/usr/bin/env python3
"""Split domain + clean_text JSON into small deterministic worker batches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_companies(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    companies = payload.get("companies") if isinstance(payload, dict) else payload
    if not isinstance(companies, list):
        raise ValueError("Input must be an array or an object with a companies array")
    for index, company in enumerate(companies):
        if not isinstance(company, dict) or not company.get("domain"):
            raise ValueError(f"Company {index} is missing domain")
        if not isinstance(company.get("clean_text"), str):
            raise ValueError(f"Company {company.get('domain')} is missing clean_text")
    return sorted(companies, key=lambda item: item["domain"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--size", type=int, default=8)
    args = parser.parse_args()

    if args.size < 1 or args.size > 10:
        parser.error("--size must be between 1 and 10")

    companies = load_companies(args.input)
    args.outdir.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(companies), args.size):
        batch_number = start // args.size + 1
        output = args.outdir / f"batch_{batch_number:03d}.json"
        output.write_text(
            json.dumps({"companies": companies[start : start + args.size]}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({"companies": len(companies), "batches": (len(companies) + args.size - 1) // args.size}))


if __name__ == "__main__":
    main()
