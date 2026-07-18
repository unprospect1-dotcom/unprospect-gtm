# Subagentes bien hechos — guía del repo (Claude Code ↔ Codex)

Fecha: 2026-07-18. Origen: repaso tras el run de `gtm-profile-company` / `gtm-classify-b2b`
que salió carísimo y lento en Claude Code. Este doc explica POR QUÉ pasó y fija el patrón
correcto para cualquier skill que use workers masivos.

## Diagnóstico del run caro (qué estábamos haciendo mal)

| # | Error | Efecto | Fix |
|---|---|---|---|
| 1 | Despachar workers sin `model` explícito en Claude Code | Un subagente sin modelo **hereda el modelo de la sesión** (docs oficiales: omitido = `inherit`). Sesión en Opus/Fable → cada worker cuesta 5-10x Haiku ($5-10 vs $1 por Mtok de input). Éste fue el grueso del "carísimo". | Agentes de proyecto en `.claude/agents/` con `model` fijado |
| 2 | Workers como subagente general (todas las tools) | Cada spawn carga todos los schemas de tools (MCP incluidos) en su contexto | `tools: Read, Write` en el frontmatter |
| 3 | Cada worker hacía su propio fetch (12 requests HTTP) + 12 lecturas de archivo | Decenas de turnos y minutos de red POR WORKER, multiplicado por ~64 lotes. Éste fue el "lento" | El orquestador materializa `ctx_NN.txt` (todo el lote en UN archivo) con `make_context.py`; el worker queda en Read → Write |
| 4 | Despacho secuencial (un worker, esperar, otro) | Tiempo total = suma de todos los lotes | Oleadas de ~10 `Agent` en un mismo mensaje; corren en paralelo/background |
| 5 | No existía `CLAUDE.md` | Claude Code **no lee `AGENTS.md`**; las sesiones arrancaban sin reglas del repo | `CLAUDE.md` raíz con `@AGENTS.md` |
| 6 | Orquestador en el modelo grande para trabajo de lotes | El modelo caro también pagaba la orquestación (leer reportes, contar líneas) | Corridas masivas: sesión `/model haiku`/`sonnet` (equivalente al modo `gpt-5.4-mini` de Codex) |

Codex NO tenía este problema porque ya existían lanes en `.codex/agents/*.toml` con
`gpt-5.4-mini` + `low` + sandbox read-only. El repo tenía la mitad Codex bien y la mitad
Claude sin construir.

## El patrón correcto (ambos harnesses)

1. **Materializar contexto primero.** El orquestador baja TODO lo que los workers van a
   leer en una sola pasada (paginada/bulk) y lo deja en disco, un archivo por lote.
   Los workers no tocan la red.
2. **Despachar por lane nombrado.**
   - Claude Code: `Agent(subagent_type: "gtm-classifier" | "gtm-verifier" | "gtm-profiler")`.
     El frontmatter ya fija `model`, `tools` y `maxTurns` — nadie tiene que acordarse.
   - Codex: lanes `gtm_classifier`, `gtm_verifier`, `gtm_profile_a/b/c`.
3. **Oleadas paralelas de ~10.** En Claude Code, varios `Agent` en un mismo mensaje corren
   en paralelo (background por default). En Codex, `max_threads = 4` en `.codex/config.toml`.
4. **Worker mínimo:** Read (1 archivo de contexto + el rubro) → clasificar → Write (1
   archivo de salida). El mensaje final del worker es solo el conteo, nunca el JSON.
5. **Capa 2 ciega estructural.** En ambos harnesses cada worker arranca con contexto
   limpio: la ceguera se rompe únicamente si el prompt de despacho incluye la capa 1.
   No incluirla, y listo.
6. **Persistir cada ~5 oleadas** a Supabase (`batches/` es gitignoreado y el contenedor
   es efímero).

## Números de referencia (para oler cuándo algo está mal)

Precios API (jul 2026): Haiku 4.5 $1/$5 por Mtok · Sonnet $3/$15 · Opus 4.8 $5/$25 ·
Fable 5 $10/$50.

- Lote de 12 dominios × 8K chars ≈ 26-30K tokens de input por worker. En Haiku ≈ **$0.04
  por lote**; capa 1 completa de ~760 dominios (64 lotes) ≈ **$3-5**.
- El mismo run con workers heredando Opus/Fable ≈ **10x**, más el overhead de tools/turnos
  del flujo viejo → decenas de dólares y sesiones topadas. Si un run masivo "se siente"
  así, revisa el despacho ANTES de tocar el prompt.
- La capa 2 (sonnet, solo sample + dudosos ≈ 40% del volumen) agrega ~$3-4.

## Reglas duras

- Ningún skill despacha workers masivos con el agente general del harness.
- Todo agente de `.claude/agents/` declara `model` y `tools` en el frontmatter (lo valida
  `scripts/check_agent_compat.py`).
- Nuevo lane = crearlo en AMBOS lados (`.claude/agents/` y `.codex/agents/`) en el mismo
  cambio, y registrar la equivalencia en `docs/CODEX-COMPATIBILITY.md`.
- El modelo grande se reserva para: adjudicar desacuerdos capa1↔capa2, sesiones de
  estrategia, y trabajo no-masivo.

## Pendiente operativo (el trabajo que motivó todo esto)

Los **762 dominios `verified=false`** de `b2b_classification` siguen esperando el re-run a
lotes chicos. Receta actualizada en `.claude/skills/gtm-classify-b2b/NEXT_STEPS.md`:
`make_context.py --unverified` → oleadas de `gtm-classifier` → carga → `gtm-verifier`
sobre sample+dudosos → carga con `verify_agree` → adjudicar desacuerdos.
