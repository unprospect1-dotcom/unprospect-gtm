# unprospect-gtm
Go to market OS for unprospect — un cold outbound machine con memoria y auto-aprendizaje.

**Empieza por [ARCHITECTURE.md](ARCHITECTURE.md)** — ahí está el mapa completo del sistema.

## Componentes
- `.claude/skills/gtm-*` — fuente canónica de los 16 skills activos para Claude Code, con su memoria y scripts.
- `.agents/skills/gtm-*` — adaptadores de descubrimiento para Codex; reutilizan los skills canónicos sin duplicarlos.
- `AGENTS.md` — reglas persistentes del repositorio para Codex.
- `workspaces/` — memoria por cliente (`unprospect` activo; `_template/` para clientes nuevos).
- `workspaces/unprospect/PROFILE.md` — fuente central de qué vende Unprospect, a quién y con qué evidencia.
- `scripts/job_signals.py` — flujo semanal Apify → evidencia → análisis → buyer → cola de copy.
- `supabase/migrations/` — capa de memoria consultable (outreach_log, angles, campaigns, replies, v_last_contact).
- `scripts/instantly_sync.py` — sincroniza envíos y replies de Instantly a Supabase.

## Uso con Claude Code y Codex

- Claude Code conserva las invocaciones `/gtm-*` y carga `.claude/skills/` como antes.
- Codex carga `AGENTS.md`, descubre los adaptadores en `.agents/skills/` e invoca los skills como `$gtm-*`.
- La lógica, scripts y `LEARNINGS.md` viven una sola vez en `.claude/skills/`.
- Consulta [docs/CODEX-COMPATIBILITY.md](docs/CODEX-COMPATIBILITY.md) para las equivalencias de herramientas y subagentes.
- Consulta [workspaces/unprospect/JOB-SIGNALS.md](workspaces/unprospect/JOB-SIGNALS.md) para el flujo LATAM de vacantes, sus dimensiones de fit y sus gates de gasto/envío.

## Local classification workflow

This repo now includes a simple local workflow to classify companies into logistics subsegments using the Supabase data already available in the workspace.

### Requirements
- Python 3.10+
- Environment variables:
  - SUPABASE_URL
  - SUPABASE_SERVICE_ROLE_KEY

### Run the classifier
```bash
python segment_companies.py
```

This will generate:
- segment_results.json
- segment_results.csv

### Run the subagent-style orchestrator
```bash
python subagent_workflow.py
```

This will generate:
- subagent_results.json

### Run tests
```bash
python scripts/check_agent_compat.py
python -m unittest discover -s tests -p "test_*.py"
python -m compileall -q .
```
