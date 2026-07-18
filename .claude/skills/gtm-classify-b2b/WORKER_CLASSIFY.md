# WORKER: clasificador B2B (lote chico) — contrato para despachar como subagente

En Claude Code despacha con el agente **`gtm-classifier`** (`.claude/agents/`); en Codex con
el lane **`gtm_classifier`** (`.codex/agents/`). Ambos ya fijan modelo barato y reglas
duras; este archivo es el contrato de la TAREA (reemplaza NN por el número de lote).

SK=<ruta absoluta a>/.claude/skills/gtm-classify-b2b

Prompt de despacho (auto-contenido, por lote):

> Clasificas el MODELO DE NEGOCIO (b2b/b2c/mixed/unclear) de empresas mexicanas leyendo
> SOLO el clean_text. 1) Lee el rubro completo SK/PROMPT.md y aplícalo al pie de la letra
> (OJO regla 6: objeto social ≠ producto; NO abuses de "mixed"). 2) Lee SK/batches/ctx_NN.txt:
> un bloque `=== dominio ===` por empresa. 3) Clasifica CADA dominio. 4) Escribe
> SK/batches/rcls_NN.jsonl, UNA línea JSON por dominio:
> {"domain","label","confidence","primary_customer","evidence","reason"}
> evidence = cita textual literal corta del clean_text. Bloque vacío -> "unclear".
> Reporta solo el conteo y la distribución; el número de líneas debe == dominios del lote.

Notas por harness:
- **Claude Code:** el worker escribe el archivo él mismo (tiene Write). No necesita Bash ni
  red: el contexto ya está materializado por `make_context.py`.
- **Codex (lane read-only):** el worker devuelve el JSONL como salida final y el
  ORQUESTADOR lo guarda en `batches/rcls_NN.jsonl` tal cual, sin editarlo.
- No mostrar al worker ninguna etiqueta previa (capa 1 nueva = desde cero).
