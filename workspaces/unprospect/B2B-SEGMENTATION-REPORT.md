# B2B Segmentation Report — universo clasificado (2026-07-20)

Fuente: `company_gtm_profiles` (clasificación GTM) × `list_companies` (firmografías Ocean/AI Ark).
Clasificación hecha con OpenAI Batch (gpt-5.4-nano capa 1 + gpt-5.4-mini capa 2 ciega).

## Universo (26,848 dominios crawleados)

| Estado | Dominios |
|---|---|
| accepted (etiqueta confiable) | 15,103 |
| needs_review (frontera b2b↔b2c, decisión de negocio) | 4,782 |
| pending (sobras, re-barrer) | 391 |
| not_profileable (sin texto útil) | 6,572 |

**Por modelo de negocio:** B2B 15,617 · mixed 1,133 · b2c 2,273 · noncommercial 447 · unclear 415.

## El corte accionable

- **12,652 B2B `accepted` con fit outbound alto/medio** — limpios, listos para lista.
- **ICP CORE = 2,858 de esos con equipo comercial de 3+ vendedores** (la señal que compra outbound).

## Matriz: vertical × tamaño de equipo comercial (B2B fit high/medium)

| Vertical | Total | 50+ | 11-50 | 3-10 | 1-2 |
|---|---:|---:|---:|---:|---:|
| autotransporte-mx | 2,666 | 11 | 117 | 439 | 738 |
| distribuidores-industriales | 1,630 | 10 | 126 | 504 | 438 |
| ti-consultoria-software-mx | 1,521 | 3 | 53 | 328 | 699 |
| agencias-audiovisuales-mx | 1,071 | 2 | 23 | 159 | 313 |
| empaque-embalaje-mx | 821 | 1 | 60 | 275 | 250 |
| despachos-contables-mx | 642 | 0 | 8 | 49 | 201 |
| instaladores-solares-mx | 531 | 0 | 18 | 85 | 168 |
| fintech-b2b-mx | 461 | 4 | 36 | 141 | 137 |
| ciberseguridad-mx | 348 | 2 | 34 | 104 | 108 |
| hr-tech-mx | 253 | 5 | 10 | 67 | 81 |
| logistics-tech-mx | 232 | 3 | 20 | 80 | 65 |
| saas-producto-mx | 204 | 0 | 13 | 68 | 59 |
| (sin lista — huérfanos del crawl) | 2,272 | — | — | — | — |

**Lectura:** los mejores objetivos por volumen × equipo comercial son **autotransporte**,
**distribuidores industriales** y **TI/software** — cada uno con 400-500 empresas de 3-10
vendedores, el sweet spot del ICP.

## Cobertura firmográfica REAL (con el campo `meta` de list_companies)

| Señal | Cobertura sobre los 12,652 B2B fit |
|---|---:|
| vertical / niche | 82% |
| tamaño equipo comercial (sales_bucket) | 82% |
| employee/staff count | 46% |
| ubicación (estado) | 40% |
| LinkedIn URL | 22% |
| revenue range | 22% |

**Deuda de datos (ver `docs/SUPABASE-ARCHITECTURE.md`):** employee_count y LinkedIn los trae
AI Ark/Ocean en el export original, pero en Supabase quedaron enterrados en `list_companies.meta`
(jsonb) sin extraer a columnas, y el 18% de los B2B fit ni siquiera está en list_companies
(huérfanos del crawl). Para tener employee_count + LinkedIn en TODOS hay que: (1) extraer meta
a columnas, (2) re-ligar los huérfanos, (3) para lo que de verdad falte, re-pull de AI Ark/Ocean.
