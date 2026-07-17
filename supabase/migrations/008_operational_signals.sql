-- Columnas operativas que ya consumen ads_transparency.py y subcat_to_supabase.py.
-- Centralizarlas aquí evita depender de cambios manuales fuera del historial de migraciones.

alter table list_companies add column if not exists ads_checked boolean;
alter table list_companies add column if not exists ads_runs boolean;
alter table list_companies add column if not exists ads_last_shown date;
alter table list_companies add column if not exists ads_formats text;

alter table list_companies add column if not exists subcat text;
alter table list_companies add column if not exists subcat_confidence text;
alter table list_companies add column if not exists subcat_evidence text;
alter table list_companies add column if not exists subcat_model text;
alter table list_companies add column if not exists subcat_verify text;
alter table list_companies add column if not exists subcat_agree boolean;

create index if not exists idx_list_companies_ads_pending
  on list_companies (niche, ads_checked);
create index if not exists idx_list_companies_subcat
  on list_companies (niche, subcat);
