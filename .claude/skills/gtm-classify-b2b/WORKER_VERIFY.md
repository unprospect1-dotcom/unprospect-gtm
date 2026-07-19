# WORKER: verificador GTM (lote chico) — contrato para despachar como subagente CIEGO

En Claude Code despacha con el agente **`gtm-verifier`** (`.claude/agents/`, modelo más
fuerte); en Codex con el lane **`gtm_verifier`**. El verificador va CIEGO: da su juicio
desde cero, SIN ver etiquetas de la capa 1. Reemplaza NN por el número de lote.

SK=<ruta absoluta a>/.claude/skills/gtm-classify-b2b

Prompt de despacho (auto-contenido, por lote):

> Eres un VERIFICADOR independiente: etiqueta desde cero, sin ver ninguna respuesta previa.
> 1) Lee el rubro SK/PROMPT.md y aplícalo al pie de la letra. 2) Lee SK/batches/ctx_NN.txt
> (bloques `=== dominio ===`). 3) Etiqueta CADA dominio. 4) Escribe SK/batches/rver_NN.jsonl,
> UNA línea JSON por dominio, EXACTAMENTE estos 4 campos:
> {"domain","verify_label","verify_fit","confidence"}
> (verify_label = business_model según el rubro; verify_fit = outbound_fit). Sin citas,
> sin justificación. Reporta solo el conteo y la distribución.

Notas por harness:
- **Claude Code:** el subagente arranca con contexto limpio: la ceguera es estructural —
  solo cuida que el prompt de despacho NO incluya los rcls_*.
- **Codex (lane read-only):** el worker devuelve el JSONL y el ORQUESTADOR lo guarda en
  `batches/rver_NN.jsonl` sin editarlo.
