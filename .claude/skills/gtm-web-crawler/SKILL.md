---
name: gtm-web-crawler
description: Crawler de sitios web self-host y gratis ($0) para enrichment profundo. Usa la capa HTTP de Crawl4AI primero y abre Chromium sólo para SPAs/JS o señales faltantes. Navega únicamente secciones de alto valor y devuelve markdown recuperable más clean_text compacto para saber qué venden, a quién, si son B2B y qué prueba social tienen. Corre en batch con concurrencia, reintentos acotados y reanudación.
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
python .../crawl.py --input doms.txt --max-pages 2 --concurrency 4 --http-concurrency 12
```

Flags: `--max-pages` (páginas por sitio, def 2), `--depth` (compatibilidad; la cascada rápida usa un salto),
`--concurrency` (pestañas Chromium en paralelo, def 4), `--http-concurrency` (requests HTTP en paralelo, def 12),
`--max-attempts` (intentos totales de un fallo, def 2), `--out` (dir de salida, def `crawl_out`),
`--no-resume` (rehacer aunque exista), `--supabase` (persistir cada resultado a la tabla
`site_crawls` durante la corrida), `--domain-timeout` (límite total del deep crawl; si
vence conserva el mejor resultado parcial). **Por defecto reanuda**: salta los `ok:true`; un
fallo viejo recibe un único intento de rescate y luego queda detenido en `crawl_attempts:2`.

## Persistencia a Supabase (recomendado para batch grande)
```bash
# durante el crawl (upsert por dominio, sobrevive reciclado del contenedor):
python .../crawl.py --input dominios.csv --out crawl_out --supabase \
  --http-concurrency 12 --concurrency 3

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
  --max-pages 2 --concurrency 3 --http-concurrency 12 --domain-timeout 45 --supabase
```

Los tres comandos son idempotentes/reanudables: `reclean` registra cada upsert confirmado
en el checkpoint y `crawl.py` salta cualquier JSON ya terminado. Usa exclusivamente las
variables globales `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` y `SUPABASE_TOKEN`.

Para una corrida larga en Windows, usa el supervisor. Divide los dominios sin solaparlos,
mantiene dos procesos aislados y reinicia sólo el que se caiga. El ejemplo usa 2 workers,
12 requests HTTP por worker y hasta 3 pestañas por navegador. Cada proceso atiende 100
dominios antes de reciclarse; como la mayoría sale por HTTP, Chrome procesa una fracción:

```powershell
python .claude/skills/gtm-web-crawler/crawl_supervisor.py `
  --input work/missing_domains.txt --out work/crawl_missing_v21 `
  --workers 2 --http-concurrency-per-worker 12 --concurrency-per-worker 3 `
  --max-pages 2 --cycle-size 100 --domain-timeout 45 --supabase
```

Cada worker escribe logs separados bajo `<out>_supervisor_logs`. Si Chrome completo se
cierra, `crawl.py` sale con código reiniciable antes de guardar un falso fracaso; el
supervisor espera unos segundos, crea un Chrome nuevo y reanuda desde los JSON existentes.
Chrome mantiene JavaScript activo en los fallbacks, pero no renderiza imágenes, CSS ni fuentes remotas. El HTML
conserva `src`, `alt` y enlaces, así que los logos y casos detectados siguen guardándose.
Además, cada worker cierra Chrome de forma ordenada al terminar su ciclo. Esto evita el
crecimiento de memoria sin pagar un arranque nuevo cada tres dominios. Crawl4AI está fijado
en 0.9.2, que además corrige la fuga de tareas/páginas del dispatcher en streaming.

## Salida
Un `<out>/<dominio>.json` por sitio:
```json
{ "domain": "...", "ok": true, "n_pages": 2, "secs": 3.1,
  "crawl_engine":"crawl4ai-0.9.2", "crawl_mode":"http_sufficient", "crawl_attempts":1,
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
Cascada priorizada: Crawl4AI pide el home por HTTP sin navegador. Si ya encuentra oferta,
audiencia/B2B y contexto de identidad/industria/prueba, termina. Si faltan señales, puntúa
los links internos (casos/clientes primero; luego servicios/productos, industrias y nosotros)
y abre sólo los mejores hasta `--max-pages`. Si el HTML es una shell de SPA o sigue thin,
repite esa misma ruta con Chromium. Nunca sale del dominio ni vuelve a cargar el home como
parte de un deep crawl separado.

## Arquitectura de 2 capas (barato→caro, mismo patrón que Parallel→subagentes)
- **Capa A (este skill, $0, masivo):** Crawl4AI HTTP → Chromium selectivo resuelve la mayoría, incluyendo SPAs.
- **Capa B (agéntica, LLM, solo el residuo):** para challenges/JS raro que la Capa A marca
  `ok:false`. Ahí un agente (browser-use/Stagehand) **autoidentifica y pica botones**. Pendiente de integrar.

## Notas del sandbox (ya resueltas en `sandbox_browser.py`, no re-debuguear)
Todo scraper con navegador aquí necesita: Chromium preinstalado vía `executable_path`,
CA del proxy en el NSS store, y **`--ssl-version-max=tls1.2`** (si no, el middlebox de
inspección TLS resetea el ClientHello TLS1.3 → `ERR_CONNECTION_RESET` en todo sitio).
Detalle completo en `BENCHMARK.md` y en `gtm-enrich-web/LEARNINGS.md`.

## Para escalar (batch grande, ej. las ~1,310 SOFOMes con dominio)
```bash
python .../crawl.py --input sofoms_domains.csv --out crawl_sofoms \
  --http-concurrency 12 --concurrency 3 --max-pages 2
```
Reanuda por resultado y por número de intentos. La concurrencia HTTP puede ser mayor porque
no abre páginas; subir `--concurrency` de Chrome con cuidado porque sí consume memoria.
