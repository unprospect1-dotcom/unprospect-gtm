# Learnings de gtm-web-crawler

> Memoria transferible del crawler. Registrar aquí sólo hallazgos medidos y reutilizables.

- [2026-07-17] (confirmado, dos muestras reales) Para clasificación GTM no conviene abrir
  Chromium por defecto. La capa HTTP incorporada de Crawl4AI conserva markdown, links,
  assets y las señales del cleaner; Chromium debe reservarse para shell JS, contenido thin
  o señales faltantes. En la muestra control: 10/10 en 17.4 s de pared.
- [2026-07-17] (confirmado) Con `max-pages=2`, deep crawl después de un home previo vuelve a
  pedir el home y añade esperas artificiales. Elegir directamente el mejor link interno
  conserva el objetivo GTM y elimina la navegación duplicada.
- [2026-07-17] (confirmado) Reciclar el proceso completo cada 3 dominios era excesivo. Con
  HTTP primero, ciclo de 100 dominios y 3 pestañas máximas por worker es conservador; los
  checkpoints permiten reiniciar sólo el worker afectado.
- [2026-07-17] (confirmado) Resume por existencia de archivo congela falsos fallos. Saltar
  `ok:true` y permitir exactamente un rescate de `ok:false` recuperó 5 dominios útiles en
  una muestra de 20 sin crear un loop infinito.
- [2026-07-17] (confirmado) Un render rápido puede devolver `success=True` pero cero markdown.
  Tratarlo como `no_usable_content` es necesario para activar el segundo render con espera
  y scroll limitado; así se recuperaron `919mexico.com` y `aairh.mx`.
