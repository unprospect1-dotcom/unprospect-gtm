# unprospect-gtm
Go to market OS for unprospect — un cold outbound machine con memoria y auto-aprendizaje.

**Empieza por [ARCHITECTURE.md](ARCHITECTURE.md)** — ahí está el mapa completo del sistema.

## Componentes
- `.claude/skills/gtm-*` — los 9 skills del ciclo (onboard → segmentos → offers → ángulos → copy → experimentos → replies → retro), cada uno con su `LEARNINGS.md` de auto-aprendizaje.
- `workspaces/` — memoria por cliente (`unprospect` activo; `_template/` para clientes nuevos).
- `supabase/migrations/` — capa de memoria consultable (outreach_log, angles, campaigns, replies, v_last_contact).
- `scripts/instantly_sync.py` — sincroniza envíos y replies de Instantly a Supabase.

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
python -m unittest discover -s tests -p "test_*.py"
```
