# WORKER: clasificador GTM mínimo (lote chico) — contrato para despachar como subagente

En Claude Code despacha con el agente **`gtm-classifier`** (`.claude/agents/`); en Codex con
el lane **`gtm_classifier`** o `spawn_agents_on_csv` vía `codex_csv.py`. Reemplaza NN por
el número de lote. Schema mínimo v2: SIN citas, SIN justificación.

SK=<ruta absoluta a>/.claude/skills/gtm-classify-b2b

Prompt de despacho (auto-contenido, por lote):

> Clasificas empresas mexicanas leyendo SOLO el clean_text. 1) Lee el rubro completo
> SK/PROMPT.md y aplícalo al pie de la letra (regla 6: objeto social ≠ producto; NO abuses
> de "mixed"). 2) Lee SK/batches/ctx_NN.txt: un bloque `=== dominio ===` por empresa.
> 3) Etiqueta CADA dominio. 4) Escribe SK/batches/rcls_NN.jsonl, UNA línea JSON por
> dominio, EXACTAMENTE estos 6 campos:
> {"domain","business_model","outbound_fit","sells","primary_customer","confidence"}
> sells ≤10 palabras, primary_customer ≤12. Bloque vacío -> business_model "unclear",
> fit "unclear", sells/customer null. Sin citas, sin justificación, sin campos extra.
> Reporta solo el conteo y la distribución; líneas del jsonl == dominios del lote.

Notas por harness:
- **Claude Code:** el worker escribe el archivo él mismo (tiene Write). Cero red, cero
  Bash: el contexto ya está materializado por `make_context.py`.
- **Codex (lane read-only):** el worker devuelve el JSONL como salida final y el
  ORQUESTADOR lo guarda tal cual en `batches/rcls_NN.jsonl`.
- No mostrar al worker ninguna etiqueta previa.
