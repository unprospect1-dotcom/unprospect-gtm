@AGENTS.md

## Claude Code

- Claude Code NO lee `AGENTS.md` por sí solo; este archivo lo importa. Las reglas de arriba
  aplican completas. No dupliques contenido aquí — edita `AGENTS.md`.
- **POLÍTICA MASIVOS (2026-07-19, decisión de Camilo): el trabajo masivo (clasificación,
  perfilado, verificación en volumen) va por API directa con Batch** (OpenAI hoy;
  `gtm-classify-b2b/openai_batch.py drain`). NO despaches oleadas de subagentes del
  harness para masivos: chocan con los límites de sesión del plan (pasó dos veces).
- Los agentes de `.claude/agents/` (`gtm-classifier`, `gtm-verifier`, `gtm-profiler`)
  se usan SOLO para calibración: golden evals, muestras chicas, adjudicación puntual.
  Si los usas, siempre por lane nombrado (nunca `general-purpose` sin `model`: hereda el
  modelo caro de la sesión) y en oleadas paralelas.
- Verificación local: `python3 scripts/check_agent_compat.py`,
  `python3 -m unittest discover -s tests -p "test_*.py"`, `python3 -m compileall -q .`.
