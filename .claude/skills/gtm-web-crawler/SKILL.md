---
name: gtm-web-crawler
description: Crawler de sitios web self-host y gratis ($0) para enrichment profundo. Dado un dominio, renderiza JS (rinde SPAs/Angular), navega solo las secciones de alto valor (nosotros, servicios, aviso de privacidad) y devuelve markdown limpio como raw data para enrichment y segmentación (a quién le venden, si es B2B, casos de estudio, sectores). Motor crawl4ai (render + deep-crawl priorizado + click nativo). Corre en batch con concurrencia y reanudación. Lo que no rinde (Cloudflare/JS raro) se marca para escalar a capa agéntica.
argument-hint: <dominio | archivo.txt/csv> [--max-pages N] [--concurrency N] [--out dir]
---

# gtm-web-crawler — dominio → contenido del sitio para personalización

Este es **el** crawler de sitios del GTM OS. Lo usa `gtm-enrich-web` (fase 2) y
cualquier skill que necesite leer el contenido real de un sitio. Motor único y
probado: **crawl4ai** (ver `BENCHMARK.md` para por qué, no trafilatura ni Scrapy).

## Antes de empezar (2 comandos, no falla)
El entorno es efímero: cada sesión instala en ~1 min la primera vez. **Corre siempre esto primero:**

```bash
bash .claude/skills/gtm-web-crawler/setup.sh        # idempotente: ~54s la 1a vez, ~2s despues
source .claude/skills/gtm-web-crawler/.venv/bin/activate
```

En Codex Desktop/Windows usa `powershell -File .claude/skills/gtm-web-crawler/setup.ps1`;
crea `.venv-win` y reutiliza Chrome o Edge instalado.

`setup.sh` hace TODO lo necesario para el sandbox (no lo saltes):
1. instala `certutil` (libnss3-tools),
2. crea venv + instala `crawl4ai html2text` (NO descarga browser: usa el Chromium preinstalado),
3. importa el CA del proxy al NSS store de Chromium.

## Uso

```bash
# un dominio
python .claude/skills/gtm-web-crawler/crawl.py paya.com.mx

# varios / desde archivo (una linea por dominio, o CSV con columna 'domain')
python .claude/skills/gtm-web-crawler/crawl.py a55.com.mx factoring.mx
python .claude/skills/gtm-web-crawler/crawl.py --input dominios.csv --out salida

# tuning
python .../crawl.py --input doms.txt --max-pages 6 --depth 1 --concurrency 4
```

Flags: `--max-pages` (páginas por sitio, def 6), `--depth` (profundidad de crawl, def 1),
`--concurrency` (dominios en paralelo, def 4), `--out` (dir de salida, def `crawl_out`),
`--no-resume` (rehacer aunque exista), `--supabase` (persistir cada resultado a la tabla
`site_crawls` durante la corrida), `--domain-timeout` (límite total del deep crawl; si
vence intenta rescatar el home). **Por defecto reanuda**: si ya existe `<out>/<dominio>.json`, lo salta.

## Persistencia a Supabase (recomendado para batch grande)
```bash
# durante el crawl (upsert por dominio, sobrevive reciclado del contenedor):
python .../crawl.py --input dominios.csv --out crawl_out --supabase --concurrency 5

# o cargar despues un dir/artefacto ya crawleado:
python .../load_supabase.py --in crawl_out
python .../load_supabase.py --in data/sofoms_crawls.jsonl.gz
```
Escribe a la tabla **`site_crawls`** (una fila por dominio). La tabla se crea sola (DDL idempotente via Management
API con `SUPABASE_TOKEN`). El upsert usa `SUPABASE_SERVICE_ROLE_KEY` (PostgREST). Join
posterior: `sofoms.domain = site_crawls.domain`. Migración en `supabase/migrations/003_site_crawls.sql`.
Si la llave legacy global fue rotada, el loader obtiene la llave server-side vigente con
`SUPABASE_TOKEN`, sólo en memoria y sin imprimirla ni guardarla.

Para completar toda la base sin duplicar dominios:

```bash
python .../supabase_pipeline.py export-missing --out work/missing_domains.txt
python .../supabase_pipeline.py reclean --checkpoint work/reclean_v21.done
python .../crawl.py --input work/missing_domains.txt --out work/crawl_missing_v21 \
  --max-pages 2 --concurrency 4 --domain-timeout 45 --supabase
```

Los tres comandos son idempotentes/reanudables: `reclean` registra cada upsert confirmado
en el checkpoint y `crawl.py` salta cualquier JSON ya terminado. Usa exclusivamente las
variables globales `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` y `SUPABASE_TOKEN`.

Para una corrida larga en Windows, usa el supervisor. Divide los dominios sin solaparlos,
mantiene dos procesos de navegador aislados y reinicia sólo el que se caiga. El ejemplo
usa 2 workers x 3 pestañas (6 dominios simultáneos). Cada navegador procesa una sola ola
de 3 dominios y se cierra antes de acumular más memoria:

```powershell
python .claude/skills/gtm-web-crawler/crawl_supervisor.py `
  --input work/missing_domains.txt --out work/crawl_missing_v21 `
  --workers 2 --concurrency-per-worker 3 --max-pages 2 `
  --cycle-size 3 --domain-timeout 45 --supabase
