# Learnings de este skill

> Memoria transferible entre clientes. El skill la lee al empezar y agrega entradas al terminar.
> Formato de entrada: `- [YYYY-MM-DD] (confianza: hipótesis|señal|confirmado) aprendizaje — evidencia`
> /gtm-retro consolida y poda este archivo.

## Reglas (confirmadas, aplicar siempre)

- [2026-07-13] (confirmado) El search cobra 0.5 créditos POR PERFIL DEVUELTO — no es gratis. Sondear con `size:1` (el `totalElements` sale completo por 0.5) y jamás paginar de más. Evidencia: saldo 15,100.0 → 15,099.5 tras un search de size=1.
- [2026-07-13] (confirmado) Para conteos masivos (sizing de mercado, tamaño de deptos por empresa) usar `gtm-getleads` primero — sus counts cuestan 0; AI Ark entra para el cierre de emails (encuentra+verifica en tiempo real, no cobra si no hay).
- [2026-07-13] (confirmado) `contact.departmentAndFunction` tiene valores maestros que agrupan: `master_sales` (incluye sales, inside_sales, field_outside_sales, channel_sales, sales_operations, sales_enablement, sales_engineering, sales_training), `master_marketing`, `master_finance`, etc. Usar el master para contar el depto completo.
- [2026-07-13] (confirmado) Company search cuesta 0.1 créditos por empresa devuelta (más barato que people: 0.5/perfil). Evidencia: saldo 15,098.0 → 15,097.9 con size=1.
- [2026-07-13] (confirmado) **Segmentar por tamaño de departamento es filtro NATIVO del company search**: `account.metric.employee: [{function: ["sales"], start: 3, end: 10}]` (enum CompanyDepartmentEnum: sales, marketing, business_development, finance, engineering…, 27 valores). También `account.metric.growth` con `timeFrame` en meses = deptos CRECIENDO. Probado en vivo: transporte MX con equipo de ventas 3–10 → 857 empresas.

## Endpoints/paths corregidos en corridas reales

- [2026-07-13] Saldo: `GET /payments/credits` (el `/credit` que traía el script daba 401). Auth: header `X-TOKEN` (Bearer NO funciona pese a lo que dice first-steps de sus docs). Env var real: `AI_ARK_API`.
- [2026-07-13] People search `POST /v1/people` verificado en vivo; exige `size >= 1` (size=0 da 400).
- [2026-07-14] (confirmado) `account.location` NO usa la forma de filtro de texto (`{any:{include:{mode,content}}}` da 400 "request not readable") — usa forma enum: `{"location": {"any": {"include": ["Mexico"]}}}`. Verificado en company search en vivo.
- [2026-07-14] (confirmado) En el response de companies, `location.headquarter.country`, `link.domain`, `keywords`, `industries` y `naics` viven en el NIVEL SUPERIOR del registro (no en `summary`); `summary` solo trae name/description/founded_year/type/industry/staff/logo. El post-filtro MX es `record.location.headquarter.country == "Mexico"` (ojo: a veces viene en minúscula "mexico").

## Reglas del usuario (correcciones textuales)

- [2026-07-13] (confirmado, regla del usuario) AI Ark trae DOS conteos de empleados por empresa: `summary.staff.range` (bracket AUTOREPORTADO de LinkedIn) y `summary.staff.total` (perfiles asociados). **En transporte/manufactura usar el autoreportado** (mucho empleado sin LinkedIn); **en SaaS/digital confiar más en el conteo de perfiles**. Ojo: `staff.total` a veces es basura (empresa de 2–10 con total=72,376) — validar contra el conteo de contactos por dominio de GetLeads (gratis).
- [2026-07-13] (confirmado) La categoría/industria es autoreportada y NO es confiable sola: empresa etiquetada "truck transportation" resultó vendedora de insumos/mantenimiento (belum.com.mx). El universo de una categoría se arma con UNIÓN DE LENTES (industria ∪ NAICS ∪ productAndServices) y se verifica con gtm-web-crawler + gtm-classify-b2b ($0) antes de gastar en personas.

## Conteos de referencia

- [2026-07-13] Gap de bases vs GetLeads (3 transportistas MX): AI Ark lista ~40-60% de la gente que GetLeads (Estafeta 2,722 vs 4,640; Castores 349 vs 544; Tresguerras 248 vs 565) — pero su email finding en tiempo real compensa donde GetLeads solo tiene ~6% VALID en MX. hubspot.com master_sales: 3,179 (vs GetLeads job_function Sales: 1,636 — taxonomías distintas, ninguna es superset).
- [2026-07-13] Universo autotransporte MX por lente (sondeos 0.1 c/u): industria "truck transportation" 7,649; NAICS 484xxx 3,880; intersección solo 1,423 → unión ≈ 10,106 (los lentes se traslapan POCO: ninguno solo basta). Sin enterprise (employeeSize 1–999): 5,708 por industria. productAndServices SMART "transporte de carga": 300 (demasiado angosto para enumerar; útil como lente de precisión). Comercio al por mayor (wholesale WORD, sin enterprise): 9,706. Ancla del mundo real (SICT 2024): 205,815 permisionarios, 166k hombre-camión no alcanzable por email, ~38.4k pequeñas+medianas formales → LinkedIn ve ~25% de ese universo.
- [2026-07-13] `employeeSize` se filtra como `{"type":"RANGE","range":[{"start":N,"end":M}]}` — **filtra sobre `staff.total` (conteo de perfiles LinkedIn), NO sobre el bracket autoreportado.** Verificado: belum.com.mx (autoreportado 2–10, staff.total 72,376) NO matchea employeeSize 1–999. ADEMÁS excluye empresas sin dato: truck MX 7,649 → 5,726 incluso con rango 1–100,000 (~25% sin staff.total se pierde con CUALQUIER filtro de tamaño — recuperable con una pasada sin filtro). Para filtrar por autoreportado no hay filtro nativo: se enumera y se post-filtra con `summary.staff.range` del response.

## Entradas

_(sin entradas todavía)_

## Archivo

_(aprendizajes superados u obsoletos)_
