# BENCHMARK — por qué crawl4ai (y qué se descartó)

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
