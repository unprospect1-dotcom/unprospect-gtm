# Supabase — centralización (HECHA 2026-07-23) + diagnóstico del "desmadre"

Fecha del diagnóstico: 2026-07-20. Motivo: el modelo se confundió sobre dónde están las
firmografías (buscó en `companies` cuando el grueso vive en `list_companies.meta`).

> **✅ ESTADO 2026-07-23 — CENTRALIZADO.** Ya existen las tablas canónicas `company`
> (26,844 empresas, 1 fila por dominio normalizado) y `contact` (5,186 personas ligadas
> por dominio). DDL en `supabase/migrations/012_canonical_company_contact.sql`; ETL
> idempotente y re-ejecutable en `scripts/centralize_supabase.py` (corre server-side vía
> Management API, no mueve las ~70k filas por red). Las tablas crudas quedan como STAGING.
> **Regla nueva: firmografía se consulta SOLO en `company`/`contact` y las vistas.**
>
> Consulta rápida de cobertura: `select * from v_company_coverage;`
> Empresas listas para outbound: `select * from v_outbound_ready;`
>
> **Empleados ligados a LinkedIn (lo que preguntó Camilo), fácil de leer:**
> - `company.employees_on_linkedin > 0` → **11,899** empresas con headcount visto en LinkedIn.
> - `company.has_linkedin = true` → **10,512** empresas con página de LinkedIn.
> - `company.linkedin_contacts > 0` → **3,039** empresas con personas nuestras que tienen LinkedIn.
> - Cruce accionable (headcount LinkedIn **y** B2B fit high/medium) → **7,131** empresas.

### Reglas de datos (semántica que NO se debe romper)
- **`employees_on_linkedin` / `employee_count`: 0 NUNCA es válido.** Una empresa no tiene 0
  empleados; un 0 = **sin dato = NULL**. El ETL fuerza `nullif(...,0)`. Al mostrar en tablas,
  usar **"s/d"** para NULL (no "0"), para no confundir "sin dato" con un cero real.
- **De dónde viene el hueco de headcount:** AI Ark SIEMPRE trae `staff.total` (0 empresas de
  AI Ark sin dato); **Ocean casi nunca lo trae** (8,531 empresas Ocean sin headcount). El
  cierre del hueco (~13,173 sin dato) es enriquecimiento por AI Ark.
- **`sales_bucket='0-sin-señal'` es distinto:** ahí el 0 SÍ es un valor real de GetLeads
  (contó 0 contactos de ventas), aunque puede ser falso negativo por cobertura MX débil (~6%)
  o títulos en español que no mapean a su taxonomía.

Lo de abajo es el diagnóstico original que motivó la centralización (se conserva como registro).

## Lo que hay hoy (dos universos paralelos que NO están unidos)

### Universo A — "las 6 mil de hace tiempo" (con contactos)
- **`companies`** (6,648) — pull viejo, enriquecido por Parallel (`enrichment_source=parallel.ai`).
  Origin: icp_list (3,331) + derived_from_contact (3,317). Tiene industry, size_bucket,
  employee_count, description, linkedin_url en COLUMNAS. Key: `id` + `domain`.
- **`contacts`** (5,279) / **`contacts_enriched`** (5,279) — personas ligadas por `company_id`.
  Traen email (2,581 con email), title, seniority, department, linkedin_url, mobile_phone,
  `ai_ark_people_id`. **SÍ tienen contacto** — vienen de AI Ark people.
- **`outbound_leads_master`** (8,636) — capa de leads deduplicada (record_type, master_key,
  dedupe_basis). Es el intento previo de tabla unificada.

### Universo B — el crawl+clasificación (SIN contactos aún)
- **`list_companies`** (31,000) — listas Ocean (22,590) + AI Ark (8,410). Firmografías en
  columnas PARCIALES (niche, sales_bucket, company_size, staff_linkedin) y el RESTO en
  `meta` (jsonb): linkedin, city/state, revenue_range, description, naics, founded_year,
  keywords, industry_categories. Key: `domain` (con duplicados por dominio).
- **`site_crawls`** (26,848) — crawl del sitio. Key: `domain`.
- **`company_gtm_profiles`** (26,848) — clasificación B2B/fit/sells/customer. Key: `domain`.

### El problema
- **Tres claves de "empresa" distintas** (`companies.domain`, `list_companies.domain`,
  `company_gtm_profiles.domain`) sin una tabla canónica que las una. El solape
  companies↔clasificados es solo ~23%.
- **Firmografías partidas en 3 lugares**: columnas de `companies`, columnas de
  `list_companies`, y `list_companies.meta` (jsonb sin extraer).
- **Contactos ligados por `company_id`** (universo A) que NO conecta con el universo B
  (el crawl) por dominio.
- Duplicados en `list_companies` (varias filas por dominio de distintas listas/fuentes).

## Estructura canónica propuesta (para la sesión de centralización)

```
company (canónica, 1 fila por dominio normalizado)
  domain PK (normalizado: sin www, minúsculas, sin slash)
  name, linkedin_url, hq_country, hq_state, hq_city
  employee_count, size_bucket, revenue_range, industry, vertical/niche
  sales_count, sales_bucket, marketing_count           <- señal GTM
  -- clasificación (join de company_gtm_profiles)
  business_model, is_b2b, outbound_fit, what_they_sell, primary_customer
  -- procedencia
  sources text[]  (ocean|aiark|parallel|crawl), first_seen, last_enriched
        │ 1..N
   contact (persona)
     company_domain FK -> company.domain     <- ligar por DOMINIO, no company_id
     full_name, title, seniority, department, email, email_status,
     linkedin_url, mobile_phone, ai_ark_people_id, source
```

Reglas: `company` es la única fuente de verdad de firmografía; se construye con un ETL que
(1) normaliza dominios, (2) extrae `list_companies.meta` a columnas, (3) fusiona
`companies` + `list_companies` + `company_gtm_profiles` por dominio (prioridad de fuente
declarada), (4) re-liga `contacts` por dominio. Las tablas crudas se conservan como staging;
nadie consulta firmografía fuera de `company`.

## Pasos de la centralización — estado

1. ✅ Función `norm_domain()` (una sola, compartida) — migración 012. Colisiones auditadas
   (list_companies 31,000 filas → 22,008 dominios únicos; universo unificado 26,844).
2. ✅ Tablas `company` canónica + `contact` con FK por dominio — migración 012.
3. ✅ ETL idempotente meta→columnas y merge por prioridad de fuente (aiark/ocean para
   firmografía; parallel para employee_count/linkedin; crawl+clasificación para
   business_model/outbound_fit) — `scripts/centralize_supabase.py`.
4. ✅ 5,186 de 5,279 contactos religados por dominio (93 sin company_id ni email_domain
   resolvible quedan solo en staging). 3,317 empresas ya tienen ≥1 contacto.
5. ✅ Vistas `v_company_coverage` (resumen) y `v_outbound_ready` (B2B fit + ≥1 contacto
   con email) = **1,503** empresas.
6. ⏳ PENDIENTE: actualizar skills/scripts para leer SOLO de `company`/`contact`/vistas.
7. ⏳ PENDIENTE: deprecar el acceso directo a `companies`/`list_companies` en la capa de
   consulta. El ETL es re-ejecutable, así que las crudas se pueden seguir alimentando y
   re-centralizar con `python scripts/centralize_supabase.py --apply`.
