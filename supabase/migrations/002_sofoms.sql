-- Registro de SOFOMes inscritas en SIPRES (CONDUSEF / gob.mx).
-- Fuente: padrón oficial de SOFOMes (csv exportado del portal), 2,177 entidades.
-- Tabla separada de `companies`: es un padrón de referencia, no una lista de leads.
-- Cuando una SOFOM ya existe en `companies`, `matched_company_id` la liga (match por
-- nombre normalizado sobre razón social o nombre comercial).

create table if not exists sofoms (
  id uuid primary key default gen_random_uuid(),
  codigo text not null unique,            -- código SIPRES
  razon_social text not null,
  nombre_comercial text,
  estado text,                            -- entidad federativa
  tipo text,                              -- ENR (no regulada) | ER (regulada)
  source text not null default 'sipres_gob_mx',
  matched_company_id uuid references companies (id),
  match_type text,                        -- razon_social | nombre_comercial
  workspace text not null default 'unprospect',
  created_at timestamptz not null default now()
);

create index if not exists idx_sofoms_estado on sofoms (estado);
create index if not exists idx_sofoms_matched on sofoms (matched_company_id);

comment on table sofoms is 'SOFOMes inscritas en SIPRES (CONDUSEF/gob.mx). matched_company_id liga a companies cuando es la misma empresa.';
