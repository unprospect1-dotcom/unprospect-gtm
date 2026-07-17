-- site_crawls: raw crawl de sitios web (gtm-web-crawler).
-- combined_markdown = insumo para el paso posterior de enrichment/segmentacion.
-- Keyed por dominio (varias SOFOMes pueden compartir dominio de grupo) -> join a sofoms.domain.

create table if not exists site_crawls (
  domain text primary key,
  ok boolean not null default false,
  n_pages int not null default 0,
  secs numeric,
  reason text,
  http_status text,
  pages jsonb,
  combined_markdown text,
  clean_text text,
  crawled_at timestamptz not null default now()
);

-- Upgrade path for databases created before clean_text became the LLM input.
alter table site_crawls add column if not exists clean_text text;

-- Tabla interna: accesible por el pipeline server-side, nunca por clientes públicos.
alter table site_crawls enable row level security;
grant select, insert, update on table site_crawls to service_role;

create index if not exists site_crawls_ok_idx on site_crawls(ok);

comment on table site_crawls is
  'Raw crawl de sitios (gtm-web-crawler). combined_markdown = insumo para enrichment/segmentacion. Join a sofoms.domain.';
