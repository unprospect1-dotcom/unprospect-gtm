# Conteo de tamaño de equipo — VENTAS × MARKETING (universo entero)

- **Fecha:** 2026-07-16
- **Workspace:** unprospect
- **Estado:** **completo (100%).** Ventas + marketing contados sobre todas las empresas de
  `list_companies`. Persistido en `sales_count`/`sales_bucket` y `marketing_count`/`marketing_bucket`.
- **Costo:** $0 créditos (GetLeads `count` es gratis). ~40k llamadas totales entre ambas dimensiones.
- **Método:** `scripts/dept_counts.py` — cuenta por dominio `job_functions:["Sales & Business Development"]`
  y `["Advertising & Marketing"]`, deduplica por dominio (un conteo por dominio → todas sus filas de nicho),
  A-cut primero, idempotente/resumible. Migración `006_marketing_counts.sql`.

## Universo y capas de segmentación

- **22,008 empresas únicas** (31,000 filas; 6,001 dominios en ≥2 nichos).

### Por nicho (universo lookalike, por fila)
| nicho | filas | · | nicho | filas |
|---|---|---|---|---|
| autotransporte-mx | 8,410 | · | despachos-contables-mx | 1,503 |
| agencias-audiovisuales-mx | 3,407 | · | logistics-tech-mx | 1,312 |
| distribuidores-industriales-mx | 3,404 | · | hr-tech-mx | 1,299 |
| ti-consultoria-software-mx | 3,068 | · | saas-producto-mx | 1,138 |
| empaque-embalaje-mx | 2,569 | · | instaladores-solares-mx | 1,120 |
| fintech-b2b-mx | 2,109 | · | ciberseguridad-mx | 1,661 |

### Por relevance (calidad lookalike, empresa única)
A: 4,118 (19%) · B: 9,344 (42%) · C: 1,226 (6%) · sin score (autotransporte/AI Ark): 7,320 (33%)

### Tamaño de equipo (empresa única)
| bucket | ventas | marketing |
|---|---|---|
| 0-sin-señal | 11,468 | 16,693 |
| 1–2 | 5,720 | 3,790 |
| 3–10 | 3,779 | 1,352 |
| 11–50 | 952 | 160 |
| 50+ | 88 | 12 |
| **con equipo (≥1)** | **10,539** | **5,314** |

- **Con ventas ≥1 Y marketing ≥1: 4,000** — el dato más confiable para targeting.
- **Google Ads:** corre 3,550 · no 18,453.
- El "0-sin-señal" está inflado por cobertura floja de GetLeads en empleados MX (mezcla empresas
  chicas reales con empresas sin contactos en su base). Accionable de verdad = buckets ≥1.

## Matriz ventas (fila) × marketing (columna) — TODAS (22,008)

| ventas ↓ / mkt → | 0 | 1–2 | 3–10 | 11–50 | 50+ | total |
|---|---|---|---|---|---|---|
| 0-sin-señal | 10,154 | 1,047 | 254 | 12 | 1 | 11,468 |
| 1–2 | 4,196 | 1,136 | 347 | 41 | 0 | 5,720 |
| 3–10 | 2,100 | 1,225 | 392 | 58 | 4 | 3,779 |
| 11–50 | 239 | 362 | 310 | 35 | 6 | 952 |
| 50+ | 4 | 20 | 49 | 14 | 1 | 88 |

## Matriz — solo A-cut (4,118 empresas de mayor calidad, universo de extracción)

| ventas ↓ / mkt → | 0 | 1–2 | 3–10 | 11–50 | 50+ | total |
|---|---|---|---|---|---|---|
| 0-sin-señal | 1,441 | 193 | 39 | 3 | 0 | 1,676 |
| 1–2 | **878** | **285** | 85 | 3 | 0 | 1,251 |
| 3–10 | **519** | **333** | 89 | 12 | 0 | 953 |
| 11–50 | 49 | 82 | 78 | 6 | 2 | 217 |
| 50+ | 1 | 1 | 13 | 5 | 0 | 20 |

## Priorización propuesta (para sacar DMs)

- **Tier 1 — sweet spot (A-cut, ~2,015 empresas):** ventas ∈ {1–2, 3–10} × marketing ∈ {0, 1–2}
  (celdas en negrita). Equipo comercial real pero función de marketing chica o nula → dependen de ventas
  para generar demanda, prospectar no es sistema. Es el pitch exacto de Unprospect. Sub-priorizar `ads_runs>0`.
- **Tier 2:** A-cut ventas 0-sin-señal × mkt 0 (~1,441) = founder-led sin marketing (validar en muestra: mezcla data gaps).
- **Tier 3:** cola B/C con las mismas celdas; equipos grandes (11–50, 50+) con marketing estructurado = dolor distinto, prioridad baja.

## Calidad y guardrails

- Verificación manual del usuario (2026-07-16): conteos **impecables** en muestra de 10.
- **Outlier cazado:** `airavirtual.com` (Aira) daba 721 ventas — dominio-agregador, GetLeads le colgaba
  contactos de terceros (seguros/tiendas, `company=None`). Reseteado a null + añadido a `DENYLIST` en `dept_counts.py`.
- **Fix de datos (2026-07-16):** 781 filas de una corrida vieja tenían `sales_count` pero `sales_bucket` en null;
  backfill por SQL derivando el bucket del conteo. Sin este fix las matrices subcontaban los buckets ≥1.
- **Guardrail pendiente antes de extraer:** revisar a ojo las ~24 empresas con ventas >100 (7 con >200)
  para cazar otros dominios-agregador tipo Aira. Los buckets chicos (sweet spot) ya están validados.
