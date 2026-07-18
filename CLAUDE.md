@AGENTS.md

## Claude Code

- Claude Code NO lee `AGENTS.md` por sí solo; este archivo lo importa. Las reglas de arriba
  aplican completas. No dupliques contenido aquí — edita `AGENTS.md`.
- **Subagentes masivos (clasificación, perfilado, verificación): usa SIEMPRE los agentes
  definidos en `.claude/agents/`** (`gtm-classifier`, `gtm-verifier`, `gtm-profiler`).
  Tienen el modelo barato fijado en su frontmatter. NUNCA despaches trabajo masivo con el
  agente general (`general-purpose`) ni sin `model` explícito: un subagente sin modelo
  hereda el modelo de la sesión principal (Opus/Fable = 5-10x el costo de Haiku).
- Despacha los workers en oleadas paralelas (varios `Agent` en un mismo mensaje, corren en
  background), no uno por uno.
- Verificación local: `python3 scripts/check_agent_compat.py`,
  `python3 -m unittest discover -s tests -p "test_*.py"`, `python3 -m compileall -q .`.
