---
name: gtm-classify-b2b
description: Clasifica el modelo de negocio (B2B / B2C / mixto) de empresas a partir del clean_text de su sitio (el que produce gtm-web-crawler). Capa 1 barata en masa con subagentes del harness (el modelo más barato disponible) + capa 2 de verificación independiente ciega con subagentes. Regla de oro - cuando clasificador y verificador coinciden se confía; cuando difieren se marca para revisión. Agnóstico al harness (funciona en Claude Code y en Codex). Usar después de gtm-web-crawler y antes de segmentar/priorizar por a-quién-le-vende.
---

# gtm-classify-b2b

Responde una sola pregunta por empresa, leyendo **solo el `clean_text`** de su sitio:
**¿a quién le vende principalmente — empresas (B2B) o consumidores (B2C)?**

Salida: `b2b` · `b2c` · `mixed` · `unclear`, con `confidence`, `primary_customer`,
`evidence` (cita textual) y `reason`. Persistido en Supabase `b2b_classification`.

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
   make_batches.py  ── parte los dominios pendientes en batch_NN.txt
        │
   ┌────▼──────────────────────────────┐  CAPA 1 — clasificación (modelo más barato)
   │ 1 subagente por batch_NN.txt      │  cada uno: fetch_ct.py -> lee ct_*.txt ->
   │   (haiku / codex-mini / …)        │  clasifica con PROMPT.md -> escribe cls_NN.jsonl
   └────┬──────────────────────────────┘
        │
   ┌────▼──────────────────────────────┐  CAPA 2 — verificación independiente CIEGA
   │ subagentes (modelo distinto/más   │  re-etiquetan SOLO el clean_text, sin ver la capa 1;
   │  fuerte) sobre sample + los low/  │  escriben verify_NN.jsonl {domain,verify_label,...}
   │  mixed/unclear                    │
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
# 1) preparar lotes (resumible: excluye los ya clasificados)
python3 make_batches.py --size 12 --outdir batches   # lotes CHICOS: ver aviso abajo
```

> **Tamaño de lote (crítico):** usa lotes de **≤12-15 dominios** por subagente. En la
> validación, lotes de 40 hicieron que el modelo barato se sesgara a b2b (61% de acuerdo
> con la verificación vs 95% con lotes de 10; conteo b2b crudo 60% → real ~46%). Lotes
> chicos = más subagentes pero clasificación confiable.

**2) CAPA 1 — despachar un subagente por `batches/batch_NN.txt`**, con el modelo más barato
del harness. Instrucción para cada subagente (auto-contenida):
> Clasifica el modelo de negocio de empresas financieras mexicanas leyendo SOLO el clean_text.
> (a) corre `python3 <skill>/fetch_ct.py --batch <batch_NN.txt>`;
> (b) lee cada `ct_<dom>.txt` como UTF-8 explícito (en Windows PowerShell usa
> `Get-Content -Encoding UTF8`; no uses el default ANSI); (c) aplica el rubro de `PROMPT.md`;
> (d) escribe `<skill>/batches/cls_NN.jsonl`, una línea JSON por dominio con
> `{domain,label,confidence,primary_customer,evidence,reason}` (evidence = cita textual).

**3) CAPA 2 — verificación ciega:** despachar subagentes (modelo distinto, idealmente más
fuerte) con el MISMO rubro, sin mostrarles la capa 1, sobre un sample estratificado + TODOS
los `confidence=low`/`mixed`/`unclear`. Escriben `verify_NN.jsonl` con
`{domain,verify_label,confidence,evidence}`.

Antes de persistir, `load_supabase.py` vuelve a leer `site_crawls.clean_text` y exige que
cada evidencia no-`unclear` sea una cita literal. Si una capa normalizó acentos, espacios o
puntuación, la carga se detiene y el dominio se vuelve a ejecutar; no se guarda evidencia
aproximada.

```bash
# 4) cargar todo (glob de los cls_/verify_ que escribieron los subagentes)
python3 load_supabase.py --classify "batches/cls_*.jsonl" \
    --verify "batches/verify_*.jsonl" --model haiku
```

## Tabla `b2b_classification`

Una fila por dominio (migración `supabase/migrations/004_b2b_classification.sql`):
`domain, label, confidence, primary_customer, evidence, reason, model, verified,
verify_label, verify_agree, verify_note, classified_at`.

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
