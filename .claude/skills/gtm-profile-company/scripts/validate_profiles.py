#!/usr/bin/env python3
"""Validate compact GTM profiles and literal evidence against source clean_text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ENUMS = {
    "entity_type": {"company", "government", "education", "nonprofit", "media_or_directory", "unclear"},
    "business_model": {"b2b", "b2c", "mixed", "noncommercial", "unclear"},
    "confidence": {"high", "medium", "low"},
    "sales_economics": {"strong", "plausible", "weak", "not_applicable", "unclear"},
    "outbound_fit": {"high", "medium", "low", "unclear"},
    "outbound_scope": {"companywide", "b2b_line_only", "none", "unclear"},
}


def load_array(path: Path, key: str | None = None) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if key and isinstance(payload, dict):
        payload = payload.get(key)
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain an array")
    return payload


def word_count(value: object) -> int:
    return len(str(value).split()) if value else 0


def validate(source_path: Path, results_path: Path) -> list[str]:
    source = load_array(source_path, "companies")
    results = load_array(results_path)
    clean_by_domain = {item["domain"]: item.get("clean_text", "") for item in source}
    errors: list[str] = []
    seen: set[str] = set()

    for profile in results:
        domain = profile.get("domain")
        if domain not in clean_by_domain:
            errors.append(f"unknown domain: {domain}")
            continue
        if domain in seen:
            errors.append(f"duplicate domain: {domain}")
        seen.add(domain)

        for field, allowed in ENUMS.items():
            if profile.get(field) not in allowed:
                errors.append(f"{domain}: invalid {field}={profile.get(field)!r}")
        if not isinstance(profile.get("b2b_line_present"), bool):
            errors.append(f"{domain}: b2b_line_present must be boolean")
        if word_count(profile.get("sells")) > 18:
            errors.append(f"{domain}: sells exceeds 18 words")
        if word_count(profile.get("primary_customer")) > 20:
            errors.append(f"{domain}: primary_customer exceeds 20 words")
        if word_count(profile.get("outbound_reason")) > 25:
            errors.append(f"{domain}: outbound_reason exceeds 25 words")

        icp = profile.get("probable_icp")
        if not isinstance(icp, dict) or set(icp) != {"company_type", "industries", "buyer", "geography"}:
            errors.append(f"{domain}: probable_icp has invalid shape")
        else:
            if not isinstance(icp.get("industries"), list):
                errors.append(f"{domain}: industries must be an array")
            if not isinstance(icp.get("geography"), list):
                errors.append(f"{domain}: geography must be an array")

        evidence = profile.get("evidence")
        if not isinstance(evidence, list) or len(evidence) > 2:
            errors.append(f"{domain}: evidence must be an array with at most 2 quotes")
        else:
            for quote in evidence:
                if not isinstance(quote, str) or quote not in clean_by_domain[domain]:
                    errors.append(f"{domain}: evidence is not a literal clean_text substring: {quote!r}")

        if profile.get("business_model") in {"b2b", "mixed"} and profile.get("b2b_line_present") is not True:
            errors.append(f"{domain}: b2b/mixed requires b2b_line_present=true")
        if profile.get("business_model") == "noncommercial":
            if profile.get("sales_economics") != "not_applicable":
                errors.append(f"{domain}: noncommercial requires sales_economics=not_applicable")
            if profile.get("outbound_fit") != "low" or profile.get("outbound_scope") != "none":
                errors.append(f"{domain}: noncommercial requires outbound_fit=low and outbound_scope=none")
        if profile.get("outbound_fit") in {"high", "medium"} and not profile.get("b2b_line_present"):
            errors.append(f"{domain}: high/medium outbound_fit requires a B2B line")
        if profile.get("outbound_scope") in {"companywide", "b2b_line_only"} and not profile.get("b2b_line_present"):
            errors.append(f"{domain}: prospectable outbound_scope requires a B2B line")

    missing = sorted(set(clean_by_domain) - seen)
    errors.extend(f"missing domain: {domain}" for domain in missing)
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    args = parser.parse_args()
    errors = validate(args.source, args.results)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
