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

- [2026-07-14] (confirmado) `primaryLocations` es OBJETO, no lista: `{"primaryLocations": {"includeCountries": ["mx"]}}` (una lista da 422 model_attributes_type). `companyMatchingMode` va DENTRO de `companiesFilters`, no en el nivel superior del body (arriba da 422 extra_forbidden). Verificado en /v3/search/companies en vivo.
- [2026-07-14] (confirmado) El warmup puede reportar un dominio en `successfulDomains` y aun así el search devolverlo en `missingDomains` con "missing context vector" (hlsgroup.com.mx) — warmup OK ≠ vector listo. El search corre igual con los seeds restantes y lo avisa en `detail: "Missing some lookalikeDomains"`. Checar `missingDomains` en el PRIMER sondeo antes de confiar en la muestra.
- [2026-07-14] (señal) El crawl de dominios `triggered` puede tardar >7 min (3 dominios no terminaron en la sesión: solsersistem.net, pagopro.com.mx, grservicios.com.mx) — los "2-5 min" son optimistas. Tener backups YA calientes evaluados y sustituir en vez de esperar.

## Reglas de calidad del lookalike (medidas con crawl real)

- [2026-07-14] (confirmado, n=70 sitios crawleados) **El score `relevance` de Ocean ES la línea de corte: A ≈ 77-83% precisión, B ≈ 5-10%, C ≈ basura.** En instaladores solares MX (seeds puros): los A son instaladores/solar-core reales; los B derivan a "sector eléctrico/energía en general" (instaladores eléctricos, UVIEs, monitoreo, UPS — hasta Toshiba corporate); los C son colados y dominios parked. **Cortar en A por default.** El drift de B no es culpa de los seeds — es el radio semántico del modo precise; B puede reciclarse como universo de OTRO segmento (servicios eléctricos/eficiencia energética).
- [2026-07-14] (señal) Costo real por lead VERIFICADO (lookalike + crawl + evaluación): 226 cr / ~390 instaladores reales ≈ 0.6 créditos por empresa confirmada con sitio.
- [2026-07-14] (señal) Artefactos de crawl a vigilar al evaluar calidad: texto de error del proxy capturado como contenido (grupoenergiamexico.com) y sitios hackeados con spam (altihp.com con texto de casino) — no son colados del lookalike, son ruido del crawl.

## Seeds que funcionaron / no funcionaron

- [2026-07-14] (confirmado) **El centro semántico de los seeds pesa más que su número**: en BPO/nómina MX, 2 seeds tech-flavored (coltomex.com = data BPO, alliax.com = shared services con keywords de RPA/software) entre 8 arrastraron TODA la muestra a consultoría TI/procesos (0/10 de nómina). Re-muestra con solo los 6 seeds de nómina/administración de personal → 6-7/10 en el nicho. Para nichos "servicio + tecnología", NO mezclar sub-roles tech con sub-roles de servicio tradicional en el mismo lookalike.
- [2026-07-14] (señal) En MX, nómina/payroll y reclutamiento/staffing son UN MISMO espacio semántico (las empresas de "capital humano" hacen ambos) — un lookalike de maquila de nómina siempre traerá reclutadoras puras coladas; separarlas requiere la capa de crawl+clasificación, no filtros de Ocean.
- [2026-07-14] (confirmado) Servicios profesionales MX, 3 universos con seeds del modo SEEDS (pool AI Ark + evaluación LLM): TI (teknik.mx, gtec.com.mx, dotnet.com.mx, thincode.com, rd-its.com, cynthus.com.mx, matersys.mx, softnet.com.mx, itbs-grp.com, interax.com.mx) → total 3,068, muestra 10/10 limpia. Contable (skatt.com.mx, loftonsc.com, pkf.com.mx, bhrmx.com, delapazcostemalle.com.mx, bargallocardosoyasociados.com, nexiamexico.mx, hlbpuebla.com, ramirezsoto.com.mx, villegasyvillegas.com.mx) → total 1,503, muestra ~7-8/10 (drift a legal + un SaaS de facturación). BPO/nómina v2 (pronomina.com.mx, eog.mx, grupoono.lat, grupoestrategia.mx, intermex.mx, labormx.com) → total 3,503. Filtros: precise, primaryLocations {includeCountries:["mx"]}, employeeCountLinkedin 10-700.

