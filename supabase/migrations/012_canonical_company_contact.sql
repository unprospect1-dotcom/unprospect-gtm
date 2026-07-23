-- Centralización 2026-07-23 (decisión de Camilo): UNA sola fuente de verdad de empresa.
-- Antes: firmografía partida en 3 lugares (columnas de `companies`, columnas de
-- `list_companies`, y `list_companies.meta` jsonb sin extraer) + 3 claves de dominio
-- sin unir. Ver docs/SUPABASE-ARCHITECTURE.md.
--
-- Este archivo crea SOLO el esquema canónico (DDL). El ETL idempotente que lo llena
-- desde las tablas crudas vive en scripts/centralize_supabase.py (re-ejecutable).
-- Las tablas crudas (companies, list_companies, company_gtm_profiles, contacts, ...)
-- se conservan como STAGING; nadie consulta firmografía fuera de `company`/`contact`.

-- ────────────────────────────────────────────────────────────────────────────
-- Normalización de dominio: UNA sola definición compartida por todo el sistema.
-- minúsculas, sin esquema http(s)://, sin www., sin path, sin puerto.
-- ────────────────────────────────────────────────────────────────────────────
create or replace function norm_domain(d text) returns text
language sql immutable as $$
  select nullif(
    split_part(
      split_part(
        regexp_replace(
          regexp_replace(lower(trim(coalesce(d, ''))), '^https?://', ''),
          '^www\.', ''),
        '/', 1),
      ':', 1),
    '')
$$;

-- ────────────────────────────────────────────────────────────────────────────
-- company: 1 fila por dominio normalizado. La ÚNICA fuente de verdad de firmografía.
-- ────────────────────────────────────────────────────────────────────────────
create table if not exists company (
  domain              text primary key,          -- normalizado (norm_domain)
  name                text,
  website             text,
  description         text,

  -- ── LinkedIn / empleados (lo que Camilo quiere leer fácil) ────────────────
  linkedin_url        text,                       -- URL de la empresa en LinkedIn
  has_linkedin        boolean not null default false,   -- ¿tenemos su LinkedIn?
  employees_on_linkedin integer,                  -- headcount visto en LinkedIn (staff_linkedin)
  linkedin_contacts   integer not null default 0, -- # de personas nuestras con LinkedIn en esta empresa
  employee_count      integer,                    -- headcount duro (Parallel / companies)
  size_bucket         text,                       -- bracket de tamaño autoreportado

  -- ── Firmografía ───────────────────────────────────────────────────────────
  industry            text,
  vertical            text,                       -- niche/vertical del list building
  revenue_range       text,
  founded_year        text,
  hq_country          text,
  hq_state            text,
  hq_city             text,

  -- ── Señal GTM ─────────────────────────────────────────────────────────────
  sales_count         integer,                    -- contactos en ventas (GetLeads)
  sales_bucket        text,
  marketing_count     integer,

  -- ── Clasificación (join de company_gtm_profiles / b2b_classification) ─────
  business_model      text,                       -- b2b | b2c | mixed | unclear
  is_b2b              boolean,
  outbound_fit        text,                       -- high | medium | low | unclear
  what_they_sell      text,
  primary_customer    text,

  -- ── Estado del pipeline de enrichment ─────────────────────────────────────
  crawled             boolean not null default false,   -- ¿tenemos crawl del sitio?
  classified          boolean not null default false,   -- ¿clasificada B2B/fit?
  has_contacts        boolean not null default false,   -- ¿tenemos ≥1 persona?

  -- ── Procedencia ───────────────────────────────────────────────────────────
  sources             text[] not null default '{}',     -- ocean | aiark | parallel | crawl
  niches              text[] not null default '{}',      -- todos los niches donde apareció
  meta                jsonb,                             -- resto sin extraer (auditoría)
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create index if not exists company_has_linkedin_idx     on company (has_linkedin);
create index if not exists company_employees_li_idx      on company (employees_on_linkedin);
create index if not exists company_vertical_idx          on company (vertical);
create index if not exists company_outbound_fit_idx      on company (outbound_fit);
create index if not exists company_is_b2b_idx            on company (is_b2b);

comment on table company is
  'Fuente de verdad canónica de empresa (1 fila por dominio normalizado). Construida por scripts/centralize_supabase.py desde companies + list_companies + company_gtm_profiles. NO consultar firmografía fuera de aquí.';
comment on column company.employees_on_linkedin is 'Headcount visto en LinkedIn (staff_linkedin de list_companies). Puede ser ruidoso — validar vs GetLeads.';
comment on column company.linkedin_contacts is '# de personas nuestras (tabla contact) con linkedin_url en esta empresa.';

-- ────────────────────────────────────────────────────────────────────────────
-- contact: persona ligada a company POR DOMINIO (no por company_id legacy).
-- ────────────────────────────────────────────────────────────────────────────
create table if not exists contact (
  id                  uuid primary key default gen_random_uuid(),
  company_domain      text references company (domain),
  full_name           text,
  first_name          text,
  last_name           text,
  title               text,
  headline            text,
  seniority           text,
  department          text,
  email               text,
  email_status        text,
  linkedin_url        text,
  mobile_phone        text,
  location            text,
  country             text,
  state               text,
  city                text,
  ai_ark_people_id    text,
  source              text,
  legacy_contact_id   uuid,                        -- id en contacts (staging)
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create index if not exists contact_company_domain_idx on contact (company_domain);
create index if not exists contact_email_idx          on contact (email);
create index if not exists contact_linkedin_idx       on contact (linkedin_url);

comment on table contact is
  'Personas ligadas a company por DOMINIO. Construida por scripts/centralize_supabase.py desde contacts (staging).';

-- ────────────────────────────────────────────────────────────────────────────
-- Vistas de lectura
-- ────────────────────────────────────────────────────────────────────────────

-- Resumen ejecutivo de cobertura: cuántas empresas, cuántas con LinkedIn, etc.
create or replace view v_company_coverage as
select
  count(*)                                          as total_companies,
  count(*) filter (where has_linkedin)              as with_linkedin_url,
  count(*) filter (where employees_on_linkedin > 0) as with_employee_headcount,
  count(*) filter (where linkedin_contacts > 0)     as with_linkedin_contacts,
  count(*) filter (where has_contacts)              as with_any_contact,
  count(*) filter (where crawled)                   as crawled,
  count(*) filter (where classified)                as classified,
  count(*) filter (where is_b2b)                    as b2b,
  count(*) filter (where outbound_fit in ('high','medium')) as outbound_fit_ok
from company;

-- Empresas listas para outbound: B2B + fit + firmografía mínima + ≥1 contacto con email.
create or replace view v_outbound_ready as
select c.*
from company c
where c.is_b2b is true
  and c.outbound_fit in ('high', 'medium')
  and c.has_contacts is true
  and exists (
    select 1 from contact ct
    where ct.company_domain = c.domain and ct.email is not null
  );
