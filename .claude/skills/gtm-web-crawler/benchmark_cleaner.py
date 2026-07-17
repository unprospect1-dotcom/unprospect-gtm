#!/usr/bin/env python3
"""Benchmark determinista del cleaner sobre crawls reales.

Mide lo que importa para segmentación, no similitud superficial de texto:
retención de entidades, cobertura de señales GTM, ruido y presupuesto de contexto.
"""

from __future__ import annotations

import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import re
import statistics
import sys

from clean_markdown import analyze_markdown, noise_line_count


DEFAULT_DATA = Path(__file__).resolve().parent / "data" / "sofoms_crawls.jsonl.gz"


def legacy_clean_markdown(md: str) -> str:
    """Baseline v1 congelado para comparar el cambio."""
    if not md:
        return ""
    ui_noise = re.compile(r"""^\s*(
        saltar\ al\ contenido | ir\ al\ contenido | skip\ to\ content |
        enviando\ formulario.* | formulario\ recibido.* | el\ servidor\ ha\ detectado.* |
        introducir\ (nombre|correo|mensaje).* | escriba\ su\ mensaje.* | enviar |
        men[uú] | toggle\ navigation | cargando.* | loading.* |
        aceptar\ cookies.* | usamos\ cookies.* | this\ site\ uses\ cookies.* |
        \d+ | x | ← | → | » | «
    )\s*$""", re.IGNORECASE | re.VERBOSE)
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"https?://\S+", "", md)
    out: list[str] = []
    seen: set[str] = set()
    for raw in md.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw).strip(" \t*>-|")
        if not line:
            if out and out[-1] != "":
                out.append("")
            continue
        if ui_noise.match(line):
            continue
        if len(re.sub(r"[^0-9A-Za-zÁÉÍÓÚÑáéíóúñ ]", "", line)) < 3:
            continue
        keyable = not line.startswith("# /")
        if keyable and line in seen:
            continue
        if keyable:
            seen.add(line)
        out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * q)]


def load_records(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    records: list[dict] = []
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("ok") and record.get("combined_markdown"):
                records.append(record)
    return records


def stratified(records: list[dict], size: int) -> list[dict]:
    ordered = sorted(records, key=lambda item: len(item.get("combined_markdown") or ""))
    if size <= 0 or size >= len(ordered):
        return ordered
    if size == 1:
        return [ordered[len(ordered) // 2]]
    indices = {round(i * (len(ordered) - 1) / (size - 1)) for i in range(size)}
    return [ordered[index] for index in sorted(indices)]


def mean_recall(meta: dict, field: str) -> float:
    recalls: list[float] = []
    source = meta.get("source_entities") or {}
    values = meta.get(field) or {}
    for key, originals in source.items():
        if originals:
            recalls.append(float(values.get(key, 0.0)))
    return statistics.mean(recalls) if recalls else 1.0


def category_recall(meta: dict) -> float:
    source = set(meta.get("source_categories") or [])
    if not source:
        return 1.0
    target = set(meta.get("context_categories") or [])
    return len(source & target) / len(source)


def run(records: list[dict], max_chars: int) -> dict:
    rows: list[dict] = []
    for record in records:
        source = record["combined_markdown"]
        legacy = legacy_clean_markdown(source) if len(source) <= 250_000 else None
        result = analyze_markdown(source, max_chars)
        meta = result["meta"]
        rows.append({
            "domain": record["domain"],
            "source_chars": len(source),
            "legacy_chars": len(legacy) if legacy is not None else None,
            "clean_chars": len(result["clean_text"]),
            "context_chars": len(result["segmentation_context"]),
            "legacy_noise": noise_line_count(legacy) if legacy is not None else None,
            "clean_noise": meta["noise_lines_clean"],
            "context_noise": meta["noise_lines_context"],
            "clean_entity_recall": mean_recall(meta, "entity_recall_clean"),
            "context_entity_recall": mean_recall(meta, "entity_recall_context"),
            "category_recall": category_recall(meta),
            "source_categories": meta.get("source_categories") or [],
            "context_categories": meta.get("context_categories") or [],
            "visual_assets": len(meta.get("visual_assets") or []),
            "evidence_links": len(meta.get("evidence_links") or []),
            "context": result["segmentation_context"],
        })

    clean_entity = [row["clean_entity_recall"] for row in rows]
    context_entity = [row["context_entity_recall"] for row in rows]
    category = [row["category_recall"] for row in rows]
    context_chars = [row["context_chars"] for row in rows]
    summary = {
        "sample": len(rows),
        "source_chars_median": round(statistics.median(row["source_chars"] for row in rows)),
        "legacy_chars_median": round(statistics.median(
            row["legacy_chars"] for row in rows if row["legacy_chars"] is not None
        )),
        "clean_chars_median": round(statistics.median(row["clean_chars"] for row in rows)),
        "context_chars_median": round(statistics.median(context_chars)),
        "context_chars_p90": round(percentile(context_chars, 0.90)),
        "context_chars_max": max(context_chars, default=0),
        "clean_entity_recall_mean": round(statistics.mean(clean_entity), 4),
        "clean_entity_recall_min": round(min(clean_entity), 4),
        "context_entity_recall_mean": round(statistics.mean(context_entity), 4),
        "category_recall_mean": round(statistics.mean(category), 4),
        "category_recall_min": round(min(category), 4),
        "legacy_noise_median": round(statistics.median(
            row["legacy_noise"] for row in rows if row["legacy_noise"] is not None
        ), 2),
        "clean_noise_median": round(statistics.median(row["clean_noise"] for row in rows), 2),
        "context_noise_median": round(statistics.median(row["context_noise"] for row in rows), 2),
        "sites_with_visual_evidence": sum(row["visual_assets"] > 0 for row in rows),
        "sites_with_evidence_links": sum(row["evidence_links"] > 0 for row in rows),
        "category_presence": dict(sorted(Counter(
            category for row in rows for category in row["context_categories"]
        ).items())),
    }
    summary["passes"] = {
        "clean_entity_recall_mean>=0.995": summary["clean_entity_recall_mean"] >= 0.995,
        "category_recall_mean>=0.98": summary["category_recall_mean"] >= 0.98,
        "context_p90<=budget": summary["context_chars_p90"] <= max_chars,
        "context_noise_median==0": summary["context_noise_median"] == 0,
    }
    return {"summary": summary, "rows": rows}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--sample", type=int, default=240)
    parser.add_argument("--max-context", type=int, default=10_000)
    parser.add_argument("--show-worst", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    selected = stratified(load_records(args.data), args.sample)
    result = run(selected, args.max_context)
    if args.json:
        printable = {"summary": result["summary"], "rows": [
            {key: value for key, value in row.items() if key != "context"}
            for row in result["rows"]
        ]}
        print(json.dumps(printable, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
        worst = sorted(result["rows"], key=lambda row: (
            row["category_recall"], row["clean_entity_recall"], -row["context_chars"]
        ))[:args.show_worst]
        for row in worst:
            print("\n===", row["domain"], {
                "category_recall": row["category_recall"],
                "entity_recall": row["clean_entity_recall"],
                "context_chars": row["context_chars"],
                "source_categories": row["source_categories"],
                "context_categories": row["context_categories"],
            })
            print(row["context"][:1200].replace("\n", " "))

    return 0 if all(result["summary"]["passes"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
