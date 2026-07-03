---
name: gtm-ocean
description: Listas lookalike con Ocean.io - dale 3-10 dominios de clientes reales y encuentra empresas similares por semantica de producto/servicio, luego las personas correctas dentro y sus emails verificados. Con presupuesto de creditos DURO (cada resultado de busqueda y cada email cuestan 1 credito). Sigue el contrato universal - warmup gratis de seeds, sondeo de conteo, muestra aprobada, y solo entonces gastar.
argument-hint: <workspace> <dominios seed separados por coma | descripción>
---

# GTM Ocean — lookalikes con presupuesto

## Antes de empezar (contrato de memoria)
1. Lee `LEARNINGS.md` en este directorio y `config/providers.yaml` (sección `ocean` + `defaults` + `csv_schema`). **Nada hardcodeado.**
2. Lee del workspace: `BUYER-MAP.md` (títulos/seniority), `SEGMENTS.md`, `PROFILE.md` si existen.
3. Verifica que la env var de `ocean.env_key` exista; si no, detente y dilo.
4. **Consulta el saldo (`balance`) SIEMPRE al arrancar.** Reporta: saldo, `dailyLimitRateLeft`, y cuánto permite gastar esta corrida según `credit_budget` (max_per_run, sin bajar de reserve).

## Economía de créditos (la regla de este skill)
- **1 crédito por resultado devuelto** en search (companies y people) — pedir 500 resultados = 500 créditos, los quieras o no.
- **1 crédito por email verificado** en reveal.
- Lista de N personas con email ≈ **hasta 2×N créditos**. Con el saldo actual, di siempre el costo estimado ANTES de cada llamada que gaste.
- Gratis: `warmup` de seeds y el `enrich-company` que responde 201 (dominio en crawl).
- Por eso el flujo es: gratis → 1 crédito → muestra pequeña → aprobación → gasto real.

## Referencia técnica
- Auth: header `x-api-token`. Search en `/v3`, el resto en `/v2`. Rate limit self-serve: 60 req/min, 1,000 req/día.
- `POST /v3/search/companies` — body `{size, searchAfter, companiesFilters: {lookalikeDomains: [...], includeDomains, excludeDomains, ...}}`. Lookalike con modo `precise` (similitud semántica de producto/servicio, default) o `broad` (misma industria). Máx `lookalike.max_domains` seeds. Paginación por cursor `searchAfter`.
- `POST /v3/search/people` — `peopleFilters` (jobTitles, seniorities, departments, `changedPositionAfter` "YYYY-MM") + filtros de empresa (incl. lookalike). La respuesta trae `id` por persona — **guárdalo: es la llave del reveal**. Campos: name, jobTitle, seniorities, departments, domain, country, linkedinUrl.
- `POST /v2/reveal/emails` — lista de person ids (+ `webhookUrl` opcional). **Async**: los emails llegan después; sin webhook, re-consultar. Solo cobra los verificados que encuentra.
- `POST /v2/warmup/companies` — valida seeds y dispara crawl de dominios que Ocean no tenga. **Gratis.**
- `POST /v2/enrich/company` — por dominio; `201` = aún no está en su DB, crawl disparado sin costo, reintentar en 2–5 min.
- `GET /v2/credits/balance` — saldo y límite diario restante.
- Ejecuta con `scripts/ocean.py` (subcomandos: `balance`, `warmup`, `companies`, `people`, `reveal-emails`, `enrich-company`).
- Paths verificados contra la API real (2026-07); los nombres exactos de campos del body pueden variar — ante 400, ajustar y registrar en LEARNINGS.

## Flujo (contrato universal: gratis → contar → muestra → aprobar → gastar)

### 1. Seeds y filtros — inferir, preguntar lo mínimo
Pide/toma los 3–10 dominios seed (clientes reales del workspace > logos aspiracionales — los seeds definen todo). Del buyer map infiere jobTitles/seniorities; pregunta solo geografía/tamaño si no están en el ICP. Elige modo `precise` salvo que el usuario quiera ampliar (`broad`).

### 2. Warmup (gratis)
Corre `warmup` con los seeds. Si algún seed no está en la DB de Ocean, espera el crawl (2–5 min) antes de buscar — un seed vacío degrada todo el lookalike.

### 3. Sondeo de conteo (1 crédito)
Búsqueda con `size: 1` (`search.count_probe_size`) para ver el total disponible. Presenta: total, costo estimado de la lista que el usuario quiere (N búsqueda + ~N reveal), saldo restante proyectado. **Espera aprobación del presupuesto.** Si excede `credit_budget.max_per_run` o dejaría el saldo bajo `reserve`, proponlo en tandas.

### 4. Muestra de aprobación (~25 créditos)
Trae `defaults.sample_size` empresas/personas y muéstralas en tabla. Correcciones → ajusta filtros (excludeDomains para falsos positivos, jobTitles más precisos) → re-muestra. **Dos rondas limpias = filtros bloqueados.** Cada re-muestra cuesta — dilo y cuenta el gasto acumulado.

### 5. Dedupe antes del gasto grande
Cruza los dominios de la muestra/conteo contra `outreach_log` y `companies` de Supabase (workspace actual). Los ya contactados van a `excludeDomains` — no pagues por resultados que vas a tirar.

### 6. Búsqueda completa + reveal
Pagina con `searchAfter` hasta el N aprobado. Junta los person ids y corre `reveal-emails` por lote. Es async: espera/re-consulta y reporta cuántos emails verificados llegaron vs cobrados.

### 7. Artefacto
Normaliza al `csv_schema` (source=`ocean`, source_id=person id) → `lists/<workspace>/<YYYY-MM-DD>-<slug>.csv` + `-REPORT.md`: seeds usados, modo, filtros JSON reproducibles, totales, créditos gastados vs estimados, saldo final, estado **aprobado**. Los seeds y el resultado también van a `SEGMENTS.md` si definieron un segmento nuevo.

## Al terminar (contrato de memoria)
- Registra en `LEARNINGS.md`: qué seeds produjeron lookalikes limpios vs ruidosos, precise vs broad por caso, nombres de campos del body corregidos en corridas reales, y costos reales vs estimados.
