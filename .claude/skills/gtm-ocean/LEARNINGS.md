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

- [2026-07-13] (señal) Transporte refrigerado MX — 10 seeds construidos con el modo SEEDS (universo AI Ark + clean_text del crawler + evaluación LLM), warmup OK los 10: carriers frioexpress.com, cabalo.mx, fwdlogistica.com, gpmetlogistics.com, transportesgmx.com, alsur.com.mx, corporativoenciso.com; cadena de frío/3PL frigorificosarcosa.com, dickalogistics.com, accessa.com.mx. Falsos positivos típicos del nicho detectados: aseguradoras de carga, fabricantes de carrocerías refrigeradas, retail de congelados, aduanales genéricas. (Pendiente: correr el lookalike y calificar la limpieza.)
- [2026-07-14] (confirmado) **Company search cuesta 0.2 créditos/resultado, no 1.0**: 1,120 lookalikes = 226 créditos (`creditsUsed` en el response lo confirma). El response trae `total` → una muestra de 10 (2 créditos) revela el universo completo — ese es el "conteo barato" en plan self-serve. La respuesta anida `companies[].company` + `relevance` (letras A/B/C, no números) — el score sirve para cortar la cola (C) antes de gastar en personas/emails.
- [2026-07-14] (confirmado) Lookalike precise con 10 seeds de instaladores solares MX: universo 1,120; calidad de muestra 10/10 solar/renovables; relevancia A=477, B=618, C=25. `employeeCountLinkedin 2-700` deja pasar autoreportados grandes con poco LinkedIn (por diseño — corte de alcanzabilidad).
- [2026-07-13] (señal) Instaladores solares MX — cold start completo en ~10 min y 3.2 créditos de AI Ark (probe + pool de 31 candidatos con descripción incluida): 10 seeds warmup-OK: galt.mx, ecocentro.mx, naturalproject.mx, energialibre.com.mx, energiasolarinc.com, marsamsolar.com, sunbank.mx, heliostecnologiasolar.net, pueblosolar.mx, greenvolt.com.mx. Descartados por evaluación: telecom conglomerate, 2 US, automatización, remodelaciones. OJO: el warmup puede fallar con "crawler failed" en dominios reales (etesla.mx, globalsolare.com) — tener 2-3 backups evaluados listos.

## Entradas

- [2026-07-13] (confirmado) `GET /v2/credits/balance` verificado en vivo con env var `OCEAN_API`: saldo {oneTime: 4368.8, recurrent: 300.0}, dailyLimitRateLeft 1000. Ocean queda reservado para lookalikes semánticos — para conteos y selección usar `gtm-getleads` (gratis) y para emails `gtm-lists-aiark`.
- [2026-07-13] (confirmado) `GET /v2/data-fields` es GRATIS y trae los valores válidos de industrias (46 categorías propias + 248 LinkedIn), regiones por país (regions.mx = 32 estados) y 6,451 tecnologías. Los endpoints `/v3/search/*/preview` (conteos) son ENTERPRISE-ONLY — en self-serve dan 402; sondear con size chico.
- [2026-07-13] (confirmado, de docs oficiales) Nombres reales de campos que difieren de lo asumido: `jobTitleKeywords` (no jobTitles), `changedPositionAfter` formato YYYY-MM-DD (no YYYY-MM), países en códigos ISO alpha-2 ("mx", no "Mexico"). Ocean también trae `departmentSizes` (empresas por tamaño de depto, ej. Sales from/to), `departmentGrowth` (3/6/12 meses, % o absoluto) y separa `employeeCountLinkedin` vs `employeeCountOcean` — mismo patrón LinkedIn-vs-real que AI Ark.

## Archivo

_(aprendizajes superados u obsoletos)_
