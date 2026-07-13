---
name: gtm-getleads
description: Listas, conteos y enrichment con GetLeads.io (~370M contactos, 515 industrias). Su superpoder - conteos y catálogos de filtros GRATIS (0 créditos) - lo vuelve la capa de sizing/descubrimiento de TODO el stack. Modos - contar (sizing gratis, tamaño de deptos, descubrimiento de títulos), lista (receta DM-unión), decision-makers, fallback (empresas sin DM), enriquecer (CSV con emails/LinkedIn), señales (funding/M&A). Sigue el contrato universal - contar gratis, muestra aprobada, y solo entonces gastar.
argument-hint: <workspace> <modo: contar|lista|dms|fallback|enriquecer|señales> [segmento o dominios o CSV]
---

# GTM GetLeads — contar gratis antes de gastar en cualquier lado

## Antes de empezar (contrato de memoria)
1. Lee `LEARNINGS.md` en este directorio y `config/providers.yaml` (sección `getleads` + `defaults` + `csv_schema`). **Nada hardcodeado.**
2. Lee del workspace: `BUYER-MAP.md` (personas/títulos), `SEGMENTS.md`, `PROFILE.md` si existen.
3. Verifica que la env var de `getleads.env_key` exista; si no, detente y dilo.
4. Consulta el saldo (`scripts/getleads.py credits` — gratis) y repórtalo con el presupuesto de la corrida según `credit_budget`.

## Economía de créditos (la regla de este skill)
- **GRATIS (0 créditos): `count`, `filter-values`, `health`.** Sin límite práctico salvo el rate (100 req/min).
- **1 crédito por registro devuelto** en search/decision-makers/colleagues y **por acierto** en enrich (no-match no cobra).
- Export asíncrono (CSV en S3): cobra por fila exportada; en plan free se capa a `min(saldo, disponible)`.
- **Regla de oro del stack: todo lo que se pueda contar, se cuenta gratis aquí ANTES de gastar en GetLeads, AI Ark u Ocean.**
- Cobertura de email VALID fuera de USA es débil (México ~6%) — para emails de listas MX el cierre es AI Ark (encuentra y verifica en tiempo real, no cobra si no hay email). Este skill produce la selección; `gtm-lists-aiark` produce los emails.

## Referencia técnica
- Auth: `Authorization: Bearer` (o `X-API-Key`) con la key `glb_live_…`. Base: `getleads.base_url`. Rate: 100 req/min global, 429 al excederse.
- Docs completas (no públicas — extraídas de su SPA): `reference/getleads-api.md`. Endpoints clave:
  - `POST /contacts/search/count` — **GRATIS**. Mismo body que search. Devuelve `total_matching` + `creditsRemaining`.
  - `POST /contacts/search` — filtros AND entre campos, **OR dentro de cada array** (verificado). `limit` (máx 50k), `offset`, `max_per_company` (1–50), `columns`, y `where_sql` (predicado SQL crudo para campos sin filtro dedicado, ej. `MONTHLY_GOOGLE_ADSPEND_ORG > 0`).
  - Filtros: `domains`, `industries` (515 LinkedIn), `headquarters_countries`, `job_titles` (substring, OR), `job_functions` (22 deptos), `seniority` (C-Team/VP/Director/Manager/Staff/Other), `personas`, `company_size_min/max`, `employees_min/max`, `revenue`, `technologies`, `email_status` (VALID/CATCH_ALL/INVALID), `require_phone`, y `exclude_*` (domains, industries, job_titles, countries).
  - `GET /contacts/filter-values?field=…` — **GRATIS**. Enums exactos (industries, job_functions, personas, seniority, countries…). Nunca inventes el string de una industria: consúltalo.
  - `POST /contacts/search/export` — asíncrono; `export_id` → poll `GET /contacts/search/export/{id}` → `export_url` (CSV S3, expira 24h). `max_rows` opcional.
  - `POST /contacts/lookup/decision-makers` — `{domain, limit, offset}`. Preset C-Team/VP/Director/Head. **No ve títulos en español** — para MX úsalo solo como capa, no como única fuente.
  - `POST /contacts/lookup/colleagues` — `{email_domain, limit_per_item, offset}` — todas las personas de un dominio.
  - `POST /enrich/from-email|from-linkedin|from-person` — batch de 100; 1 crédito por acierto.
  - `GET /funding/signals`, `GET /acquisitions/signals` — señales de funding/M&A parseadas de feeds en vivo.
- Ejecuta con `scripts/getleads.py` (subcomandos: `health`, `credits`, `count`, `search`, `export`, `export-status`, `decision-makers`, `colleagues`, `enrich-email`, `enrich-linkedin`, `enrich-person`, `filter-values`, `signals`).

## LA RECETA DM-UNIÓN (el flujo repetible de toda lista)

El objetivo: no dejar pasar a ningún decision-maker, con precisión medida, pagando solo una vez. Ni la taxonomía sola ni un diccionario de títulos solo bastan (en MX la taxonomía pierde hasta 42% de dirección; el diccionario pierde otro tanto). **Siempre las dos capas, unidas, medidas gratis.**

