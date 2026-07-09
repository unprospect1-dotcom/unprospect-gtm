# NEXT STEPS — gtm-enrich-web (capa profunda de enrichment)

## Estado actual (2026-07-09)
- La capa de **descubrimiento de dominio** está resuelta y probada a escala (2,177 SOFOMes): Parallel `lite` + triage + verificación con subagentes. Ver `SKILL.md` y `LEARNINGS.md`.
- En `sofoms`: 1,310 con dominio (`discarded=false`), 867 sin dominio descartadas (`discarded=true`). Las usables para campaña salen con `where discarded = false`.

## Bake-off resuelto (2026-07-09) — motor elegido: crawl4ai
Objetivo: una **capa de enrichment profundo** que, dado un dominio, extraiga el contenido del sitio para personalización de cold email (no solo "existe el dominio", sino qué hace, a quién, señales de dolor observable).

Se corrió el bake-off sobre 8 dominios SOFOM reales (ver `deep_scrape/`). Decisión:
- **Capa A (masiva, $0): `crawl4ai`** — render JS (resuelve SPA), markdown limpio (alimenta directo a `gtm-copy`), descubre links internos y hace **deep-crawl acotado** que navega solo las secciones (nosotros/servicios/aviso de privacidad), y soporta **click nativo** (js_code / C4A-Script) sin LLM por página. 8/8 ok, ~7.6s/sitio.
- **Fast-path: `trafilatura`** para sitios obviamente estáticos (1s), pero NO puede ir solo: devuelve 0 chars en SPAs (paya, ion).
- **Capa B (agéntica, LLM, solo residuo): browser-use / Stagehand** para lo que la Capa A deja delgado: Cloudflare (aspiria.mx quedó en "Just a moment...") y JS raro. Aquí es donde "autoidentifica y pica botones". Mismo patrón que Parallel→subagentes.

### Pendiente para integrar como fase 2 del skill
1. Diseñar el crawl acotado por sitio: seed=home, seguir SOLO links de alto valor (about/nosotros, servicios/productos, aviso-de-privacidad/legal, contacto), tope ~6 páginas, dedupe www/no-www.
2. Definir el schema de salida (qué hace, a quién, geografía, señales de dolor observable, razón social del aviso) → tabla/columna en Supabase.
3. Triage: si trafilatura ya da texto rico y estático, usarlo; si el sitio es SPA/thin, ir a crawl4ai; si crawl4ai queda thin o hay challenge, escalar a Capa B.
4. Batch con reanudación idempotente por dominio (mismo patrón que la corrida de dominios).

## Notas heredadas de la corrida de dominios (aplican al scraping)
- El proxy del sandbox bloquea/`503` sitios grandes con curl: no confiar en fetch local como prueba, usar user-agent de navegador y/o el scraper elegido.
- Sitios SPA no rinden texto útil por HTML plano: hay que renderizar JS o leer los bundles (`assets/i18n/*.json`) — el scraper debe manejar esto.
- El aviso de privacidad / términos es donde vive la razón social y datos duros de la entidad.
