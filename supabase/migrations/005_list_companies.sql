-- Listas de empresas por nicho — el registro durable de todo list building.
-- Regla (2026-07-14): TODA lista generada por los skills (gtm-getleads, gtm-lists-aiark,
-- gtm-ocean, gtm-prospeo) se upserta aquí con su niche; el CSV local es solo artefacto de trabajo.
create table if not exists list_companies (
  id uuid primary key default gen_random_uuid(),
  niche text not null,            -- slug del nicho: autotransporte-mx, instaladores-solares-mx, ...
  domain text not null,
  name text,
  source text,                    -- aiark | ocean | getleads | prospeo | user
  source_id text,                 -- id del proveedor para re-consultas
  relevance text,                 -- score del proveedor si existe (Ocean: A/B/C)
  company_size text,              -- bracket autoreportado
  staff_linkedin integer,         -- conteo de perfiles LinkedIn (puede ser basura — validar vs GetLeads)
  sales_count integer,            -- conteo GetLeads de contactos en ventas (0 = sin señal)
  sales_bucket text,              -- 0-sin-señal | 1-2 | 3-10 | 11-50 | 50+ | sin-dominio
  meta jsonb,                     -- resto de columnas del CSV de origen
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique (niche, domain)
);
create index if not exists idx_list_companies_niche on list_companies (niche);
create index if not exists idx_list_companies_domain on list_companies (domain);
