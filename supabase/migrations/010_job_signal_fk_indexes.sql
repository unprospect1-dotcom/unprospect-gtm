-- Cover foreign keys used by cleanup and joins.
create index if not exists idx_job_signals_run_id
  on public.job_signals (run_id);
create index if not exists idx_job_signals_company_id
  on public.job_signals (company_id);
