-- Separate the strength of the hiring signal from account, employer and geography fit.
-- A job's location is informational and must never be used as proof of company headquarters.

alter table public.job_signals
  add column if not exists job_location_requirement text,
  add column if not exists company_address_country_code text,
  add column if not exists company_hq_country text,
  add column if not exists company_region_fit text not null default 'unreviewed'
    check (company_region_fit in ('unreviewed', 'latam', 'non_latam', 'uncertain')),
  add column if not exists signal_fit text not null default 'unreviewed'
    check (signal_fit in ('unreviewed', 'high', 'medium', 'low', 'no_signal')),
  add column if not exists account_fit text not null default 'unreviewed'
    check (account_fit in ('unreviewed', 'high', 'medium', 'low', 'no_fit')),
  add column if not exists prospecting_scope text not null default 'unknown'
    check (prospecting_scope in ('unknown', 'national', 'regional_latam', 'international', 'mixed')),
  add column if not exists prospecting_markets jsonb not null default '[]'::jsonb
    check (jsonb_typeof(prospecting_markets) = 'array'),
  add column if not exists outbound_motions jsonb not null default '[]'::jsonb
    check (jsonb_typeof(outbound_motions) = 'array'),
  add column if not exists employer_confidence text not null default 'unreviewed'
    check (employer_confidence in ('unreviewed', 'verified', 'likely', 'hidden', 'uncertain')),
  add column if not exists campaign_action text not null default 'review'
    check (campaign_action in ('review', 'contact', 'hold', 'exclude'));

-- Preserve the useful part of prior decisions without pretending that a prior overall
-- rejection proves there was no outbound signal.
update public.job_signals
set signal_fit = fit
where signal_fit = 'unreviewed'
  and fit in ('high', 'medium');

update public.job_signals
set employer_confidence = 'hidden',
    campaign_action = 'hold'
where prefilter_reasons ? 'hidden_employer';

update public.job_signals
set company_address_country_code = upper(raw_payload->'companyAddress'->>'addressCountry')
where company_address_country_code is null
  and jsonb_typeof(raw_payload->'companyAddress') = 'object'
  and nullif(raw_payload->'companyAddress'->>'addressCountry', '') is not null;

-- The v0.1 sample mixed dimensions, so keep its evidence but return it to the review queue.
update public.job_signals
set pipeline_status = 'ready_for_analysis',
    needs_human_review = true,
    account_fit = 'unreviewed',
    company_region_fit = 'unreviewed',
    prospecting_scope = 'unknown',
    prospecting_markets = '[]'::jsonb,
    outbound_motions = '[]'::jsonb,
    campaign_action = case
      when prefilter_reasons ? 'hidden_employer' then 'hold'
      else 'review'
    end,
    updated_at = now()
where analysis_version = 'job-signal-rubric-v0.1-sample';

-- Correct the former Mexico-only assumption without hardcoding a generated row id.
update public.job_signals
set fit = 'unreviewed',
    fit_confidence = null,
    signal_fit = 'high',
    job_location_requirement = 'Colombia',
    employer_confidence = 'likely',
    campaign_action = 'review',
    pipeline_status = 'ready_for_analysis',
    analysis_reason = 'La vacante contiene una señal outbound fuerte. El requisito de residencia en Colombia no la excluye; falta verificar si la empresa está basada en LATAM.',
    analysis_version = 'job-signal-market-v2-correction',
    analyzed_at = now(),
    needs_human_review = true,
    updated_at = now()
where workspace = 'unprospect'
  and source = 'linkedin_jobs'
  and prefilter_reasons ? 'geo_mismatch:Colombia';

create index if not exists idx_job_signals_market_review
  on public.job_signals (
    workspace,
    campaign_action,
    company_region_fit,
    signal_fit,
    harvested_at desc
  );

comment on column public.job_signals.signal_fit is
  'Strength of the outbound/new-logo hiring signal, independent from account eligibility.';
comment on column public.job_signals.company_region_fit is
  'Whether the employer is based in LATAM; job location alone is never sufficient evidence.';
comment on column public.job_signals.prospecting_scope is
  'Market scope named or inferred from the job: national, LATAM regional, international or mixed.';
comment on column public.job_signals.campaign_action is
  'Operational action after all dimensions are reviewed; distinct from signal_fit.';
