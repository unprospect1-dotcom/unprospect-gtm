# Supabase — diagnóstico del "desmadre" y plan de centralización

Fecha: 2026-07-20. Motivo: el modelo se confundió sobre dónde están las firmografías
(buscó en `companies` cuando el grueso vive en `list_companies.meta`). Este doc mapea lo
que HAY y propone la estructura canónica. **Trabajo pendiente para una sesión dedicada.**

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

## Pasos de la sesión de centralización (orden)

1. Función de normalización de dominio (una sola, compartida) + auditar colisiones.
2. Migración: tabla `company` canónica + `contact` con FK por dominio.
3. ETL idempotente meta→columnas y merge por prioridad de fuente (aiark/ocean para
   firmografía; parallel para industry dura; crawl+clasificación para business_model).
4. Re-ligar los 5,279 contactos por dominio; medir cuántos B2B fit ya tienen contacto.
5. Vista `v_outbound_ready` = B2B fit + firmografía mínima + ≥1 contacto con email válido.
6. Actualizar skills/scripts para leer SOLO de `company`/`contact`/vistas, no de las crudas.
7. Deprecar el acceso directo a `companies`/`list_companies` en la capa de consulta.
