# Raw crawl data — SOFOMes (corrida 2026-07-09)

Salida del crawl de `gtm-web-crawler` sobre los **1,295 dominios únicos usables** de
`sofoms` (`discarded=false, domain not null`). Es el corpus histórico **raw** para
enrichment y segmentación (a quién le venden, si es B2B, casos de estudio, sectores).
El loader actual deriva `site_crawls.clean_text` con el cleaner v2 al importar este
archivo; no hay que modificar ni volver a generar el respaldo.

**También está en Supabase** (fuente canónica para el paso posterior): tabla `site_crawls`,
1,295 filas, join por `sofoms.domain = site_crawls.domain`. Este `.gz` es el respaldo/portable.

## Archivos
- `sofoms_crawls.jsonl.gz` (7.5 MB) — una línea JSON por dominio:
  `{domain, ok, n_pages, secs, reason, pages:[{path,url}], combined_markdown}`.
  `combined_markdown` es el contenido concatenado de las secciones navegadas.
- `manifest.csv` — índice liviano (`domain, ok, n_pages, chars, reason`) para escanear
  sin descomprimir.

## Leer
```python
import gzip, json
for line in gzip.open("sofoms_crawls.jsonl.gz", "rt", encoding="utf-8"):
    rec = json.loads(line)
    if rec["ok"]:
        raw = rec["combined_markdown"]
        # Al cargarlo, load_supabase.py crea clean_text (<=10K chars) para el LLM.
```

La corrida histórica no incluye `pages[].raw_markdown`, `visual_assets` ni
`evidence_links`; esos campos se generan en crawls nuevos. Al importar el histórico,
`load_supabase.py` extrae los links e imágenes que sí están en `combined_markdown` y los
adjunta a la página correspondiente dentro del JSONB `pages`, sin alterar el `.gz`.

## Resumen de la corrida
- 963 ok (74%) con contenido · 332 (25%) `sin_contenido_util`.
- 3.2 páginas/sitio promedio · 33.8 MB de markdown total.
- Los 332 fallidos (muestra): ~52% muertos/inalcanzables (`000`), ~30% vivos pero thin
  (SPA/JS → **Capa B agéntica**), resto redirects/403/503.
- Regenerar: `python crawl.py --input <dominios> --out crawl_out` (reanuda solo).
