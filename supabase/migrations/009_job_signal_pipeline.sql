-- Bandeja durable para señales de contratación.
-- Conserva el posting completo; los paquetes cortos para LLM son derivados y reemplazables.

create table if not exists public.job_signal_runs (
  id uuid primary key default gen_random_uuid(),
  workspace text not null default 'unprospect',
  source text not null default 'linkedin_jobs',
  provider_run_id text,
  provider_dataset_id text,
  status text not null default 'started'
    check (status in ('started', 'succeeded', 'failed', 'timed_out', 'aborted')),
  keyword_count integer not null default 0 check (keyword_count >= 0),
  harvested_count integer not null default 0 check (harvested_count >= 0),
  unique_count integer not null default 0 check (unique_count >= 0),
  estimated_cost_usd numeric(10, 4),
  actual_cost_usd numeric(10, 4),
  config_snapshot jsonb not null default '{}'::jsonb,
  error text,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.job_signals (
  id uuid primary key default gen_random_uuid(),
  workspace text not null default 'unprospect',
  source text not null default 'linkedin_jobs',
  source_job_id text not null,
  run_id uuid references public.job_signal_runs(id) on delete set null,

  job_url text,
  role_title text,
  job_function text,
  seniority text,
  employment_type text,
  location text,
  posted_at timestamptz,
  harvested_at timestamptz not null default now(),
  description_text text,
  description_hash text,
  analysis_excerpt text,

  company_id uuid references public.companies(id) on delete set null,
  company_name text,
  company_domain text,
  company_website text,
  company_linkedin_url text,
  company_logo_url text,
  company_employee_count integer,
  company_industries text,

  prefilter_priority text not null default 'review'
    check (prefilter_priority in ('high', 'medium', 'low', 'review')),
  prefilter_reasons jsonb not null default '[]'::jsonb,
  fit text not null default 'unreviewed'
    check (fit in ('unreviewed', 'high', 'medium', 'no_fit', 'excluded')),
  fit_confidence numeric(4, 3) check (fit_confidence between 0 and 1),
  extracted_problem text,
  evidence_quotes jsonb not null default '[]'::jsonb,
  analysis_reason text,
  analysis_version text,
  analyzed_at timestamptz,
  needs_human_review boolean not null default true,

  buyer_role_hint text,
  contact_id uuid references public.contacts(id) on delete set null,
  contact_channel text check (contact_channel in ('email', 'linkedin')),
  contact_email_status text,
  contact_matched_at timestamptz,

  copy_status text not null default 'not_started'
    check (copy_status in ('not_started', 'drafted', 'approved', 'rejected')),
  email_subject text,
  email_1_body text,
  email_2_body text,
  lead_magnet_brief jsonb,
  linkedin_brief jsonb,

  pipeline_status text not null default 'discovered'
    check (pipeline_status in (
      'discovered', 'ready_for_analysis', 'qualified', 'not_fit',
      'ready_for_contact', 'ready_for_copy', 'draft_ready',
      'approved', 'sent', 'rejected', 'error'
    )),
  approved_at timestamptz,
  sent_at timestamptz,
  raw_payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (workspace, source, source_job_id)
);

create index if not exists idx_job_signals_review_queue
  on public.job_signals (workspace, pipeline_status, prefilter_priority, harvested_at desc);
create index if not exists idx_job_signals_company_domain
  on public.job_signals (workspace, company_domain);
create index if not exists idx_job_signals_contact
  on public.job_signals (contact_id) where contact_id is not null;
create index if not exists idx_job_signal_runs_started
  on public.job_signal_runs (workspace, started_at desc);

alter table public.job_signal_runs enable row level security;
alter table public.job_signals enable row level security;

revoke all on table public.job_signal_runs from anon, authenticated;
revoke all on table public.job_signals from anon, authenticated;
grant all on table public.job_signal_runs to service_role;
grant all on table public.job_signals to service_role;

comment on table public.job_signals is
  'Weekly hiring signals. Full source is retained; copy is blank until explicitly generated and approved.';
