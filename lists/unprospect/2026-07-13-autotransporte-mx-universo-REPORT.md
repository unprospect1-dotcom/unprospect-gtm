# Universo autotransporte MX — enumeración AI Ark (2026-07-13)

**Estado: COMPLETO — enumeración + buckets de equipo comercial fusionados (batch gratis GetLeads, 9,238 conteos, $0)**

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