```

Cada worker escribe logs separados bajo `<out>_supervisor_logs`. Si Chrome completo se
cierra, `crawl.py` sale con código reiniciable antes de guardar un falso fracaso; el
supervisor espera unos segundos, crea un Chrome nuevo y reanuda desde los JSON existentes.
Chrome mantiene JavaScript activo, pero no renderiza imágenes ni fuentes remotas. El HTML
conserva `src`, `alt` y enlaces, así que los logos y casos detectados siguen guardándose.
Además, cada worker cierra Chrome de forma ordenada cada 3 dominios. Este ciclo evita el
crecimiento de memoria observado con el reciclado interno de Crawl4AI 0.9.1 en Windows.

## Salida
Un `<out>/<dominio>.json` por sitio:
```json
{ "domain": "...", "ok": true, "n_pages": 4, "secs": 13.1,
  "pages": [{
    "url":"...", "path":"/nosotros", "chars":1234,
    "markdown":"...fit...", "raw_markdown":"...raw...",
    "visual_assets":[{"url":"...logo.svg", "alt":"Cliente X", "path":"/casos"}],
    "evidence_links":[{"url":".../caso-x", "text":"Caso Cliente X", "path":"/casos"}]
  }],
  "combined_markdown":"# /\n...fit completo...",
  "clean_text":"...contexto compacto para el LLM...",
  "clean_meta":{"version":"2.1", "context_chars":5432, "context_categories":["audience","b2b","identity","industry","offer","proof"]} }
```
- `pages[].raw_markdown` conserva el render original cuando difiere del fit. No se manda al LLM, pero permite recuperar un dato o volver a limpiar sin recrawlear.
- `pages[].markdown` es el `fit_markdown` de crawl4ai; `combined_markdown` concatena esa vista completa y recuperable para procesamiento posterior.
- `pages[].visual_assets` y `pages[].evidence_links` guardan logos, imágenes y enlaces candidatos a casos de éxito como metadata estructurada. El contexto sólo incluye hasta 5 pistas visuales; la lista completa queda en `pages`.
- `clean_text` es deliberadamente el **contexto operativo compacto** (máximo 10K chars) que consume el LLM. Prioriza identidad, industria, oferta, ICP/audiencia, señales B2B y prueba social; preserva cifras, porcentajes, moneda, certificaciones, emails y teléfonos.
- `clean_meta` deja visible la versión, tamaño y categorías presentes para auditar calidad sin releer todo el raw.
- El cleaner es determinista: no resume ni inventa. Quita navegación, formularios, cookies y duplicados, pero toda pérdida deliberada es recuperable desde `combined_markdown` o `pages[].raw_markdown`.
- La evaluación congelada y los umbrales de regresión están en `docs/CLEANER-EVAL.md`; se reproducen con `benchmark_cleaner.py`.
- Para futuras corridas `crawl.py` usa el filtro de densidad de crawl4ai (`fit_markdown`) y después el cleaner v2, así el contenido sale denso desde el inicio.
- `ok:false` con `reason: sin_contenido_util__escalar_a_capa_B_agentica` = challenge/bot-protection
  (Cloudflare) o sitio muerto → esos van a la **Capa B agéntica** (browser-use/Stagehand), no se inventan.

## Cómo navega las secciones (respuesta a "¿todo el sitio o solo el home?")
Deep-crawl priorizado: parte del home, puntúa los links internos por keywords de alto
valor (nosotros/servicios/productos/clientes/casos/industrias/contacto…) y visita primero esos, hasta
`--max-pages`, sin salir del dominio. No hay que listar URLs a mano.

Si el deep crawl agota `--domain-timeout`, hace un intento directo al home. Esto evita
falsos negativos en sitios útiles cuyo grafo de links se cuelga. En Windows activa ahorro
de memoria y recicla el navegador cada 40 páginas.

## Arquitectura de 2 capas (barato→caro, mismo patrón que Parallel→subagentes)
- **Capa A (este skill, $0, masivo):** crawl4ai resuelve ~la mayoría, incluyendo SPAs.
- **Capa B (agéntica, LLM, solo el residuo):** para challenges/JS raro que la Capa A marca
  `ok:false`. Ahí un agente (browser-use/Stagehand) **autoidentifica y pica botones**. Pendiente de integrar.

## Notas del sandbox (ya resueltas en `sandbox_browser.py`, no re-debuguear)
Todo scraper con navegador aquí necesita: Chromium preinstalado vía `executable_path`,
CA del proxy en el NSS store, y **`--ssl-version-max=tls1.2`** (si no, el middlebox de
inspección TLS resetea el ClientHello TLS1.3 → `ERR_CONNECTION_RESET` en todo sitio).
Detalle completo en `BENCHMARK.md` y en `gtm-enrich-web/LEARNINGS.md`.

## Para escalar (batch grande, ej. las ~1,310 SOFOMes con dominio)
```bash
python .../crawl.py --input sofoms_domains.csv --out crawl_sofoms --concurrency 4
```
Reanuda solo por archivo (idempotente): si la sesión se corta, re-corre el mismo comando.
Concurrencia 4 ≈ 4 sitios en paralelo; subir con cuidado (memoria del navegador).
