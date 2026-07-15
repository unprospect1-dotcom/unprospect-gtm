-- Tamaño de departamento de marketing por empresa (GetLeads count, GRATIS) → segmentación.
-- Espejo de sales_count/sales_bucket (migraciones 001/005). Mismo método y economía:
-- contar contactos job_functions:["Advertising & Marketing"] por dominio (0 créditos).
-- Buckets idénticos a ventas para que la matriz ventas × marketing sea directa.
alter table list_companies add column if not exists marketing_count integer;
alter table list_companies add column if not exists marketing_bucket text;
create index if not exists idx_list_companies_marketing_bucket on list_companies (marketing_bucket);
