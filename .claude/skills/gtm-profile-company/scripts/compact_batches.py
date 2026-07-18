#!/usr/bin/env python3
"""Create smaller first-pass context while preserving the immutable 8K source batches."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SIGNAL_WORDS = (
    "servicio", "soluci", "producto", "empresa", "cliente", "industr", "sector",
    "negocio", "plataforma", "software", "equipo", "distribu", "fabric", "caso",
    "proyecto", "contact", "ventas", "corpor", "mayoreo", "b2b", "organiza",
    "instituci", "gobierno", "universidad", "ofrecemos", "ayudamos", "especializa",
    "mercado", "confían", "clientes que", "testimonio", "resultado",
)


def compact_text(text: str, limit: int = 4_000) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    head = text[:2_500].rstrip()
    selected: list[str] = []
    used = 0
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        folded = line.casefold()
        if not line or not any(word in folded for word in SIGNAL_WORDS):
            continue
        if line in head or line in selected:
            continue
        addition = line[:500]
        if used + len(addition) + 1 > 1_150:
            break
        selected.append(addition)
        used += len(addition) + 1
    tail = text[-348:].lstrip()
    middle = "\n".join(selected)
    return f"{head}\n{middle}\n{tail}"[:limit]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int)
    parser.add_argument("--limit", type=int, default=4_000)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(args.input_dir.glob("batch_*.json"))
    written = 0
    companies = 0
    source_chars = 0
    context_chars = 0
    for path in files:
        number = int(path.stem.split("_")[-1])
        if number < args.start or args.end is not None and number > args.end:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for company in payload["companies"]:
            source = company["clean_text"]
            compact = compact_text(source, args.limit)
            company["clean_text"] = compact
            company["context_chars"] = len(compact)
            source_chars += len(source)
            context_chars += len(compact)
            companies += 1
        (args.output_dir / path.name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        written += 1

    print(
        json.dumps(
            {
                "batches": written,
                "companies": companies,
                "source_chars": source_chars,
                "context_chars": context_chars,
                "retained_rate": context_chars / source_chars if source_chars else 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
