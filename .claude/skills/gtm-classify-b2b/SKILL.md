---
name: gtm-classify-b2b
description: Clasifica el modelo de negocio (B2B / B2C / mixto) de empresas a partir del clean_text de su sitio (el que produce gtm-web-crawler). Capa 1 barata en masa con subagentes del harness (el modelo más barato disponible) + capa 2 de verificación independiente ciega con subagentes. Regla de oro - cuando clasificador y verificador coinciden se confía; cuando difieren se marca para revisión. Agnóstico al harness (funciona en Claude Code y en Codex). Usar después de gtm-web-crawler y antes de segmentar/priorizar por a-quién-le-vende.
---

# gtm-classify-b2b

Responde lo mínimo necesario por empresa, leyendo **solo el `clean_text`** de su sitio
(**schema mínimo v2, 2026-07-18**): ¿es B2B?, ¿es fit para outbound?, ¿qué vende? y ¿a
quién? Sin citas ni justificación — el control de calidad es la doble pasada ciega.

Salida (6 campos): `business_model` (b2b·b2c·mixed·noncommercial·unclear) ·
`outbound_fit` (high·medium·low·unclear) · `sells` (≤10 palabras) · `primary_customer`
(≤12 palabras) · `confidence`. Persistido en `b2b_classification` (load_supabase.py) o en
la cola `company_gtm_profiles` (load_profiles.py, corrida masiva de perfiles).

Paso natural **después de `gtm-web-crawler`** (que llena `site_crawls.clean_text`) y
**antes de `gtm-pain-segments`** (segmentar por a-quién-le-vende necesita saber si es B2B).

## Principio: solo subagentes, agnóstico al harness

El clasificador **NO** es un servicio externo (nada de Parallel/APIs de terceros). Es un
**loop de subagentes del propio harness**: en Claude Code se lanzan con la tool de agentes
(`model: haiku`, el más barato); en Codex, con su mecanismo de subagentes y el modelo más
barato equivalente. Todo lo demás son scripts de **stdlib + requests** (corren igual en
ambos). Así el skill es portable.

```
site_crawls.clean_text
        │
   make_context.py  ── UNA descarga masiva; escribe re_NN.txt + ctx_NN.txt
        │              (todo el clean_text del lote en UN archivo por lote)
   ┌────▼──────────────────────────────┐  CAPA 1 — clasificación (modelo más barato)
   │ 1 worker por lote                 │  cada uno: Read ctx_NN.txt -> clasifica con
   │  Claude Code: agente gtm-classifier│  PROMPT.md -> Write rcls_NN.jsonl
   │  Codex: lane gtm_classifier       │  (cero red, cero Bash por worker)
   └────┬──────────────────────────────┘
        │
   ┌────▼──────────────────────────────┐  CAPA 2 — verificación independiente CIEGA
   │ Claude Code: agente gtm-verifier  │  re-etiquetan SOLO el clean_text, sin ver la capa 1;
   │ Codex: lane gtm_verifier          │  escriben rver_NN.jsonl {domain,verify_label,...}
   │ sobre sample + low/mixed/unclear  │
   └────┬──────────────────────────────┘
        │
   load_supabase.py  ── upsert a b2b_classification, calcula verify_agree
```

**Regla de oro:** capa 1 y capa 2 **coinciden** → confiar (en la validación fue el 95%,
todos correctos en casos claros). **Difieren** → `verify_agree=false` = cola de revisión
(solo el ~5%, siempre empresas de frontera que sirven a varios segmentos).

## Prompt

Todo el criterio vive en **`PROMPT.md`** (etiquetas + 8 reglas de desempate). Única fuente de
verdad; lo usan por igual clasificadores y verificadores. Editarlo ahí, no duplicar.

Reglas que costó aprender (ver LEARNINGS.md):
- **Objeto social ≠ producto** — el texto legal no cuenta como producto.
- **No truncar** — alimentar ≥7–8K chars (el hero real suele venir tras el banner de cookies).
- **Nómina:** al trabajador → b2c; a la empresa como prestación → b2b.
- **Gobierno / software para financieras / "no atendemos personas físicas"** → b2b.

## Correr (mismo flujo en Claude Code y Codex)

