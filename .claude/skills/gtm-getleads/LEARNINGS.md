# Learnings de este skill

> Memoria transferible entre clientes. El skill la lee al empezar y agrega entradas al terminar.
> Formato de entrada: `- [YYYY-MM-DD] (confianza: hipótesis|señal|confirmado) aprendizaje — evidencia`
> /gtm-retro consolida y poda este archivo.

## Reglas (confirmadas, aplicar siempre)

- [2026-07-13] (confirmado) `count` y `filter-values` cuestan 0 créditos SIEMPRE — contar antes de gastar, sin excepción. Evidencia: ~30 conteos corridos, saldo intacto en 5,000, `credits_used: 0` en cada response.
- [2026-07-13] (confirmado) Los arrays de filtro son OR interno, AND entre campos — verificado: "Director"=823 + "Gerente"=2,272 = ambos-en-array 3,095 exacto (transporte MX).
- [2026-07-13] (confirmado) El match de `job_titles` es substring y SENSIBLE A ACENTOS — "Tráfico"=404 vs "Trafico"=157 en el mismo segmento. Sondear siempre ambas variantes.
- [2026-07-13] (confirmado) `exclude_job_titles: ["Asistente","Assistant"]` es obligatorio cuando el diccionario incluye "Director" — "Asistente" solo ya matcheaba 337 en transporte MX.
- [2026-07-13] (confirmado) En México la taxonomía (seniority/job_functions) pierde DMs masivamente: dirección C-Team=638 vs unión con diccionario ES=909 (+42%); ventas +10%; marketing +30%. La unión de capas no es opcional.
- [2026-07-13] (confirmado) Cobertura de email VALID en México ~6% (transporte: 1,722 de 29,462) — GetLeads selecciona, AI Ark cierra los emails (tiempo real, no cobra si no encuentra). DMs con VALID en 3 transportistas reales: Estafeta 5/43, Castores 0/12, Tresguerras 0/10.

## Diccionarios de títulos por sector/geo (activo reutilizable)

### Transporte terrestre de carga — México (2026-07-13)
- Dirección: CEO, Director General, Dueño, Propietario, Fundador, Founder, Owner, Socio, Socio Fundador, Presidente, Gerente General, General Manager, Managing Director
- Ventas: Ventas, Comercial, Sales, Business Development, Desarrollo de Negocio, KAM, Key Account, Jefe de Ventas, Coordinador Comercial
- Marketing: Marketing, Mercadotecnia, Mercadeo, Growth, Publicidad, Brand, Marca
- Sectoriales descubiertos por sondeo: **Tráfico/Trafico** (404+157 — EL título operativo del sector), Encargado (249), Administrador (232), Gerente de Sucursal (72), Subdirector (28), Head (47)
- Excludes: Asistente, Assistant

## Conteos de referencia (para calibrar sorpresas)

- [2026-07-13] Transporte carga MX (Truck Transportation + Transportation/Trucking/Railroad + Freight and Package Transportation, HQ Mexico): 29,462 contactos; DMs unión 3 personas ≈ 4,300.
- [2026-07-13] Gap de bases GetLeads vs AI Ark (mismas 3 empresas MX): Estafeta 4,640 vs 2,722; Castores 544 vs 349; Tresguerras 565 vs 248. GetLeads lista 1.6–2.3× más gente; AI Ark compensa con email finding en tiempo real. Ninguna base sola es el universo.

## Endpoints/campos corregidos en corridas reales

- [2026-07-13] Auth verificada: `Authorization: Bearer` con key `glb_live_…` (env `GETLEADS_API`). Health OK (335.5M registros). No hay endpoint de saldo dedicado: el `creditsRemaining` viene en los responses de count (gratis) — de ahí el subcomando `credits`.

## Entradas

_(las nuevas corridas agregan aquí)_

## Archivo

_(aprendizajes superados u obsoletos)_
