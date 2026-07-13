# Universo autotransporte MX — enumeración AI Ark (2026-07-13)

**Estado: UNIVERSO COMPLETO CON BUCKETS — 6 lentes, 148 industrias auditadas, 8,125 dominios con conteo de equipo comercial ($0). Crawler corriendo (persiste a `site_crawls` en Supabase).**

## Distribución FINAL de buckets (México con dominio, 8,201 empresas)
| sales_bucket | Empresas | % |
|---|---|---|
| 0-sin-señal | 5,501 | 67% |
| 1-2 | 1,595 | 19% |
| 3-10 | 862 | 10% |
| 11-50 | 220 | 2% |
| 50+ | 23 | <1% |

**2,348 empresas NUEVAS (no en Supabase) con equipo comercial de 1–50** — el target directo.

## Fase 2 (mismo día): las lentes que faltaban
Revisión manual de las 148 industrias de AI Ark + NAICS del ecosistema. Lentes agregadas
(con exclusiones encadenadas para no pagar traslapes dos veces):

| Lente | Empresas (únicas tras dedupe) |
|---|---|
| `freight and package transportation` | 2,411 |
| `transportation, logistics, supply chain and storage` | 878 |
| `warehousing and storage` | 235 |
| NAICS 488 (forwarding/apoyo) + 492 (paquetería) + 493 (almacenes), sin 484 | 1,949 |

**Universo total: 11,671 únicas · 11,272 MX · 8,201 con dominio.** Costo fase 2: 588.5 créditos.

Evaluadas y EXCLUIDAS a propósito (van en la etapa de mayoreo/comex, no en transporte):
`wholesale import and export` (335 MX 2–700) e `international trade and development` (1,080) —
traders y aduanales, no transportistas. `maritime transportation` y `airlines and aviation`
fuera por no ser terrestre; mudanzas ya cubiertas por NAICS 484210.

## Distribución de buckets (México con dominio, 4,661 empresas)
| sales_bucket | Empresas | % |
|---|---|---|
| 0-sin-señal | 2,940 | 63% |
| 1-2 | 960 | 20% |
| 3-10 | 589 | 12% |
| 11-50 | 156 | 3% |
| 50+ | 16 | <1% |

- **1,482 empresas NUEVAS (no en Supabase) con equipo comercial de 1–50** — el corazón del target.
- "0-sin-señal" ≠ sin equipo: significa cero contactos etiquetados ventas en GetLeads; muchas tienen
  gente (`total_count` > 0) sin etiquetar — se rescatan con la escalera de fallback del skill gtm-getleads.
- La doble compuerta funcionó: **187 empresas** tienen `staff_linkedin` (AI Ark) inflado >3× vs el
  conteo real de GetLeads — usar `total_count`/`sales_count` como verdad de alcanzabilidad.

## Qué es
Etapa 1 del pipeline canónico (ver `docs/PLAN-lead-platforms.md` §5): el universo completo de
empresas de autotransporte de carga en México visibles en AI Ark, con corte de alcanzabilidad
**2–700 personas en LinkedIn** (decisión del usuario: corte por LinkedIn, NO autoreportado;
mínimo 2 para transporte por subrepresentación de operadores).

Siguiente paso: crawler propio (`gtm-web-crawler`) sobre los dominios → subcategorías
(flota carga general / refrigerado / freight forwarder / 3PL / software / paquetería) →
`gtm-pain-segments` con los buckets de equipo comercial.

## Filtros reproducibles (AI Ark `POST /v1/companies`, 0.1 créditos/empresa)
- Lente A `industry`: `location=Mexico` + `industries WORD "truck transportation"` + `employeeSize RANGE 2–700` → 4,557
- Lente B `naics_only`: `location=Mexico` + `naics IN (484110,484121,484122,484210,484220,484230)` + `industries EXCLUDE "truck transportation"` + mismo employeeSize → 1,696

## Números
| Métrica | Valor |
|---|---|
| Empresas únicas enumeradas | 6,198 |
| **México real** (el filtro location=Mexico coló New Mexico/US y otros — columna `pais_ok`) | **5,929** |
| Con dominio (crawleables) | 4,661 (79%) |
| Ya en Supabase (`en_supabase=si`) | 311 |
| **Nuevas con dominio** | **4,350** |
| Sin dominio (solo LinkedIn) | ~1,270 |
| Dominios únicos al batch de buckets | 4,619 |

Top estados: Nuevo León (~700 con variantes de grafía), Jalisco 375, CDMX 260, Tamaulipas 173, Edomex 171.

## Créditos
- Enumeración: 625.3 (6,253 filas devueltas × 0.1)
- Página perdida por debug de Cloudflare/User-Agent: 10.0
- Sondeos de diseño (2026-07-13): ~1.6
- **Saldo AI Ark después: 14,461.4** · GetLeads: 5,000 intacto (conteos gratis) · Ocean: intacto

## Calidad de datos observada (para el crawler)
- `staff_linkedin` a veces basura (ej. 72k en empresa de 10) — el batch de GetLeads (columnas
  `sales_count`/`total_count`) es la doble compuerta.
- Hay dominios basura (IPs, dominios ajenos) en AI Ark — el crawler los descarta.
- 269 empresas de otros países marcadas `pais_ok=no` — NO eliminadas del CSV, filtrar al usar.
- Grafías de estado inconsistentes ("Nuevo León"/"Nuevo Leon") — normalizar al segmentar.

## Archivos
- `2026-07-13-autotransporte-mx-universo.csv` (gitignored — 6,198 filas; el maestro local)
- `transport-sales-counts.csv` (scratchpad; se fusiona al terminar el batch como `sales_count`,
  `total_count` y `sales_bucket`: 0=sin señal / 1-2 / 3-10 / 11-50 / 50+)
