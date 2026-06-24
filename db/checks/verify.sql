-- =============================================================================
-- verify.sql — run AFTER 0001 + 0002 to confirm the migration landed correctly.
-- Each query prints expected vs actual based on the design-time profiling.
-- =============================================================================

-- 1) Row counts. Expect companies = 6,654 and contacts = 5,305.
select 'companies' as tbl, count(*) from companies
union all
select 'contacts',  count(*) from contacts;

-- 2) Company origin split. Expect icp_list ~3,331, derived_from_contact ~3,323.
select origin, count(*) from companies group by origin order by 2 desc;

-- 3) Contact linkage. Expect ~5,212 linked, 93 with NULL company_id.
select
  count(*)                                            as total_contacts,
  count(company_id)                                   as with_company,
  count(*) - count(company_id)                        as without_company
from contacts;

-- 4) No orphan FKs (every company_id must exist in companies). Expect 0.
select count(*) as orphan_company_fks
from contacts c
where c.company_id is not null
  and not exists (select 1 from companies x where x.id = c.company_id);

-- 5) Nothing lost vs staging. Expect contacts == staging contact rows.
select
  (select count(*) from outbound_leads_master where record_type='contact') as staging_contacts,
  (select count(*) from contacts)                                          as migrated_contacts;

-- 6) Top companies by contact count (sanity: energiareal.mx should be ~10).
select co.name, co.domain, count(c.id) as contacts
from companies co
join contacts c on c.company_id = co.id
group by co.id, co.name, co.domain
order by contacts desc
limit 10;

-- 7) Enrichment coverage now centralized on companies (no longer per-contact).
select
  count(*)                                    as companies,
  count(industry)                             as with_industry,
  count(size_bucket)                          as with_size,
  count(description)                          as with_description
from companies;
