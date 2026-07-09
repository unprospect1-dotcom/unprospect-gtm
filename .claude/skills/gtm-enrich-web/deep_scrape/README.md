# Deep scrape — fase 2 de enrichment (dominio → contenido para personalización)

Motor elegido tras el bake-off (2026-07-09): **crawl4ai** (render JS + markdown +
deep-crawl/click nativo, self-host, $0). Con **trafilatura** como fast-path para
sitios obviamente estáticos y **capa agéntica** (browser-use/Stagehand) reservada
para el residuo (Cloudflare y JS raro).

## Archivos
- `sandbox_browser.py` — **helper obligatorio para correr Chromium en el sandbox CCR.**
  Resuelve los 3 bloqueos (binario preinstalado, CA del proxy en NSS, reset del
  ClientHello TLS1.3). Cualquier scraper con JS (crawl4ai, scrapy-playwright,
  browser-use, Stagehand) debe usar esta config o no arranca. Ver `LEARNINGS.md`.
- `bakeoff.py` — comparador de scrapers por etapas (`python bakeoff.py <trafilatura|playwright|crawl4ai>`),
  escribe `bakeoff_results.json` incremental.
- `bakeoff_results.json` — resultados de la corrida sobre 8 dominios SOFOM reales.

## Config de Chromium en el sandbox (resumen)
```python
import sandbox_browser as sb
sb.bootstrap_nss()          # importa el CA del proxy en ~/.pki/nssdb (idempotente)
# Playwright directo:
b = p.chromium.launch(**sb.launch_kwargs())
# crawl4ai:
sb.patch_crawl4ai()         # inyecta executable_path + flags TLS/proxy
```
Flags clave: `executable_path=/opt/pw-browsers/chromium`, `--no-sandbox`,
`--proxy-server=$HTTPS_PROXY`, `--proxy-bypass-list=<-loopback>`,
`--ssl-version-max=tls1.2` (el fix del reset del ClientHello post-quantum).

## Resultado del bake-off (8 dominios SOFOM, 2026-07-09)
| método | ok | t prom | notas |
|---|---|---|---|
| trafilatura (sin JS) | 5/8 | 1.0s | rápido pero **0 chars en SPAs** (paya, ion) |
| playwright + html2text | 8/8 | 5.8s | rinde SPAs; texto plano; descubre links internos |
| **crawl4ai** | **8/8** | **7.6s** | **más texto útil (markdown), deep-crawl + click nativo** |

Los dos con navegador descubren links internos (3–22/sitio) → deep-crawl acotado
navega secciones solo (home + nosotros + servicios + aviso de privacidad).
Ninguno resuelve el challenge de Cloudflare (aspiria.mx) → eso va a la capa agéntica.
