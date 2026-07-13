# Learnings de este skill

> Memoria transferible entre clientes. El skill la lee al empezar y agrega entradas al terminar.
> Formato de entrada: `- [YYYY-MM-DD] (confianza: hipótesis|señal|confirmado) aprendizaje — evidencia`
> /gtm-retro consolida y poda este archivo.

## Reglas (confirmadas, aplicar siempre)

- [2026-07-13] (confirmado) El search cobra 0.5 créditos POR PERFIL DEVUELTO — no es gratis. Sondear con `size:1` (el `totalElements` sale completo por 0.5) y jamás paginar de más. Evidencia: saldo 15,100.0 → 15,099.5 tras un search de size=1.
- [2026-07-13] (confirmado) Para conteos masivos (sizing de mercado, tamaño de deptos por empresa) usar `gtm-getleads` primero — sus counts cuestan 0; AI Ark entra para el cierre de emails (encuentra+verifica en tiempo real, no cobra si no hay).
- [2026-07-13] (confirmado) `contact.departmentAndFunction` tiene valores maestros que agrupan: `master_sales` (incluye sales, inside_sales, field_outside_sales, channel_sales, sales_operations, sales_enablement, sales_engineering, sales_training), `master_marketing`, `master_finance`, etc. Usar el master para contar el depto completo.

## Endpoints/paths corregidos en corridas reales

- [2026-07-13] Saldo: `GET /payments/credits` (el `/credit` que traía el script daba 401). Auth: header `X-TOKEN` (Bearer NO funciona pese a lo que dice first-steps de sus docs). Env var real: `AI_ARK_API`.
- [2026-07-13] People search `POST /v1/people` verificado en vivo; exige `size >= 1` (size=0 da 400).

## Conteos de referencia

- [2026-07-13] Gap de bases vs GetLeads (3 transportistas MX): AI Ark lista ~40-60% de la gente que GetLeads (Estafeta 2,722 vs 4,640; Castores 349 vs 544; Tresguerras 248 vs 565) — pero su email finding en tiempo real compensa donde GetLeads solo tiene ~6% VALID en MX. hubspot.com master_sales: 3,179 (vs GetLeads job_function Sales: 1,636 — taxonomías distintas, ninguna es superset).

## Entradas

_(sin entradas todavía)_

## Archivo

_(aprendizajes superados u obsoletos)_
