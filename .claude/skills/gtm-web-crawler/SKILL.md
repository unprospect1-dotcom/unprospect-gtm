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
`--no-resume` (rehacer aunque exista). **Por defecto reanuda**: si ya existe `<out>/<dominio>.json`, lo salta.

## Salida
Un `<out>/<dominio>.json` por sitio:
```json
{ "domain": "...", "ok": true, "n_pages": 4, "secs": 13.1,
  "pages": [ {"url":"...", "path":"/nosotros", "chars": 1234, "markdown":"..."} ],
  "combined_markdown": "# /\n...\n---\n# /nosotros\n..." }
```
- `combined_markdown` es **raw data para enrichment y segmentación** (a quién le venden, si es B2B o no, casos de estudio, sectores, etc.). NO es copy ni feed a `gtm-copy`; el análisis/extracción de señales es un paso posterior aparte.
- `ok:false` con `reason: sin_contenido_util__escalar_a_capa_B_agentica` = challenge/bot-protection
  (Cloudflare) o sitio muerto → esos van a la **Capa B agéntica** (browser-use/Stagehand), no se inventan.

## Cómo navega las secciones (respuesta a "¿todo el sitio o solo el home?")
Deep-crawl priorizado: parte del home, puntúa los links internos por keywords de alto
valor (nosotros/servicios/aviso/privacidad/legal/contacto…) y visita primero esos, hasta
`--max-pages`, sin salir del dominio. No hay que listar URLs a mano.

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
