# BENCHMARK — por qué crawl4ai (y qué se descartó)

## Optimización masiva 2026-07-17 — HTTP primero, Chromium selectivo

La elección de motor no cambió: ambas capas son Crawl4AI 0.9.2 y producen el mismo
markdown, filtro de densidad y cleaner. Lo que cambió fue cuándo pagamos el navegador.

El wrapper anterior hacía home con Chromium y, si faltaban señales, lanzaba un deep crawl
que volvía a pedir el home antes de abrir una página interna. El supervisor además cerraba
Chrome cada 3 dominios. Para `max-pages=2` eso podía significar tres navegaciones y un nuevo
proceso de Chrome por ola.

La cascada nueva hace:

1. home mediante `AsyncHTTPCrawlerStrategy`;
2. si falta contexto, una página interna elegida por señal GTM;
3. Chromium sólo si el HTML es una shell JS/thin;
4. espera+scroll limitado sólo si el primer render también queda vacío.

Resultados reales:

| prueba | anterior | cascada 0.9.2 |
|---|---:|---:|
| muestra mixta de 10 dominios | varios corridos individualmente | **10/10 en 17.4 s de pared** |
| `21sthr.com` | 147.8 s / 1,147 clean chars | **16.5 s / los mismos 1,147** |
| `7-eleven.com.mx` | 106.6 s / 2 páginas | **7.7 s / 2 páginas**; mismos 50 assets visuales, sin inflar clean con el aviso de privacidad |
| `212.com.mx` HTTP aislado | 7.2 s con Chrome | **0.6–1.0 s**, 3,311 clean chars y las 6 categorías útiles |
| muestra adicional de 20 | 12 sitios útiles en artefactos previos | **17 útiles**; los 3 fallos finales ya fallaban antes |

La muestra adicional recuperó cinco falsos fallos anteriores. La regla de resume ahora
salta éxitos, pero reintenta una vez los `ok:false`; el segundo fallo queda checkpointed.

Nota del source upstream: `arun_many()` usa dispatchers eficientemente para URLs normales,
pero cuando recibe `deep_crawl_strategy` lo evita y procesa las URLs iniciales en secuencia.
Por eso este wrapper controla la concurrencia por dominio y abre directamente las pocas
páginas internas elegidas, en vez de meter deep crawl dentro de `arun_many()`.

Corrida 2026-07-09 sobre 8 dominios SOFOM reales. Chars = texto/markdown útil extraído.
`L` = links internos descubiertos (capacidad de navegar secciones). `Y/.` = ok.

| dominio | trafilatura (sin JS) | playwright+html2text | **crawl4ai** |
|---|---|---|---|
| paya.com.mx (SPA Angular) | 0 . | 3028 Y | 5563 (3L) Y |
| a55.com.mx | 3441 Y | 4085 Y | 8406 (4L) Y |
| aspiria.mx (Cloudflare) | 41 . | 258 Y | 491 (0L) Y |
| factoring.mx | 3890 Y | 5889 Y | 110635 (8L) Y |
| blucapital.mx | 1546 Y | 2706 Y | 7780 (8L) Y |
| apoyosofom.com | 1375 Y | 4778 Y | 5200 (2L) Y |
| alcanacapital.com | 1264 Y | 3095 Y | 5004 (4L) Y |
| ion.com.mx (JS) | 0 . | 6853 Y | 14437 (21L) Y |
| **totales** | **5/8 · 1.0s/sitio** | **8/8 · 5.8s** | **8/8 · 7.6s** |

## Veredicto: crawl4ai
Rinde 8/8 (incluye SPAs), da el texto más rico (markdown, feed directo a `gtm-copy`),
descubre links internos para navegar secciones, y hace click/deep-crawl nativo sin LLM
por página. El sobrecosto vs playwright puro (~1.8s) compra deep-crawl priorizado + markdown
limpio ya resueltos. $0, self-host.

## Descartado (no re-evaluar sin razón nueva)
- **trafilatura (sin JS):** rápido (1s) pero **0 chars en SPAs** (paya, ion) y muere en
  Cloudflare. No puede ser el motor. Además su `fetch_url` no usa el proxy del sandbox y
  cuelga sin timeout. Fuera.
- **playwright + html2text a mano:** funciona (8/8) pero es reinventar lo que crawl4ai ya
  trae (deep-crawl, scoring, markdown, anti-bot). Sin ventaja. Fuera como producto (queda
  como baseline de referencia en el bench, no en el skill).
- **Scrapy / plugin Zyte `/scrape`:** modelo spider-por-layout, bueno para listings
  uniformes, no para miles de homepages distintos; clickear con JS empuja a Zyte API de
  **pago** ($1+/1k requests browser). Rompe el "$0 a escala". Fuera del motor por defecto.
- **Zyte API automatic extraction:** de pago. Solo como fallback puntual para bot-protection
  dura, con el trial de $5. No para batch.

## Residuo → Capa B (agéntica)
Lo único que crawl4ai NO resolvió: challenge de Cloudflare (aspiria.mx quedó en el HTML de
"Just a moment…"). Eso se marca `ok:false` y va a browser-use/Stagehand, donde un agente
autoidentifica y pica botones. Pendiente de integrar; es fracción chica.

## El desbloqueo técnico (aplica a cualquier navegador headless en el sandbox)
`ERR_CONNECTION_RESET` en TODO sitio pese a que curl funciona = el middlebox de inspección
TLS resetea el ClientHello grande de TLS 1.3 (keyshare post-quantum). Fix: `--ssl-version-max=tls1.2`.
Más: Chromium preinstalado vía `executable_path=/opt/pw-browsers/chromium`, `--no-sandbox`,
`--proxy-server=$HTTPS_PROXY`, `--proxy-bypass-list=<-loopback>`, y el CA del proxy importado
al NSS (`~/.pki/nssdb`) con certutil. Todo encapsulado en `sandbox_browser.py`.
