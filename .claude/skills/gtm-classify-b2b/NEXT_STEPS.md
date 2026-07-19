# NEXT STEPS — terminar la clasificación B2B per-dominio (Claude Code o Codex)

## Estado actual (en Supabase `b2b_classification`, 962 filas)

- **200 filas VERIFICADAS y confiables** (`verified=true`): 40 golden + 160 muestra masiva,
  ambas con segundo modelo (sonnet) + adjudicación. Estas NO se tocan.
- **762 filas SIN verificar** (`verified=false`): tienen etiqueta de la primera corrida
  masiva que se hizo con **lotes de 40**, la cual **se sesga a b2b** (ver LEARNINGS.md:
  acuerdo con verificación 61%). Sirven como estimado poblacional pero **no son confiables
  per-dominio**.
- **Conteo B2B**: crudo 60% → **corregido ~46%** (b2b 46% / b2c 28% / mixed 15% / unclear 10%).
  El corregido es el bueno a nivel población.

## Objetivo pendiente

Dar etiqueta per-dominio confiable a las **762 sin verificar**, con el diseño de dos capas a
**lotes de 10** (el fix de tamaño de lote). Se intentó pero el re-run se perdió por refresh
del contenedor (los artefactos viven en `batches/`, gitignoreado).

## ⚠️ REGLA OPERATIVA CRÍTICA

**Carga cada oleada a Supabase apenas termina.** Los archivos `batches/*.jsonl` son
gitignoreados y se PIERDEN si el contenedor se refresca. No acumules 20 lotes en disco: en
cuanto tengas ~5-10 `rcls_NN.jsonl`, córrelos con `load_supabase.py`. Supabase es la única
fuente de verdad durable.

## Receta (misma en Claude Code y Codex; usa los lanes de subagentes del repo)

```bash
SK=.claude/skills/gtm-classify-b2b
cd $SK

# 1) materializar lotes + contexto de los 762 no verificados (UNA sola descarga):
python3 make_context.py --unverified --size 12
#    escribe batches/re_NNNN.txt + batches/ctx_NNNN.txt (numeración de 4 dígitos;
#    clean_text del lote en UN archivo). Schema mínimo v2: salida de 6 campos, SIN citas.

# 2) CAPA 1: 1 worker por lote, sigue WORKER_CLASSIFY.md.
#    Claude Code -> agente gtm-classifier (.claude/agents/, model: haiku YA fijado).
#    Codex       -> lane gtm_classifier (.codex/agents/).
#    Dispara en OLEADAS PARALELAS de ~10 (en Claude Code: varios Agent en un mismo mensaje).
#    Cada worker: Read ctx_NN.txt -> Write batches/rcls_NN.jsonl. Sin fetch, sin Bash.
#    NUNCA despachar sin agente nombrado: sin `model` el subagente hereda el modelo caro.

# 3) CARGA capa 1 apenas tengas lotes hechos (repite seguido):
python3 load_supabase.py --classify "batches/rcls_*.jsonl" --model haiku-b12
#   (esto pone verified=false; es capa 1 mejorada. La verificación viene en el paso 4.)

# 4) CAPA 2 verificación CIEGA: 1 worker por lote, sigue WORKER_VERIFY.md.
#    Claude Code -> agente gtm-verifier (model: sonnet). Codex -> lane gtm_verifier.
#    Sobre sample estratificado + TODOS los low/mixed/unclear. Escribe batches/rver_NN.jsonl.

# 5) CARGA con verificación (calcula verify_agree):
python3 load_supabase.py --classify "batches/rcls_*.jsonl" --verify "batches/rver_*.jsonl" --model haiku-b12

# 6) ADJUDICAR desacuerdos (donde capa1 != capa2): léelos tú (el orquestador) y decide.
#    Son ~10-30% y casi siempre frontera b2b/mixed/b2c.
```

```sql
-- desacuerdos a adjudicar
select domain, label, verify_label, confidence from b2b_classification
where verified and not verify_agree;
-- conteo B2B confiable final
select label, count(*) from b2b_classification where verify_agree group by label;
```

## Consejo de escala
762 dominios a lotes de 12 = ~64 workers de capa 1 (+ capa 2 sobre sample y dudosos).
Con el agente `gtm-classifier` (haiku) y contexto pre-materializado, cada worker cuesta
centavos y una oleada de 10 corre en paralelo; ya no debería topar límites de sesión como
cuando los workers heredaban el modelo caro. Aun así, carga a Supabase cada ~5 oleadas
(regla operativa de arriba). La alternativa "1-a-1" (un subagente por dominio) da máxima
precisión pero son ~1500 spawns — no vale el overhead.
