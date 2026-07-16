# Next steps — handoff (2026-07-16)

## Lo que quedó hecho esta sesión
- **Segmentación ventas × marketing** sobre las 22,008 empresas (`list_companies`), 100% contado, gratis (GetLeads count).
  Reporte: `lists/unprospect/2026-07-16-ventas-marketing-conteo-REPORT.md`. Migraciones 006/007.
- **Rescate AI Ark** de 337 blind-spots de GetLeads (0-sin-señal + LinkedIn>50) → `aiark_sales_count`, max() aplicado. ~77 cr.
- **BUYER-MAP.md** con las 3 personas + banco de títulos ES/EN (con formas femeninas y jerga MX). Validado gratis.
- **Sizing de DMs** (gratis) sobre las 22k, gerente+ y comprehensivo (taxonomía ∪ banco de títulos):
  - Líderes comerciales: **29,052** · Dueños/Dirección (C-Team): **13,258** · Líderes de marketing: **6,795**.
  - Emaileables hoy (GetLeads VALID): 22,064 gerentes+ (3,617 líderes de ventas) — es el PISO, sube con Icypeas/AI Ark.
- **Hallazgo estructural** (con evidencia web): la pérdida de recall es de MX/LATAM, no de USA. En USA la base trae al
  decision-maker (pierde solo obreros); en MX pierde al dueño → por eso se necesita Apify/LinkedIn de recall. Ver replies previos.
- Crawl backfill de la cola B/C corriendo en background (reclaim-safe: cada chunk → Supabase, retoma solo).

## Paso siguiente → CODEX (otra sesión): separar B2B de B2C
- Usar `gtm-classify-b2b` sobre el `clean_text` de `site_crawls` (2 capas: clasificador barato + verificador ciego).
- Estado: **A-cut 90% crawleado**, listo. `site_crawls` ~41% del universo con contenido útil; `b2b_classification` solo 962 hechas.
- Empezar por el A-cut (universo de extracción); tirar los colados B2C (ej. consumer-lending en fintech, reclutamiento en hr-tech).

## Paso siguiente → CLAUDE (otra sesión): limpiar/trimear MÁS los crawler results, de forma confiable
Objetivo del usuario: **eliminar toda la basura de forma confiable** del texto crawleado.

Limpiador actual: `.claude/skills/gtm-web-crawler/clean_markdown.py`. Ya quita imágenes, URLs, dedup exacto de líneas,
y una lista **hardcodeada** de ruido UI (ES + algo EN). Límites a atacar:
1. **Ruido UI hardcodeado** → frágil. Pierde cookie banners en otros idiomas, chat/WhatsApp widgets, breadcrumbs,
   footers de dirección/teléfono, "© 2024", newsletter signups, redes sociales.
2. **Dedup solo exacto por línea** → los menús con variación por página sobreviven.
3. **No hay detección de boilerplate cross-page.** La palanca más CONFIABLE: marcar como plantilla las líneas/bloques
   que aparecen en ≥N páginas del MISMO dominio (frecuencia) y tirarlas — no depende de listas hardcodeadas.
4. **No hay extracción por densidad de contenido** (readability/jusText/trafilatura-style) para quedarse con "la carne".
   Nota: BENCHMARK.md eligió crawl4ai sobre trafilatura para el CRAWL, pero un pase de densidad POST-clean sí ayuda.
5. **Sesgo a español** en la lista de ruido.

Enfoque sugerido (barato → caro):
- (a) **Boilerplate cross-page por frecuencia** (gratis, determinista, confiable) — el mayor lift.
- (b) Densidad de contenido / readability pass sobre lo que queda.
- (c) Opcional: pase LLM con modelo barato para el residual, solo si (a)+(b) no bastan.
Medir con una muestra de dominios (comparar tokens antes/después y revisar que no se coma contenido útil de "nosotros/servicios").
