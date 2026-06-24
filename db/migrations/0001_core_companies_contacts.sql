-- =============================================================================
-- 0001_core_companies_contacts.sql
-- Normalized outbound core: companies (account master) 1 --- N contacts.
--
-- ADDITIVE & NON-DESTRUCTIVE: creates new objects only. It does NOT touch
-- outbound_leads_master, which stays as the raw / staging / ingestion layer.
-- Safe to re-run (idempotent: IF NOT EXISTS / CREATE OR REPLACE everywhere).
-- =============================================================================

begin;

-- gen_random_uuid() lives in pgcrypto; pg_trgm powers the name trigram index.
-- Both extensions must be created up front, before any table or index below
-- references them (the gin_trgm_ops operator class comes from pg_trgm).
create extension if not exists pgcrypto;
create extension if not exists pg_trgm;

-- -----------------------------------------------------------------------------
-- Helpers
-- -----------------------------------------------------------------------------

-- Canonicalize a domain: lowercase, strip scheme, strip leading "www.",
-- drop any path. Returns NULL for empty input. Used both here and at write time
-- so company identity stays consistent.
create or replace function norm_domain(d text)
returns text language sql immutable as $$
  select nullif(
    split_part(
      regexp_replace(
        regexp_replace(lower(trim(coalesce(d, ''))), '^https?://', ''),
        '^www\.', ''
      ),
      '/', 1
    ),
  '');
$$;

-- Parse a possibly-dirty text number into int4, returning NULL when empty or
-- out of int4 range (some staging rows carry garbage like 14-digit strings in
-- company_employee_count). Prevents 22003 overflow during backfill.
create or replace function safe_int(t text)
returns integer language sql immutable as $$
  select case
    when nullif(regexp_replace(coalesce(t, ''), '[^0-9]', '', 'g'), '') is null then null
    when nullif(regexp_replace(coalesce(t, ''), '[^0-9]', '', 'g'), '')::numeric
         between -2147483648 and 2147483647
      then nullif(regexp_replace(coalesce(t, ''), '[^0-9]', '', 'g'), '')::int
    else null
  end;
$$;

-- Generic updated_at touch trigger.
create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

-- -----------------------------------------------------------------------------
-- companies — the account master (one row per company / account)
-- -----------------------------------------------------------------------------
create table if not exists companies (
  id                       uuid primary key default gen_random_uuid(),

  -- identity (dedupe on domain first, linkedin_url as fallback)
  domain                   text,                 -- normalized via norm_domain()
  linkedin_url             text,
  name                     text,
  website                  text,

  -- firmographics
  industry                 text,
  size_bucket              text,                 -- e.g. "11-50 employees"
  employee_count           integer,
  company_type             text,
  primary_phone            text,
  founding_year            integer,
  annual_revenue           text,                 -- ranges/strings, kept as text

  -- enrichment (Parallel.ai et al.)
  description              text,
  description_short        text,
  description_source_urls  text[],
  description_basis        jsonb,
  enrichment_status        text,
  enrichment_source        text,
  enrichment_task_group_id text,
  enrichment_task_run_id   text,
  enrichment_error         text,
  enriched_at              timestamptz,
  needs_company_review     boolean not null default false,

  -- location (HQ)
  hq_location              text,
  hq_country               text,
  hq_state                 text,
  hq_city                  text,

  -- segmentation
  niche                    text,
  subniche                 text,
  tags                     text[],
  icp_score                integer,              -- reserved for prioritization

  -- account-level suppression (ABM)
  do_not_contact           boolean not null default false,
  suppression_reason       text,

  -- lineage back to the staging table
  origin                   text,                 -- 'icp_list' | 'derived_from_contact'
  legacy_company_id        text,
  legacy_master_key        text,
  source_master_id         uuid,                 -- outbound_leads_master.id (ICP rows)

  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now()
);

-- Identity: a domain (when present) maps to exactly one company; same for
-- linkedin_url. Partial uniques so the many NULL-domain ICP rows don't collide.
create unique index if not exists companies_domain_key
  on companies (domain) where domain is not null;
create unique index if not exists companies_linkedin_key
  on companies (linkedin_url) where linkedin_url is not null;

