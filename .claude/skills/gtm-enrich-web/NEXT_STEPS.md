# NEXT STEPS — gtm-enrich-web (capa profunda de enrichment)

## Estado actual (2026-07-09)
- La capa de **descubrimiento de dominio** está resuelta y probada a escala (2,177 SOFOMes): Parallel `lite` + triage + verificación con subagentes. Ver `SKILL.md` y `LEARNINGS.md`.
- En `sofoms`: 1,310 con dominio (`discarded=false`), 867 sin dominio descartadas (`discarded=true`). Las usables para campaña salen con `where discarded = false`.

## Bake-off resuelto (2026-07-09) — motor: crawl4ai, ya empaquetado como skill `gtm-web-crawler`
Objetivo: una **capa de enrichment profundo** que, dado un dominio, extraiga el contenido del sitio para personalización de cold email (no solo "existe el dominio", sino qué hace, a quién, señales de dolor observable).

**La Capa A ya es un skill independiente y probado: `gtm-web-crawler`** (ver su `SKILL.md` y `BENCHMARK.md`). Corre con `bash .claude/skills/gtm-web-crawler/setup.sh` + `crawl.py --input <dominios.csv>`. Decisión del bake-off (8 dominios SOFOM reales):
- **Capa A (masiva, $0): `crawl4ai`** — 8/8, render JS (resuelve SPA), markdown limpio, deep-crawl priorizado que navega secciones solo, click nativo sin LLM por página.
- Descartados: trafilatura (0 chars en SPAs), Scrapy/Zyte (spider-por-layout / de pago). Ver `gtm-web-crawler/BENCHMARK.md`.
- **Capa B (agéntica, LLM, solo residuo): browser-use / Stagehand** para lo que la Capa A marca `ok:false`: Cloudflare y JS raro. Aquí "autoidentifica y pica botones". Mismo patrón que Parallel→subagentes. **Pendiente de integrar.**

### Pendiente para integrar como fase 2 del skill
1. Diseñar el crawl acotado por sitio: seed=home, seguir SOLO links de alto valor (about/nosotros, servicios/productos, aviso-de-privacidad/legal, contacto), tope ~6 páginas, dedupe www/no-www.
2. Definir el schema de salida (qué hace, a quién, geografía, señales de dolor observable, razón social del aviso) → tabla/columna en Supabase.
3. Triage: si trafilatura ya da texto rico y estático, usarlo; si el sitio es SPA/thin, ir a crawl4ai; si crawl4ai queda thin o hay challenge, escalar a Capa B.
4. Batch con reanudación idempotente por dominio (mismo patrón que la corrida de dominios).

## Notas heredadas de la corrida de dominios (aplican al scraping)
- El proxy del sandbox bloquea/`503` sitios grandes con curl: no confiar en fetch local como prueba, usar user-agent de navegador y/o el scraper elegido.
- Sitios SPA no rinden texto útil por HTML plano: hay que renderizar JS o leer los bundles (`assets/i18n/*.json`) — el scraper debe manejar esto.
- El aviso de privacidad / términos es donde vive la razón social y datos duros de la entidad.
