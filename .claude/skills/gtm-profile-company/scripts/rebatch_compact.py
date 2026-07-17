#!/usr/bin/env python3
"""Flatten immutable source batches and create compact batches of up to 10 companies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from compact_batches import compact_text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--size", type=int, default=10)
    parser.add_argument("--context-limit", type=int, default=4_000)
    args = parser.parse_args()
    if args.size < 1 or args.size > 10:
        parser.error("--size must be between 1 and 10")

    companies: list[dict] = []
    for number in range(args.start, args.end + 1):
        source = args.input_dir / f"batch_{number:05d}.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        for company in payload["companies"]:
            company["clean_text"] = compact_text(company["clean_text"], args.context_limit)
            company["context_chars"] = len(company["clean_text"])
            companies.append(company)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(companies), args.size):
        number = start // args.size + 1
        target = args.output_dir / f"batch_fast_{number:05d}.json"
        target.write_text(
            json.dumps({"companies": companies[start : start + args.size]}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "companies": len(companies),
                "batches": (len(companies) + args.size - 1) // args.size,
                "batch_size": args.size,
            }
        )
    )


if __name__ == "__main__":
    main()
