#!/usr/bin/env python3
"""Validate two blind pass directories and build consensus/arbitration artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_profiles import validate


FIELDS = ["entity_type", "business_model", "b2b_line_present", "sales_economics", "outbound_fit", "outbound_scope"]


def load(path: Path, key: str | None = None):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if key and isinstance(payload, dict):
        payload = payload.get(key)
    return payload


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--run-a-dir", required=True, type=Path)
    parser.add_argument("--run-b-dir", required=True, type=Path)
    parser.add_argument("--outdir", required=True, type=Path)
    parser.add_argument("--arbitration-size", type=int, default=8)
    args = parser.parse_args()

    source_files = sorted(args.source_dir.glob("batch_*.json"))
    validation_errors: list[str] = []
    sources: dict[str, dict] = {}
    pass_a: dict[str, dict] = {}
    pass_b: dict[str, dict] = {}

    for source_file in source_files:
        run_a_file = args.run_a_dir / source_file.name
        run_b_file = args.run_b_dir / source_file.name
        if not run_a_file.exists():
            validation_errors.append(f"missing pass A file: {source_file.name}")
            continue
        if not run_b_file.exists():
            validation_errors.append(f"missing pass B file: {source_file.name}")
            continue
        validation_errors.extend(f"{source_file.name} pass A: {error}" for error in validate(source_file, run_a_file))
        validation_errors.extend(f"{source_file.name} pass B: {error}" for error in validate(source_file, run_b_file))
        for item in load(source_file, "companies"):
            sources[item["domain"]] = item
        for item in load(run_a_file):
            pass_a[item["domain"]] = item
        for item in load(run_b_file):
            pass_b[item["domain"]] = item

    if validation_errors:
        write_json(args.outdir / "validation_errors.json", validation_errors)
        print(json.dumps({"valid": False, "errors": len(validation_errors)}, ensure_ascii=False))
        raise SystemExit(1)

    agreement = {field: 0 for field in FIELDS}
    consensus: list[dict] = []
    review: list[dict] = []
    arbitration_sources: list[dict] = []

    for domain in sorted(sources):
        first = pass_a[domain]
        second = pass_b[domain]
        differing = [field for field in FIELDS if first.get(field) != second.get(field)]
        for field in FIELDS:
            agreement[field] += first.get(field) == second.get(field)
        if differing:
            review.append(
                {
                    "domain": domain,
                    "fields": differing,
                    "pass_a": {field: first.get(field) for field in differing},
                    "pass_b": {field: second.get(field) for field in differing},
                    "source_hash": sources[domain].get("source_hash"),
                }
            )
            arbitration_sources.append(sources[domain])
            continue

        business_model = first["business_model"]
        accepted = dict(first)
        accepted["is_b2b"] = (
            True if business_model in {"b2b", "mixed"}
            else False if business_model in {"b2c", "noncommercial"}
            else None
        )
        accepted["source_hash"] = sources[domain].get("source_hash")
        accepted["consensus_fields"] = list(FIELDS)
        accepted["decision_method"] = "consensus"
        consensus.append(accepted)

    arbitration_dir = args.outdir / "arbitration_batches"
    for start in range(0, len(arbitration_sources), args.arbitration_size):
        number = start // args.arbitration_size + 1
        write_json(arbitration_dir / f"batch_{number:05d}.json", {"companies": arbitration_sources[start : start + args.arbitration_size]})

    total = len(sources)
    summary = {
        "valid": True,
        "total": total,
        "full_consensus": len(consensus),
        "needs_arbitration": len(review),
        "agreement": {
            field: {"count": count, "rate": count / total if total else 0}
            for field, count in agreement.items()
        },
        "arbitration_batches": (len(arbitration_sources) + args.arbitration_size - 1) // args.arbitration_size,
    }
    write_json(args.outdir / "consensus.json", consensus)
    write_json(args.outdir / "review_queue.json", review)
    write_json(args.outdir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
