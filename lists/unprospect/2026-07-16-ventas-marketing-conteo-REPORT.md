# Conteo de tamaño de equipo — VENTAS × MARKETING (universo entero)

- **Fecha:** 2026-07-16
- **Workspace:** unprospect
- **Estado:** **completo (100%).** Ventas + marketing contados sobre todas las empresas de
  `list_companies`. Persistido en `sales_count`/`sales_bucket` y `marketing_count`/`marketing_bucket`.
- **Costo:** $0 créditos (GetLeads `count` es gratis). ~40k llamadas totales entre ambas dimensiones.
- **Método:** `scripts/dept_counts.py` — cuenta por dominio `job_functions:["Sales & Business Development"]`
  y `["Advertising & Marketing"]`, deduplica por dominio (un conteo por dominio → todas sus filas de nicho),
  A-cut primero, idempotente/resumible. Migración `006_marketing_counts.sql`.

## Cobertura

- **22,008 empresas únicas** (31,000 filas; 6,001 dominios en ≥2 nichos).
- **Con equipo de ventas (≥1):** 10,539
- **Con equipo de marketing (≥1):** 5,314
- **Con ambos (≥1 y ≥1):** 4,001 — el dato más confiable para targeting.
- El "0-sin-señal" está inflado por cobertura floja de GetLeads en empleados MX: mezcla empresas
  realmente chicas/founder-led con empresas donde GetLeads no tiene los contactos. Accionable de verdad = buckets ≥1.

## Matriz ventas (fila) × marketing (columna) — TODAS (22,008)

| ventas ↓ / mkt → | 0 | 1–2 | 3–10 | 11–50 | 50+ | total |
|---|---|---|---|---|---|---|
| 0-sin-señal | 10,168 | 1,047 | 254 | 12 | 1 | 11,482 |
| 1–2 | 3,922 | 1,040 | 322 | 36 | 0 | 5,320 |
| 3–10 | 2,019 | 1,177 | 374 | 54 | 4 | 3,628 |
| 11–50 | 233 | 358 | 300 | 31 | 6 | 928 |
| 50+ | 3 | 20 | 49 | 14 | 1 | 87 |

## Matriz — solo A-cut (4,118 empresas de mayor calidad, universo de extracción)

| ventas ↓ / mkt → | 0 | 1–2 | 3–10 | 11–50 | 50+ | total |
|---|---|---|---|---|---|---|
| 0-sin-señal | 1,440 | 192 | 39 | 3 | 0 | 1,674 |
| 1–2 | **781** | **253** | 74 | 3 | 0 | 1,111 |
| 3–10 | **478** | **300** | 80 | 11 | 0 | 869 |
| 11–50 | 47 | 78 | 72 | 4 | 2 | 203 |
| 50+ | 0 | 1 | 13 | 5 | 0 | 19 |

## Priorización propuesta (para sacar DMs)

- **Tier 1 — sweet spot (A-cut, ~1,812 empresas):** ventas ∈ {1–2, 3–10} × marketing ∈ {0, 1–2}.
  Equipo comercial real pero función de marketing chica o nula → dependen de ventas para generar demanda,
  prospectar no es sistema. Es el pitch exacto de Unprospect. Sub-priorizar las que corren Google Ads (`ads_runs>0`).
- **Tier 2:** A-cut ventas 0-sin-señal × mkt 0 (~1,440) = founder-led sin marketing (validar en muestra: mezcla data gaps).
- **Tier 3:** cola B/C con las mismas celdas; equipos grandes (11–50, 50+) con marketing estructurado = dolor distinto, prioridad baja.

## Calidad y guardrails

- Verificación manual del usuario (2026-07-16): conteos **impecables** en muestra de 10.
- **Outlier cazado:** `airavirtual.com` (Aira) daba 721 ventas — dominio-agregador, GetLeads le colgaba
  contactos de terceros (seguros/tiendas, `company=None`). Reseteado a null + añadido a `DENYLIST` en `dept_counts.py`.
- **Guardrail pendiente antes de extraer:** revisar a ojo las 24 empresas con ventas >100 (7 con >200)
  para cazar otros dominios-agregador tipo Aira. Los buckets chicos (sweet spot) ya están validados.
