#!/usr/bin/env python3
"""Valida que cada skill canónico de Claude tenga un adaptador descubrible por Codex."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CLAUDE_SKILLS = ROOT / ".claude" / "skills"
CODEX_SKILLS = ROOT / ".agents" / "skills"
CLAUDE_AGENTS = ROOT / ".claude" / "agents"
CODEX_AGENTS = ROOT / ".codex" / "agents"
COMPAT_DOC = "docs/CODEX-COMPATIBILITY.md"


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    try:
        block = text.split("---", 2)[1]
    except IndexError:
        return {}
    result: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def skill_names(root: Path) -> set[str]:
    if not root.is_dir():
        return set()
    return {path.parent.name for path in root.glob("*/SKILL.md")}


def validate() -> list[str]:
    errors: list[str] = []
    canonical = skill_names(CLAUDE_SKILLS)
    adapters = skill_names(CODEX_SKILLS)

    for name in sorted(canonical - adapters):
        errors.append(f"Falta adaptador Codex: .agents/skills/{name}/SKILL.md")
    for name in sorted(adapters - canonical):
        errors.append(f"Adaptador sin skill canónico: .agents/skills/{name}/SKILL.md")

    for name in sorted(canonical & adapters):
        canonical_path = CLAUDE_SKILLS / name / "SKILL.md"
        adapter_path = CODEX_SKILLS / name / "SKILL.md"
        canonical_meta = frontmatter(canonical_path)
        adapter_meta = frontmatter(adapter_path)

        if canonical_meta.get("name") != name:
            errors.append(f"name canónico inválido en {canonical_path.relative_to(ROOT)}")
        if not canonical_meta.get("description"):
            errors.append(f"description canónica faltante en {canonical_path.relative_to(ROOT)}")
        if adapter_meta.get("name") != name:
            errors.append(f"name de adaptador inválido en {adapter_path.relative_to(ROOT)}")
        if not adapter_meta.get("description"):
            errors.append(f"description de adaptador faltante en {adapter_path.relative_to(ROOT)}")

        adapter_text = adapter_path.read_text(encoding="utf-8")
        canonical_ref = f".claude/skills/{name}/SKILL.md"
        if canonical_ref not in adapter_text:
            errors.append(f"{adapter_path.relative_to(ROOT)} no referencia {canonical_ref}")
        if COMPAT_DOC not in adapter_text:
            errors.append(f"{adapter_path.relative_to(ROOT)} no referencia {COMPAT_DOC}")

    errors.extend(validate_agent_lanes())
    return errors


def validate_agent_lanes() -> list[str]:
    """Lanes de subagentes: cada agente Claude declara model/tools; cada lado tiene lanes."""
    errors: list[str] = []
    claude_lanes = sorted(CLAUDE_AGENTS.glob("*.md")) if CLAUDE_AGENTS.is_dir() else []
    codex_lanes = sorted(CODEX_AGENTS.glob("*.toml")) if CODEX_AGENTS.is_dir() else []

    if not claude_lanes:
        errors.append("Faltan lanes Claude en .claude/agents/ (los workers heredarían el modelo caro)")
    if not codex_lanes:
        errors.append("Faltan lanes Codex en .codex/agents/")

    for path in claude_lanes:
        meta = frontmatter(path)
        rel = path.relative_to(ROOT)
        if not meta.get("name"):
            errors.append(f"{rel}: falta name en frontmatter")
        if not meta.get("description"):
            errors.append(f"{rel}: falta description en frontmatter")
        if not meta.get("model"):
            errors.append(f"{rel}: falta model en frontmatter (sin model el subagente hereda el modelo de la sesión)")
        if not meta.get("tools"):
            errors.append(f"{rel}: falta tools en frontmatter (heredaría todas las tools)")

    for path in codex_lanes:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        if "model" not in text:
            errors.append(f"{rel}: falta model en el lane Codex")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("Compatibilidad de agentes: ERROR")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Compatibilidad de agentes: OK ({len(skill_names(CLAUDE_SKILLS))} skills)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