create index if not exists companies_industry_idx    on companies (industry);
create index if not exists companies_size_idx        on companies (size_bucket);
create index if not exists companies_niche_idx       on companies (niche);
create index if not exists companies_dnc_idx         on companies (do_not_contact);
create index if not exists companies_name_trgm_idx   on companies using gin (lower(name) gin_trgm_ops);

drop trigger if exists trg_companies_updated_at on companies;
create trigger trg_companies_updated_at before update on companies
  for each row execute function set_updated_at();

-- -----------------------------------------------------------------------------
-- contacts — person level (one row per person), linked to a company
-- -----------------------------------------------------------------------------
create table if not exists contacts (
  id                       uuid primary key default gen_random_uuid(),
  company_id               uuid references companies (id) on delete set null,

  -- person
  first_name               text,
  last_name                text,
  full_name                text,
  title                    text,
  headline                 text,
  seniority                text,
  department               text,

  -- contactability
  email                    text,
  all_emails               text,
  email_domain             text,
  email_provider           text,
  email_status             text,
  email_security_gateway_provider text,
  mobile_phone             text,
  linkedin_url             text,
  ai_ark_people_id         text,

  -- location (person)
  location                 text,
  country                  text,
  state                    text,
  city                     text,

  -- outbound state (per-contact). NOTE: phase 2 moves the message bodies and
  -- touch history into dedicated sequence/touch tables; kept flat for now.
  campaign_name            text,
  lead_status              text,
  interest_status          text,
  outbound_status          text,
  last_contacted_from      text,
  last_contacted_at        timestamptz,
  last_responded_at        timestamptz,
  next_contact_at          timestamptz,
  recontact_after_days     integer,
  contact_attempt_count    integer not null default 0,
  bounce_count             integer not null default 0,
  do_not_contact           boolean not null default false,
  pause_until              timestamptz,
  needs_email_enrichment   boolean not null default false,

  outbound_initial_subject     text,
  outbound_initial_body        text,
  outbound_follow_up_1_body    text,
  outbound_follow_up_2_body    text,

  tags                     text[],

  -- lineage back to the staging table
  dedupe_basis             text,
  contact_key              text,
  legacy_contact_id        text,
  legacy_master_key        text,
  source_master_id         uuid,                 -- outbound_leads_master.id

  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now()
);

-- One contact per email (case-insensitive). Verified 0 dup emails at design time.
create unique index if not exists contacts_email_key
  on contacts (lower(email)) where email is not null;
create unique index if not exists contacts_linkedin_key
  on contacts (linkedin_url) where linkedin_url is not null;

create index if not exists contacts_company_idx        on contacts (company_id);
create index if not exists contacts_outbound_status_idx on contacts (outbound_status);
create index if not exists contacts_next_contact_idx    on contacts (next_contact_at);
create index if not exists contacts_email_status_idx    on contacts (email_status);
create index if not exists contacts_dnc_idx             on contacts (do_not_contact);

drop trigger if exists trg_contacts_updated_at on contacts;
create trigger trg_contacts_updated_at before update on contacts
  for each row execute function set_updated_at();

-- -----------------------------------------------------------------------------
-- Convenience view: contacts flattened with their company firmographics.
-- This replaces the "company_* columns copied onto every contact" pattern —
-- the data is joined live instead of duplicated.
-- -----------------------------------------------------------------------------
create or replace view contacts_enriched as
select
  c.*,
  co.name          as company_name,
  co.domain        as company_domain,
  co.industry      as company_industry,
  co.size_bucket   as company_size,
  co.linkedin_url  as company_linkedin,
  co.niche         as company_niche,
  co.do_not_contact as company_do_not_contact
from contacts c
left join companies co on co.id = c.company_id;

-- -----------------------------------------------------------------------------
-- Security: enable RLS on the new tables (deny-by-default). The service_role
-- key bypasses RLS, so backend skills keep working. Front-end (authenticated)
-- policies are intentionally deferred to a follow-up migration.
-- -----------------------------------------------------------------------------
alter table companies enable row level security;
alter table contacts  enable row level security;

comment on table companies is 'Account master. One row per company; dedupe on domain then linkedin_url. Built from outbound_leads_master (raw/staging).';
comment on table contacts  is 'Person level. FK company_id -> companies.id. Firmographics come via the FK, not copied. Built from outbound_leads_master (raw/staging).';
comment on view  contacts_enriched is 'Contacts joined to their company firmographics (replaces the old denormalized company_* columns).';

commit;