### Paso 0 — Segmento base (input del usuario)
Industria(s) + geografía + tamaño de empresa. Consulta `filter-values` para los strings exactos. Pregunta solo lo que no puedas inferir del workspace: ¿HQ o ubicación de la persona? ¿qué personas del buyer map? ¿exclusiones?

### Paso 1 — Conteo base (gratis)
`count` del segmento sin filtro de rol. Este número ancla todo lo demás.

### Paso 2 — Capa A: taxonomía (gratis)
Por persona del buyer map: `count` con `job_functions` / `seniority` / `personas` (ej. ventas = `job_functions: ["Sales & Business Development"]`; dirección = `seniority: ["C-Team"]`).

### Paso 3 — Capa B: diccionario de títulos ES+EN (gratis)
Genera ~50–150 keywords candidatas por persona (español + inglés, **con y sin acento** — el match es sensible a acentos, "Tráfico" ≠ "Trafico"). Incluye jerga del sector (transporte MX: "Tráfico", "Encargado", "Administrador", "Gerente de Sucursal"). Sonda cada candidata con `count` (gratis, 100/min); sobreviven las >0. El diccionario final va a LEARNINGS como activo reutilizable por sector.

### Paso 4 — Aritmética de unión (gratis)
Por persona: `count(A)`, `count(B)`, `count(A AND B)` → **A∪B = A + B − A∩B**. Presenta la tabla: cuánto agrega cada capa. Detecta falsos positivos previsibles y mételos a `exclude_job_titles` (mínimo: "Asistente", "Assistant") y re-cuenta.

### Paso 5 — Muestra de aprobación (~25 créditos)
`search` con `limit` = `defaults.sample_size`. El usuario corrige → cada corrección se vuelve filtro/exclude → re-conteo gratis → re-muestra solo si cambió mucho. **Dos rondas limpias = filtros bloqueados.**

### Paso 6 — Dedupe antes de gastar (gratis)
Cruza contra Supabase (`outreach_log`, `companies` del workspace) → dominios ya contactados a `exclude_domains`. Reporta cuántos se excluyeron.

### Paso 7 — Export pagando la unión, no la suma
Por persona: corrida A (taxonomía) y corrida B (diccionario). El traslape A∩B saldría pagado doble — evítalo excluyendo la capa A del segundo export vía `where_sql` cuando el traslape sea grande (>15%), o acéptalo si es chico. `max_per_company: 1-2` por corrida para estructura "1 dueño + 1 ventas + 1 marketing por empresa". Dedupe local por id/email al unir.

### Paso 8 — Cierre de emails
Filtra `email_status: VALID` primero (gratis contar cuántos hay). Los DMs sin email verificado NO se tiran: van a `gtm-lists-aiark` (export single: 1 crédito, solo cobra si encuentra email BounceBan-verificado).

## Modo FALLBACK — empresas donde no apareció ningún DM

Escalera por dominio, de gratis a caro. Precios reales por empresa:

1. **(Gratis)** `count` del dominio con el diccionario DM completo. Si >0 pero el export general no lo trajo, es tema de `max_per_company` — repesca dirigida.
2. **(Gratis)** Escalera de keywords genéricas por dominio: "Gerente", "Director", "Jefe", "Coordinador", "Encargado", "Supervisor" — encuentra QUÉ hay sin pagar. Si una capa da 1–5, trae solo esa capa (1 crédito por persona traída).
3. **(0.5 créditos/persona — AI Ark)** Si nada matchea: lista TODAS las personas del dominio vía AI Ark people search (la mitad del precio de GetLeads que cobra 1/persona vía `colleagues`). Claude clasifica los títulos y elige el mejor 1–2.
4. **(1 crédito — AI Ark)** Export single del elegido para email verificado; no cobra si no encuentra.

Costo típico por empresa rescatada: **2–5 créditos** (escalera) hasta **~0.5×N + 1** si hubo que listar a todos (N = personas en la base; cuéntalo GRATIS antes en GetLeads con `count domains:[X]` para saber el precio exacto de antemano).

## Otros modos
- **contar**: sizing puro — mercado por filtro, tamaño de un depto por empresa (`domains:[X], job_functions:[Y]` → gratis por dominio, 100 empresas/min), señal Google Ads vía `where_sql`. Entregable: CSV de conteos + lectura.
- **dms**: `decision-makers` por dominio (1 crédito/registro) — rápido para pocos dominios en mercados EN; en MX complementa con el diccionario ES.
- **enriquecer**: CSV con emails o LinkedIn URLs → `enrich-*` por lotes de 100. Estimación de costo = filas (solo cobra aciertos). Reporta % de acierto.
- **señales**: funding/M&A con filtros; 1 crédito/registro.

## Artefacto
Normaliza al `csv_schema` (source=`getleads`) → `lists/<workspace>/<YYYY-MM-DD>-<slug>.csv` + `-REPORT.md`: filtros JSON reproducibles por corrida, tabla de conteos por capa (A, B, unión), traslapes, excludes aplicados, créditos gastados vs estimados, saldo final, y qué se mandó a AI Ark para cierre de emails. Estado **aprobado**.

## Al terminar (contrato de memoria)
- Registra en `LEARNINGS.md`: diccionario de títulos que sobrevivió (por sector/geo), falsos positivos nuevos, % cobertura de email VALID observado por geo, costos reales vs estimados, y campos de `where_sql` que funcionaron.
