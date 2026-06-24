-- =============================================================================
-- 0002_backfill_from_master.sql
-- Populate companies + contacts from outbound_leads_master (the raw/staging
-- table). NON-DESTRUCTIVE: only reads from master, never modifies it.
-- IDEMPOTENT: re-running skips rows that already exist (by natural key / id).
--
-- Expected result on current data (8,636 staging rows):
--   companies: 6,654  (3,331 from ICP list + 3,323 derived from contact domains)
--   contacts : 5,305  (5,212 linked to a company, 93 with NULL company_id)
-- =============================================================================

begin;

-- -----------------------------------------------------------------------------
-- STEP 1 — companies from the ICP list (record_type = 'company').
-- Identity key: domain when present, else linkedin_url. Deduped within source.
-- -----------------------------------------------------------------------------
insert into companies (
  domain, linkedin_url, name, website,
  industry, size_bucket, employee_count, company_type, primary_phone, founding_year, annual_revenue,
  description, description_short, description_source_urls, description_basis,
  enrichment_status, enrichment_source, enrichment_task_group_id, enrichment_task_run_id, enrichment_error, enriched_at,
  needs_company_review,
  hq_location, hq_country, hq_state, hq_city,
  niche, subniche, tags,
  do_not_contact,
  origin, legacy_company_id, legacy_master_key, source_master_id,
  created_at, updated_at
)
select
  s.domain, s.company_linkedin, s.company_name, s.company_website,
  s.company_industry, s.company_size,
  safe_int(s.company_employee_count),
  s.company_type, s.company_primary_phone,
  safe_int(s.company_founding_year),
  s.company_annual_revenue,
  s.company_description, s.company_description_short, s.company_description_source_urls, s.company_description_basis,
  s.parallel_enrichment_status, s.parallel_processor, s.parallel_task_group_id, s.parallel_task_run_id, s.parallel_error, s.parallel_enriched_at,
  coalesce(s.needs_company_review, false),
  s.location, s.country, s.state, s.city,
  s.niche, s.subniche, s.tags,
  coalesce(s.do_not_contact, false),
  'icp_list', s.legacy_company_id, s.master_key, s.id,
  coalesce(s.created_at, now()), now()
from (
  select distinct on (coalesce(norm_domain(company_domain), lower(company_linkedin)))
         *, norm_domain(company_domain) as domain
  from outbound_leads_master
  where record_type = 'company'
  order by coalesce(norm_domain(company_domain), lower(company_linkedin)), created_at nulls last
) s
where not exists (
  select 1 from companies c
  where (s.domain is not null and c.domain = s.domain)
     or (s.company_linkedin is not null and c.linkedin_url = s.company_linkedin)
);

-- -----------------------------------------------------------------------------
-- STEP 2 — companies derived from contact domains not already present.
-- Picks the richest contact row per domain (prefers ones carrying industry/name).
-- -----------------------------------------------------------------------------
insert into companies (
  domain, name, website, industry, size_bucket, employee_count, company_type, primary_phone, founding_year, annual_revenue,
  niche, subniche, tags,
  origin, created_at, updated_at
)
select
  s.domain, s.company_name, s.company_website, s.company_industry, s.company_size,
  safe_int(s.company_employee_count),
  s.company_type, s.company_primary_phone,
  safe_int(s.company_founding_year),
  s.company_annual_revenue,
  s.niche, s.subniche, s.tags,
  'derived_from_contact', coalesce(s.created_at, now()), now()
from (
  select distinct on (norm_domain(company_domain))
         *, norm_domain(company_domain) as domain
  from outbound_leads_master
  where record_type = 'contact' and norm_domain(company_domain) is not null
  order by norm_domain(company_domain),
           (company_industry is not null) desc,
           (company_name is not null) desc,
           created_at nulls last
) s
where not exists (select 1 from companies c where c.domain = s.domain);

-- -----------------------------------------------------------------------------
-- STEP 3 — contacts. Reuses master.id as the contact id (clean 1:1 + idempotent).
-- Resolves company_id by joining the contact's normalized domain to companies.
-- -----------------------------------------------------------------------------
insert into contacts (
  id, company_id,
  first_name, last_name, full_name, title, headline, seniority, department,
  email, all_emails, email_domain, email_provider, email_status, email_security_gateway_provider, mobile_phone, linkedin_url, ai_ark_people_id,
  location, country, state, city,
  campaign_name, lead_status, interest_status, outbound_status, last_contacted_from,
  last_contacted_at, last_responded_at, next_contact_at, recontact_after_days,
  contact_attempt_count, bounce_count, do_not_contact, pause_until, needs_email_enrichment,
  outbound_initial_subject, outbound_initial_body, outbound_follow_up_1_body, outbound_follow_up_2_body,
  tags, dedupe_basis, contact_key, legacy_contact_id, legacy_master_key, source_master_id,
  created_at, updated_at
)
select
  m.id, co.id,
  m.first_name, m.last_name, m.full_name, m.title, m.headline, m.seniority, m.department,
  m.email, m.all_emails, m.email_domain, m.email_provider, m.email_status, m.email_security_gateway_provider, m.mobile_phone, m.contact_linkedin, m.ai_ark_people_id,
  m.location, m.country, m.state, m.city,
  m.campaign_name, m.lead_status, m.interest_status, m.outbound_status, m.last_contacted_from,
  m.last_contacted_at, m.last_responded_at, m.next_contact_at, m.recontact_after_days,
  coalesce(m.contact_attempt_count, 0), coalesce(m.bounce_count, 0), coalesce(m.do_not_contact, false), m.pause_until, coalesce(m.needs_email_enrichment, false),
  m.outbound_initial_subject, m.outbound_initial_body, m.outbound_follow_up_1_body, m.outbound_follow_up_2_body,
  m.tags, m.dedupe_basis, m.contact_key, m.legacy_contact_id, m.master_key, m.id,
  coalesce(m.created_at, now()), now()
from outbound_leads_master m
left join companies co on co.domain = norm_domain(m.company_domain)
where m.record_type = 'contact'
  and not exists (select 1 from contacts x where x.id = m.id);

commit;
