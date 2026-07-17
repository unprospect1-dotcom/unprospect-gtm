-- Compact GTM profile for every crawled domain.
-- Source: site_crawls.clean_text. The main table is the current consensus;
-- blind pass outputs live in company_gtm_profile_runs for auditability.

create table if not exists public.company_gtm_profiles (
  domain                    text primary key
    references public.site_crawls(domain)
    on update cascade
    on delete restrict,

  -- Primary segmentation field. NULL means "not enough evidence", never "no".
  is_b2b                    boolean,
  business_model            text,
  entity_type               text,
  confidence                text,
  b2b_line_present          boolean,

  what_they_sell            text,
  primary_customer          text,
  icp_company_type          text,
  icp_industries            text[] not null default '{}',
  icp_buyer                 text,
  icp_geographies           text[] not null default '{}',

  sales_economics           text,
  outbound_fit              text,
  outbound_scope            text,
  outbound_reason           text,
  evidence                  text[] not null default '{}',

  profile_status            text not null default 'pending',
  profileability_reason     text,
  needs_review              boolean not null default false,
  consensus_fields          text[] not null default '{}',
  attempt_count             integer not null default 0,
  claimed_at                timestamptz,
  last_error                text,

  source_crawl_ok           boolean not null default false,
  source_clean_chars        integer not null default 0,
  current_source_hash       text,
  profiled_source_hash      text,
  source_crawled_at         timestamptz,

  rubric_version            text not null default 'gtm-company-profile-v1',
  rubric_hash               text,
  producer_model            text,
  verifier_model            text,
  decision_method           text,
  profiled_at               timestamptz,
  created_at                timestamptz not null default now(),
  updated_at                timestamptz not null default now(),

  constraint company_gtm_profiles_business_model_check
    check (business_model is null or business_model in ('b2b', 'b2c', 'mixed', 'noncommercial', 'unclear')),
  constraint company_gtm_profiles_entity_type_check
    check (entity_type is null or entity_type in ('company', 'government', 'education', 'nonprofit', 'media_or_directory', 'unclear')),
  constraint company_gtm_profiles_confidence_check
    check (confidence is null or confidence in ('high', 'medium', 'low')),
  constraint company_gtm_profiles_sales_economics_check
    check (sales_economics is null or sales_economics in ('strong', 'plausible', 'weak', 'not_applicable', 'unclear')),
  constraint company_gtm_profiles_outbound_fit_check
    check (outbound_fit is null or outbound_fit in ('high', 'medium', 'low', 'unclear')),
  constraint company_gtm_profiles_outbound_scope_check
    check (outbound_scope is null or outbound_scope in ('companywide', 'b2b_line_only', 'none', 'unclear')),
  constraint company_gtm_profiles_status_check
    check (profile_status in ('pending', 'processing', 'needs_review', 'accepted', 'failed', 'not_profileable', 'stale')),
  constraint company_gtm_profiles_profileability_reason_check
    check (profileability_reason is null or profileability_reason in ('no_clean_text', 'thin_text')),
  constraint company_gtm_profiles_decision_method_check
    check (decision_method is null or decision_method in ('consensus', 'arbiter', 'human')),
  constraint company_gtm_profiles_attempt_count_check
    check (attempt_count >= 0),
  constraint company_gtm_profiles_evidence_count_check
    check (cardinality(evidence) <= 2),
  constraint company_gtm_profiles_current_hash_format_check
    check (current_source_hash is null or current_source_hash ~ '^[0-9a-f]{64}$'),
  constraint company_gtm_profiles_profiled_hash_format_check
    check (profiled_source_hash is null or profiled_source_hash ~ '^[0-9a-f]{64}$'),
  constraint company_gtm_profiles_rubric_hash_format_check
    check (rubric_hash is null or rubric_hash ~ '^[0-9a-f]{64}$'),
  constraint company_gtm_profiles_b2b_consistency_check
    check (
      (business_model is null and is_b2b is null)
      or (business_model in ('b2b', 'mixed') and is_b2b is true)
      or (business_model in ('b2c', 'noncommercial') and is_b2b is false)
      or (business_model = 'unclear' and is_b2b is null)
    ),
  constraint company_gtm_profiles_accepted_complete_check
    check (
      profile_status <> 'accepted'
      or (
        business_model is not null
        and entity_type is not null
        and confidence is not null
        and b2b_line_present is not null
        and sales_economics is not null
        and outbound_fit is not null
        and outbound_scope is not null
        and current_source_hash is not null
        and profiled_source_hash = current_source_hash
        and rubric_hash is not null
        and producer_model is not null
        and decision_method is not null
        and profiled_at is not null
      )
    ),
  constraint company_gtm_profiles_accepted_relationships_check
    check (
      profile_status <> 'accepted'
      or (
        (business_model not in ('b2b', 'mixed') or b2b_line_present is true)
        and (business_model <> 'noncommercial' or sales_economics = 'not_applicable')
        and (outbound_scope not in ('companywide', 'b2b_line_only') or b2b_line_present is true)
        and (outbound_scope <> 'none' or b2b_line_present is false)
      )
    )
);

