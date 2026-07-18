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

## Por qué Codex hizo solo ~2,000 en 14 horas (post-mortem con docs oficiales)

Observado: ~2,000 dominios en ~840 min ≈ **143/hora** (lotes de 10 → ~4.2 min/lote). Las
causas, confirmadas contra la documentación de Codex (developers.openai.com/codex/subagents):

1. **`max_threads = 4`** en `.codex/config.toml`, cuando el tope duro de Codex es **6**
   (no configurable más arriba; issue openai/codex#11965). Dejamos 1/3 de la capacidad
   sin usar. Ya está en 6.
2. **La oleada se bloquea con el worker más lento**: "Codex waits until all requested
   results are available, then returns a consolidated response". Con 4 workers y uno lento
   (fetch de red, retry), la oleada entera espera.
3. **Cada worker hacía su propio fetch** (12 requests HTTP + 12 lecturas) — minutos de
   overhead por lote, igual que en Claude Code antes del fix.
4. **Nada se persistía**: los `rcls_*.jsonl` vivían en `batches/` (gitignoreado) del
   contenedor efímero. El contenedor se recicló y las ~14 horas de trabajo se evaporaron —
   Supabase solo tiene 504 perfiles aceptados / 200 clasificaciones verificadas.

Sobre "Codex lanzaba chats nuevos cada vez": cada subagente aparece como su propio thread
en la UI ("the app surfaces each subagent thread") — eso es normal y deseable (ceguera +
contexto limpio). El problema no eran los chats nuevos; eran los 4 puntos de arriba.

**La herramienta correcta en Codex para trabajo masivo es `spawn_agents_on_csv`**
(experimental): lee un CSV, lanza un worker por fila, guarda estado en SQLite (resumable)
y exporta resultados combinados a CSV con `status`/`last_error`/`result_json` por fila.
Usarla con **una fila = un LOTE** (columna con la ruta del `ctx_NN.txt`), no una fila por
empresa, y correr el export → `load_supabase.py` apenas termine cada corrida.

## Las 3 formas de correr el backlog, con números (19,409 perfiles pendientes)

| Opción | Throughput | Tiempo total | Costo | Riesgos |
|---|---|---|---|---|
| **A. Batch API de Anthropic** (script stdlib+requests; Haiku capa 1, Sonnet capa 2 sobre dudosos; 50% de descuento batch) | hasta 100K requests por batch, la mayoría termina <1h | **~1-3 horas** | **~$50 ± 10 dólares API** (capa 1 ~$25 + capa 2 ~$25) | Gasto API real; requiere aprobación |
| **B. Claude Code, lanes nuevos** (oleadas de 10 `gtm-profiler` haiku en paralelo, contexto pre-materializado) | ~2,000-3,000 dominios/h | **~7-10 horas** en varias sesiones | Incluido en el plan | Límites de ventana del plan; requiere babysitting; persistir cada ~5 oleadas |
| **C. Codex bien configurado** (`spawn_agents_on_csv`, 1 fila = 1 lote, max_threads 6) | ~1,000-1,300 dominios/h | **~15-20 horas** | Incluido en el plan Codex | Tope duro de 6 threads; mismo babysitting |

(La corrida vieja de Codex iba a 143/h — cualquiera de las tres es 7-20x más rápida.)

Los 762 de `b2b_classification` son chicos con cualquier opción: ~30 min en Claude Code
(oleadas `gtm-classifier`) o ~$3-5 y minutos por Batch API.

**Decisión tomada (2026-07-18): operamos con B y C** — todo dentro de los planes, sin
gasto API. B para oleadas desde Claude Code (validada en vivo: lote de 12 en ~60s y ~29K
tokens con `gtm-classifier`); C para corridas masivas desatendidas en Codex vía
`spawn_agents_on_csv` con **1 fila = 1 lote** (`gtm-classify-b2b/codex_csv.py` genera el
CSV + prompt y colecta los resultados; estado en SQLite = resumable). La opción A (Batch
API, ~$50 y 1-3h para 19.4K) queda documentada como alternativa si algún día urge.

## Reglas duras

- Ningún skill despacha workers masivos con el agente general del harness.
- Todo agente de `.claude/agents/` declara `model` y `tools` en el frontmatter (lo valida
  `scripts/check_agent_compat.py`).
- Nuevo lane = crearlo en AMBOS lados (`.claude/agents/` y `.codex/agents/`) en el mismo
  cambio, y registrar la equivalencia en `docs/CODEX-COMPATIBILITY.md`.
- El modelo grande se reserva para: adjudicar desacuerdos capa1↔capa2, sesiones de
  estrategia, y trabajo no-masivo.

## Pendiente operativo (el trabajo que motivó todo esto)

Estado real en Supabase al 2026-07-18:

- **`company_gtm_profiles`** (gtm-profile-company): 26,848 filas — **504 accepted**,
  6,572 not_profileable, y **19,772 pending, de las cuales 19,409 tienen crawl útil**.
  Ese es el backlog grande. La cola es durable: cualquier sesión nueva reanuda con
  `profile_status=pending` sin re-derivar nada.
- **`b2b_classification`** (gtm-classify-b2b, universo SOFOM): 962 filas — 200 verificadas,
  **762 sin verificar** esperando el re-run a lotes chicos
  (`make_context.py --unverified` → oleadas `gtm-classifier` → carga → `gtm-verifier`).
- `site_crawls`: 26,848 dominios crawleados, 21,499 con clean_text útil.

El estado de una corrida vive en Supabase (cola con status), NUNCA en el chat: así un chat
nuevo del orquestador cuesta una query de onboarding, no una re-derivación completa.
