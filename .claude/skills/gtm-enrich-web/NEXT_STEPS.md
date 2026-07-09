# NEXT STEPS — gtm-enrich-web (capa profunda de enrichment)

## Estado actual (2026-07-09)
- La capa de **descubrimiento de dominio** está resuelta y probada a escala (2,177 SOFOMes): Parallel `lite` + triage + verificación con subagentes. Ver `SKILL.md` y `LEARNINGS.md`.
- En `sofoms`: 1,310 con dominio (`discarded=false`), 867 sin dominio descartadas (`discarded=true`). Las usables para campaña salen con `where discarded = false`.

## Lo que sigue (otra sesión)
Objetivo: una **capa de enrichment profundo** que, dado un dominio, extraiga el contenido del sitio para personalización de cold email en campañas (no solo "existe el dominio", sino qué hace, a quién, señales de dolor observable, etc.).

Plan: **probar varios scrapers de páginas web — gratis y en repo** (sin quemar créditos de proveedores), compararlos y quedarnos con el mejor como motor de esta capa. Candidatos a evaluar:
- Scrapers open-source / self-host (crawl4ai, trafilatura, playwright puro, readability, etc.).
- Criterios: calidad de extracción de texto útil, manejo de SPAs/JS (varios sitios SOFOM son Angular — ver caso paya.com.mx), robustez ante bot-protection, costo (idealmente $0), y facilidad de correr en batch dentro del entorno.
- Entregable: el ganador integrado como la fase 2 del skill (dominio → contenido estructurado → señales de personalización), alimentando a `gtm-copy` / `gtm-campaign-ideation`.

## Notas heredadas de la corrida de dominios (aplican al scraping)
- El proxy del sandbox bloquea/`503` sitios grandes con curl: no confiar en fetch local como prueba, usar user-agent de navegador y/o el scraper elegido.
- Sitios SPA no rinden texto útil por HTML plano: hay que renderizar JS o leer los bundles (`assets/i18n/*.json`) — el scraper debe manejar esto.
- El aviso de privacidad / términos es donde vive la razón social y datos duros de la entidad.
