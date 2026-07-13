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
- **Catálogo completo de filtros, playbook y valores (46 categorías propias + 248 industrias LinkedIn, 24 deptos, seniorities, tamaños): `FILTERS.md` en este directorio. Consúltalo antes de armar cualquier query.**
- Auth: header `x-api-token`. Search en `/v3`, el resto en `/v2`. Rate limit self-serve: 60 req/min, 1,000 req/día. `GET /v2/data-fields` (GRATIS) trae los valores válidos de industrias/regiones/tecnologías.
- `POST /v3/search/companies` — body `{size, searchAfter, companiesFilters: {lookalikeDomains, includeDomains, excludeDomains, companySizes, industries, linkedinIndustries, keywords, departmentSizes, employeeCountLinkedin/Ocean, primaryLocations (códigos ISO alpha-2, ej. "mx"), ...}}` + `companyMatchingMode: precise|broad`. Paginación por cursor `searchAfter`. ⚠️ Los endpoints `/preview` (conteo) son enterprise-only — en self-serve el sondeo es `size` chico.
- `POST /v3/search/people` — `peopleFilters` (`jobTitleKeywords {anyOf/allOf/noneOf}`, `seniorities`, `departments`, `skills`, `changedPositionAfter/Before` "YYYY-MM-DD", `connections`, `followers`) + `companiesFilters` anidado (incl. lookalike). La respuesta trae `id` por persona — **guárdalo: es la llave del reveal**.
- `POST /v2/reveal/emails` — lista de person ids (+ `webhookUrl` opcional). **Async**: los emails llegan después; sin webhook, re-consultar. Solo cobra los verificados que encuentra.
- `POST /v2/warmup/companies` — valida seeds y dispara crawl de dominios que Ocean no tenga. **Gratis.**
- `POST /v2/enrich/company` — por dominio; `201` = aún no está en su DB, crawl disparado sin costo, reintentar en 2–5 min.
- `GET /v2/credits/balance` — saldo y límite diario restante.
- Ejecuta con `scripts/ocean.py` (subcomandos: `balance`, `warmup`, `companies`, `people`, `reveal-emails`, `enrich-company`).
- Paths verificados contra la API real (2026-07); los nombres exactos de campos del body pueden variar — ante 400, ajustar y registrar en LEARNINGS.

## Modo SEEDS — armar los 10 seeds perfectos sin salir de la terminal ($0)

Cuando NO hay clientes reales para usar de seed (o se quiere un lookalike por sub-nicho), los seeds se construyen con evidencia, no con memoria:

1. **Candidatos** — dos variantes según lo que exista:
   - **Con universo/crawls previos**: filtra el universo enumerado (`lists/<ws>/*.csv`) o Supabase por señales del nicho — keyword en `description`, bucket de ventas sano (1–50), tamaño medio. Si hay crawl previo, busca la keyword en `site_crawls.clean_text` (PostgREST `ilike`) — el sitio pesa más que la etiqueta.
   - **Cold start (nicho nuevo, cero datos)**: AI Ark `productAndServices` SMART con el servicio en español+inglés (ej. "instalación de paneles solares") + geo + employeeSize. SMART es angosto (decenas, no miles) — exactamente lo que quieres para seeds: jalar el pool completo cuesta centavos (0.1/empresa) y las descripciones vienen en el response. Sondea gratis el tamaño del nicho en GetLeads antes (`company_description` + count = $0).
2. **Evidencia**: para cada candidato saca ventanas de texto alrededor de la keyword desde `clean_text` (si un dominio no está crawleado, córrele `gtm-web-crawler` al momento).
3. **Evaluación LLM (Claude lee, no un regex)**: clasifica cada candidato — ¿el nicho es su NEGOCIO CENTRAL o solo lo menciona? Tira los adyacentes (en "transporte refrigerado": aseguradoras de carga, fabricantes de cajas refrigeradas, tiendas de electrodomésticos y aduanales genéricas TODOS mencionan "refrigerado"). Quédate con 10, mezclando sub-roles a propósito (ej. 7 carriers + 3 cadena de frío) según lo que deba capturar el lookalike.
4. **Validación**: `warmup` con los 10 (GRATIS) — todos deben salir en `successfulDomains`; los que no, se esperan 2–5 min (crawl de Ocean) o se sustituyen.
5. Los seeds aprobados van al REPORT y a LEARNINGS (sección "Seeds que funcionaron").

## Flujo (contrato universal: gratis → contar → muestra → aprobar → gastar)

### 1. Seeds y filtros — inferir, preguntar lo mínimo
Pide/toma los 3–10 dominios seed (clientes reales del workspace > logos aspiracionales — los seeds definen todo; sin clientes reales, usa el **modo SEEDS** de arriba). Del buyer map infiere jobTitles/seniorities; pregunta solo geografía/tamaño si no están en el ICP. Elige modo `precise` salvo que el usuario quiera ampliar (`broad`).

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
