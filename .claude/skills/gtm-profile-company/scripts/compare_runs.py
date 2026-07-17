#!/usr/bin/env python3
"""Compare two blind GTM profile runs and emit agreement plus a review queue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FIELDS = ["entity_type", "business_model", "b2b_line_present", "sales_economics", "outbound_fit", "outbound_scope"]


def load(path: Path, key: str | None = None) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if key and isinstance(payload, dict):
        payload = payload.get(key)
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain an array")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--run-a", required=True, type=Path)
    parser.add_argument("--run-b", required=True, type=Path)
    args = parser.parse_args()

    source_domains = [item["domain"] for item in load(args.source, "companies")]
    run_a = {item["domain"]: item for item in load(args.run_a)}
    run_b = {item["domain"]: item for item in load(args.run_b)}
    if set(run_a) != set(source_domains) or set(run_b) != set(source_domains):
        raise ValueError("Both runs must contain every source domain exactly once")

    counts = {field: 0 for field in FIELDS}
    review = []
    for domain in source_domains:
        differing = [field for field in FIELDS if run_a[domain].get(field) != run_b[domain].get(field)]
        for field in FIELDS:
            counts[field] += run_a[domain].get(field) == run_b[domain].get(field)
        if differing:
            review.append(
                {
                    "domain": domain,
                    "fields": differing,
                    "run_a": {field: run_a[domain].get(field) for field in differing},
                    "run_b": {field: run_b[domain].get(field) for field in differing},
                }
            )

    total = len(source_domains)
    print(
        json.dumps(
            {
                "total": total,
                "full_agreement": total - len(review),
                "agreement": {field: {"count": count, "rate": count / total if total else 0} for field, count in counts.items()},
                "review_queue": review,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