comment on table public.company_gtm_profiles is
  'Current evidence-backed B2B, ICP and outbound consensus for every site_crawls domain.';
comment on column public.company_gtm_profiles.is_b2b is
  'TRUE = business_model is B2B or mixed; FALSE = B2C or noncommercial; NULL = unclear/unprofiled.';
comment on column public.company_gtm_profiles.b2b_line_present is
  'Whether any economically meaningful B2B line is supported by evidence.';
comment on column public.company_gtm_profiles.evidence is
  'At most two literal substrings from site_crawls.clean_text.';

create table if not exists public.company_gtm_profile_runs (
  id                        bigint generated always as identity primary key,
  domain                    text not null
    references public.company_gtm_profiles(domain)
    on update cascade
    on delete cascade,
  pass_number               smallint not null check (pass_number in (1, 2, 3)),
  source_hash               text not null check (source_hash ~ '^[0-9a-f]{64}$'),
  rubric_hash               text not null check (rubric_hash ~ '^[0-9a-f]{64}$'),
  model                     text not null,
  provider_run_id           text,
  profile                   jsonb not null,
  is_valid                  boolean not null,
  validation_errors         text[] not null default '{}',
  created_at                timestamptz not null default now()
);

comment on table public.company_gtm_profile_runs is
  'Append-only blind pass and arbiter outputs used to produce company_gtm_profiles consensus.';

alter table public.company_gtm_profiles enable row level security;
alter table public.company_gtm_profile_runs enable row level security;
revoke all on table public.company_gtm_profiles from public, anon, authenticated;
revoke all on table public.company_gtm_profile_runs from public, anon, authenticated;
grant select, insert, update on table public.company_gtm_profiles to service_role;
grant select, insert on table public.company_gtm_profile_runs to service_role;

create index if not exists company_gtm_profiles_work_queue_idx
  on public.company_gtm_profiles (profile_status, updated_at, domain)
  where profile_status in ('pending', 'stale', 'failed');
create index if not exists company_gtm_profiles_review_queue_idx
  on public.company_gtm_profiles (updated_at, domain)
  where profile_status = 'needs_review';
create index if not exists company_gtm_profiles_outbound_idx
  on public.company_gtm_profiles (outbound_fit, sales_economics, domain)
  where profile_status = 'accepted' and is_b2b is true;
create index if not exists company_gtm_profiles_icp_industries_idx
  on public.company_gtm_profiles using gin (icp_industries)
  where profile_status = 'accepted';
create index if not exists company_gtm_profile_runs_domain_idx
  on public.company_gtm_profile_runs (domain, source_hash, rubric_hash, pass_number, created_at desc);

insert into public.company_gtm_profiles as existing (
  domain,
  profile_status,
  profileability_reason,
  source_crawl_ok,
  source_clean_chars,
  current_source_hash,
  source_crawled_at
)
select
  sc.domain,
  case
    when length(btrim(coalesce(sc.clean_text, ''))) < 300 then 'not_profileable'
    else 'pending'
  end,
  case
    when length(btrim(coalesce(sc.clean_text, ''))) = 0 then 'no_clean_text'
    when length(btrim(sc.clean_text)) < 300 then 'thin_text'
    else null
  end,
  coalesce(sc.ok, false),
  length(btrim(coalesce(sc.clean_text, ''))),
  case
    when nullif(btrim(sc.clean_text), '') is null then null
    else encode(extensions.digest(sc.clean_text, 'sha256'), 'hex')
  end,
  sc.crawled_at
from public.site_crawls sc
on conflict (domain) do nothing;
