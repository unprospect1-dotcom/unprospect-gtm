# Learnings de este skill

> Memoria transferible entre clientes. El skill la lee al empezar y agrega entradas al terminar.
> Formato de entrada: `- [YYYY-MM-DD] (confianza: hipótesis|señal|confirmado) aprendizaje — evidencia`
> /gtm-retro consolida y poda este archivo.

## Reglas (confirmadas, aplicar siempre)

_(vacío — se promueven aquí los aprendizajes confirmados en ≥2 campañas)_

## Endpoints/campos corregidos en corridas reales

_(paths verificados por sondeo 2026-07: /v3/search/companies, /v3/search/people,
/v2/reveal/emails, /v2/reveal/phones, /v2/warmup/companies, /v2/enrich/company,
/v2/credits/balance — registrar aquí nombres de campos del body al confirmarlos)_

## Seeds que funcionaron / no funcionaron

_(por workspace: qué dominios seed dieron lookalikes limpios)_

## Entradas

- [2026-07-13] (confirmado) `GET /v2/credits/balance` verificado en vivo con env var `OCEAN_API`: saldo {oneTime: 4368.8, recurrent: 300.0}, dailyLimitRateLeft 1000. Ocean queda reservado para lookalikes semánticos — para conteos y selección usar `gtm-getleads` (gratis) y para emails `gtm-lists-aiark`.
- [2026-07-13] (confirmado) `GET /v2/data-fields` es GRATIS y trae los valores válidos de industrias (46 categorías propias + 248 LinkedIn), regiones por país (regions.mx = 32 estados) y 6,451 tecnologías. Los endpoints `/v3/search/*/preview` (conteos) son ENTERPRISE-ONLY — en self-serve dan 402; sondear con size chico.
- [2026-07-13] (confirmado, de docs oficiales) Nombres reales de campos que difieren de lo asumido: `jobTitleKeywords` (no jobTitles), `changedPositionAfter` formato YYYY-MM-DD (no YYYY-MM), países en códigos ISO alpha-2 ("mx", no "Mexico"). Ocean también trae `departmentSizes` (empresas por tamaño de depto, ej. Sales from/to), `departmentGrowth` (3/6/12 meses, % o absoluto) y separa `employeeCountLinkedin` vs `employeeCountOcean` — mismo patrón LinkedIn-vs-real que AI Ark.

## Archivo

_(aprendizajes superados u obsoletos)_
