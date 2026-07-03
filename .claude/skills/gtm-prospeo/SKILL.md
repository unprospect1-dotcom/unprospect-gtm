---
name: gtm-prospeo
description: Listas y enriquecimiento con Prospeo. Modo BUSCAR - crea listas desde su base (200M+ contactos, 30+ filtros, límite 25K por búsqueda con crawl por estado). Modo ENRIQUECER - completa emails verificados, datos de persona/empresa (y mobile opcional) sobre un CSV existente, con estimación de créditos ANTES de gastar. Sigue el contrato universal de aprobación.
argument-hint: <workspace> <buscar [descripción] | enriquecer <archivo.csv>>
---

# GTM Prospeo — listas y enriquecimiento

## Antes de empezar
Además del contrato de memoria:
1. Lee `config/providers.yaml` (sección `prospeo` + `defaults` + `csv_schema`). **Nada hardcodeado: todo sale de la config.**
2. Lee del workspace: `BUYER-MAP.md` y `SEGMENTS.md` si existen.
3. Verifica que la env var indicada en `prospeo.env_key` exista. Si no, detente y dilo.

## Referencia técnica de la API
- Auth: header `X-KEY`. Base: `prospeo.base_url`. Rate limit 2–2.5 rps (usa `rate_limit_rps`), respuestas con `error: boolean`.
- `POST /search-person` — 25 resultados/página, máx 1,000 páginas = **25K por búsqueda**; para más, crawl por estado (`"California, United States #US"`) — patrón completo y lista de estados en `references/search-api.md`; taxonomía de industrias en `references/industries.md`. Filtros clave: `person_job_title` (include/exclude + `match_only_exact_job_titles`), `person_location_search`, `company_headcount_custom` (min/max), `company_industry`, `company_technology`, `company_funding` (fecha/monto/stage), `company_domain`, `person_contact_details.email: ["VERIFIED"]`, `person_duplicate_control` (ocultar ya exportados). 1 crédito por búsqueda que devuelve ≥1 resultado.
- `POST /enrich-person` — acepta: `linkedin_url` solo, `email` solo, `person_id` (del search), o `full_name`/`first+last` + identificador de empresa (name/website/linkedin). Flags: `only_verified_email`, `enrich_mobile`, `only_verified_mobile`. **Costos: 1 crédito por email verificado encontrado; mobile 10 créditos (email incluido gratis); NO_MATCH no cobra; re-enriquecer el mismo lead es GRATIS por 90 días.** Bulk hasta 50 por request.
- `POST /enrich-company` — firmográficos, funding, tech stack (bulk hasta 50).
- Search Suggestions endpoint — valida valores de filtros (ubicaciones, títulos, industrias) programáticamente; úsalo cuando dudes si un valor existe.
- Ejecuta llamadas con `scripts/prospeo.py` (subcomandos: `search`, `enrich`, `enrich-bulk`, `account`).

## Modo BUSCAR (crear lista)

1. **Inferir filtros** del buyer map/segmento; preguntar solo lo faltante. Valida títulos/ubicaciones dudosos con Search Suggestions antes de asumir.
2. **Confirmar con números**: 1 búsqueda → presenta filtros + `total_count`. Si >25K, propone el corte (por estado/geo/headcount) y confirma. **Espera aprobación.**
3. **Muestra de `defaults.sample_size`** en tabla → correcciones → traduce cada una a filtro → re-muestra. Dos rondas limpias = filtros bloqueados.
4. **Dedupe**: `person_duplicate_control` activado según config + cruce contra `outreach_log` de Supabase (los ya contactados <`recontact_after_days` días fuera).
5. **Crawl completo** paginando a `rate_limit_rps`, partiendo por estado si aplica.
6. **Artefacto**: CSV normalizado al `csv_schema` (source=`prospeo`) en `lists/<workspace>/<fecha>-<slug>.csv` + `-REPORT.md` (filtros JSON reproducibles, totales, créditos, estado **aprobado**).

## Modo ENRIQUECER (completar un CSV)

1. **Mapear columnas**: lee el CSV del usuario, infiere el mapeo a identificadores de Prospeo (¿hay linkedin_url? ¿nombre+dominio?) y muéstralo. Prioridad de identificador: `person_id` > `linkedin_url` > `email` > nombre+empresa (mejor match rate en ese orden).
2. **Estimar costo ANTES de gastar**: N leads × 1 crédito peor caso (+ ×10 si pidió mobile — solo si `enrich.enrich_mobile` o el usuario lo pide explícito). Reporta saldo actual (`account`) y **espera aprobación.**
3. **Piloto de 10**: enriquece 10, muestra match rate y calidad. Si el match rate es malo (<50%), diagnostica el identificador antes de quemar créditos en el resto.
4. **Bulk del resto** en lotes de `bulk_size`, a `rate_limit_rps`, con reintentos ante 429.
5. **Artefacto**: CSV enriquecido (columnas originales + las del `csv_schema` que se ganaron, `email_status` real) + reporte: match rate, créditos gastados vs estimados, leads sin match (separados para waterfall con AI Ark u otra fuente).

## Al terminar
- A `LEARNINGS.md` de este skill: qué identificadores dieron mejor match rate, títulos/valores de filtro que sí existen en su taxonomía, y costos reales vs estimados.