- [2026-07-13] (señal) Transporte refrigerado MX — 10 seeds construidos con el modo SEEDS (universo AI Ark + clean_text del crawler + evaluación LLM), warmup OK los 10: carriers frioexpress.com, cabalo.mx, fwdlogistica.com, gpmetlogistics.com, transportesgmx.com, alsur.com.mx, corporativoenciso.com; cadena de frío/3PL frigorificosarcosa.com, dickalogistics.com, accessa.com.mx. Falsos positivos típicos del nicho detectados: aseguradoras de carga, fabricantes de carrocerías refrigeradas, retail de congelados, aduanales genéricas. (Pendiente: correr el lookalike y calificar la limpieza.)
- [2026-07-14] (confirmado) **Company search cuesta 0.2 créditos/resultado, no 1.0**: 1,120 lookalikes = 226 créditos (`creditsUsed` en el response lo confirma). El response trae `total` → una muestra de 10 (2 créditos) revela el universo completo — ese es el "conteo barato" en plan self-serve. La respuesta anida `companies[].company` + `relevance` (letras A/B/C, no números) — el score sirve para cortar la cola (C) antes de gastar en personas/emails.
- [2026-07-14] (confirmado) Lookalike precise con 10 seeds de instaladores solares MX: universo 1,120; calidad de muestra 10/10 solar/renovables; relevancia A=477, B=618, C=25. `employeeCountLinkedin 2-700` deja pasar autoreportados grandes con poco LinkedIn (por diseño — corte de alcanzabilidad).
- [2026-07-13] (señal) Instaladores solares MX — cold start completo en ~10 min y 3.2 créditos de AI Ark (probe + pool de 31 candidatos con descripción incluida): 10 seeds warmup-OK: galt.mx, ecocentro.mx, naturalproject.mx, energialibre.com.mx, energiasolarinc.com, marsamsolar.com, sunbank.mx, heliostecnologiasolar.net, pueblosolar.mx, greenvolt.com.mx. Descartados por evaluación: telecom conglomerate, 2 US, automatización, remodelaciones. OJO: el warmup puede fallar con "crawler failed" en dominios reales (etesla.mx, globalsolare.com) — tener 2-3 backups evaluados listos.

## Entradas

- [2026-07-14] (confirmado) Pull completo de 2 universos en una corrida (4,571 resultados, 914.2 cr) con driver de paginación con resume por página: un connection reset a mitad NO costó créditos (el estado con searchAfter se guarda tras cada página). El `call()` de ocean.py solo reintenta 429 — para batch largo envolver con retry de URLError/timeout con backoff. Ritmo: ~50 resultados (1 página) por ~2-3s + 1s sleep.
- [2026-07-14] (señal) Distribución de relevancia en servicios profesionales MX: TI A=35% (1,067/3,068), contable A=38% (574/1,503) — más bajo que solar (43%). El corte A como input del crawl ($0) mantiene el costo por empresa verificada en ~0.6-0.9 cr.
- [2026-07-14] (confirmado) gtm-web-crawler sobre el corte A: 1,641 dominios en ~1 hora con concurrencia 5, 87.7% ok, persistiendo a site_crawls con --supabase (sobrevivió un restart del contenedor sin pérdida).

- [2026-07-13] (confirmado) `GET /v2/credits/balance` verificado en vivo con env var `OCEAN_API`: saldo {oneTime: 4368.8, recurrent: 300.0}, dailyLimitRateLeft 1000. Ocean queda reservado para lookalikes semánticos — para conteos y selección usar `gtm-getleads` (gratis) y para emails `gtm-lists-aiark`.
- [2026-07-13] (confirmado) `GET /v2/data-fields` es GRATIS y trae los valores válidos de industrias (46 categorías propias + 248 LinkedIn), regiones por país (regions.mx = 32 estados) y 6,451 tecnologías. Los endpoints `/v3/search/*/preview` (conteos) son ENTERPRISE-ONLY — en self-serve dan 402; sondear con size chico.
- [2026-07-13] (confirmado, de docs oficiales) Nombres reales de campos que difieren de lo asumido: `jobTitleKeywords` (no jobTitles), `changedPositionAfter` formato YYYY-MM-DD (no YYYY-MM), países en códigos ISO alpha-2 ("mx", no "Mexico"). Ocean también trae `departmentSizes` (empresas por tamaño de depto, ej. Sales from/to), `departmentGrowth` (3/6/12 meses, % o absoluto) y separa `employeeCountLinkedin` vs `employeeCountOcean` — mismo patrón LinkedIn-vs-real que AI Ark.

## Archivo

_(aprendizajes superados u obsoletos)_