Entorno: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_TOKEN` (DDL). Solo `requests`.

```bash
cd .claude/skills/gtm-classify-b2b
# 1) materializar lotes + contexto (UNA descarga; resumible: --pending excluye clasificados)
python3 make_context.py --pending --size 12 --outdir batches
# re-run de filas sesgadas (verified=false):  python3 make_context.py --unverified
```

> **Tamaño de lote (crítico):** usa lotes de **≤12-15 dominios** por subagente. En la
> validación, lotes de 40 hicieron que el modelo barato se sesgara a b2b (61% de acuerdo
> con la verificación vs 95% con lotes de 10; conteo b2b crudo 60% → real ~46%). Lotes
> chicos = más subagentes pero clasificación confiable.

**2) CAPA 1 — 1 worker barato por lote**, siguiendo `WORKER_CLASSIFY.md`:
- **Claude Code:** despacha el agente **`gtm-classifier`** (`.claude/agents/`, ya fija
  `model: haiku` + tools Read/Write). NUNCA un subagente general sin `model`: heredaría el
  modelo caro de la sesión. Lanza **oleadas de ~10 en paralelo** (varios Agent en un mismo
  mensaje; corren en background). Referencia medida: ~60s y ~29K tokens por lote de 12.
- **Codex (pocos lotes):** despacha el lane **`gtm_classifier`** (`.codex/agents/`,
  gpt-5.4-mini low). El lane es read-only: el worker devuelve el JSONL y el orquestador lo
  guarda.
- **Codex (corrida masiva):** usa `spawn_agents_on_csv` vía **`codex_csv.py`** — 1 fila =
  1 LOTE, estado en SQLite (resumable), 6 workers concurrentes:
  `python3 codex_csv.py make --layer classify` imprime el prompt exacto para pegar;
  al terminar, `codex_csv.py collect` valida y escribe los `rcls_NN.jsonl`.
- El worker solo hace: Read `ctx_NN.txt` → clasificar con `PROMPT.md` → `rcls_NN.jsonl`.
  Nada de fetch por worker: el contexto ya está en disco.

**3) CAPA 2 — verificación ciega**, siguiendo `WORKER_VERIFY.md`: agente **`gtm-verifier`**
(Claude Code, `model: sonnet`) o lane **`gtm_verifier`** (Codex), con el MISMO rubro, sin
mostrarles la capa 1, sobre un sample estratificado + TODOS los `confidence=low`/`mixed`/
`unclear`. Escriben `rver_NN.jsonl` con `{domain,verify_label,confidence,evidence}`.

Antes de persistir, los loaders validan enums y forma (valores permitidos de
business_model/outbound_fit/confidence, límites de palabras); una fila inválida detiene la
carga y el lote se re-despacha. Ya NO se piden citas: en la práctica los modelos baratos
las transcriben imperfecto (cosen fragmentos, normalizan espacios) y bloqueaban cargas sin
aportar control real — la garantía de calidad es el acuerdo entre dos pasadas ciegas.

```bash
# 4) cargar todo (glob de los rcls_/rver_ que escribieron los subagentes)
python3 load_supabase.py --classify "batches/rcls_*.jsonl" \
    --verify "batches/rver_*.jsonl" --model haiku
```

> **Costo/velocidad (por qué este flujo):** un subagente sin `model` explícito hereda el
> modelo de la sesión principal (Opus/Fable ≈ 5-10x Haiku) — ese fue el "carísimo". Y el
> flujo viejo (fetch + 12 lecturas por worker, despacho secuencial) era el "lento". Con
> agentes nombrados + contexto pre-materializado + oleadas paralelas, ~60 lotes de capa 1
> cuestan del orden de un puñado de dólares en Haiku, no decenas en el modelo grande.
> Ver `docs/SUBAGENTS.md` para la guía completa.

## Tabla `b2b_classification`

Una fila por dominio (migraciones `004_b2b_classification.sql` + `009_b2b_minimal_schema.sql`):
`domain, label, confidence, primary_customer, sells, outbound_fit, model, verified,
verify_label, verify_fit, verify_agree, classified_at` (evidence/reason quedan null desde v2).
Para la corrida masiva de perfiles, `load_profiles.py` persiste los mismos campos en
`company_gtm_profiles` (cola durable con `profile_status`).

Join: `b2b_classification.domain = site_crawls.domain = sofoms.domain`.

```sql
-- conteo B2B confiable (clasificador y verificador coinciden)
select label, count(*) from b2b_classification where verify_agree group by label;
-- cola de revisión (difieren)
select domain, label, verify_label from b2b_classification where verified and not verify_agree;
```

## Qué NO hace

- No usa servicios externos de clasificación (no Parallel, no APIs de terceros): **solo
  subagentes del harness**. Portable Claude Code ↔ Codex.
- No navega la web ni usa conocimiento de la marca: **solo** el `clean_text`. Si no alcanza
  (sitio caído, placeholder, solo aviso de fraude) → `unclear`, no adivina.
- No infiere sub-sector ni tamaño — eso es `gtm-pain-segments` sobre esta señal.
