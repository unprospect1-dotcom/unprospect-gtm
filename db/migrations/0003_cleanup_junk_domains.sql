-- =============================================================================
-- 0003_cleanup_junk_domains.sql
-- Remove pseudo-companies built from generic / non-identifying domains (social
-- networks, site builders, messaging, free email) and the contacts that hung
-- off them. Those contacts' emails were synthesized from the generic domain
-- (e.g. abonilla@facebook.com) and are not deliverable, so they are deleted too.
--
-- PREVENTION lives in 0001: norm_domain() now returns NULL for these domains
-- (via is_generic_domain), so the backfill no longer mints such companies.
-- This migration only cleans rows created before that fix.
--
-- IDEMPOTENT: re-running deletes nothing new. Requires is_generic_domain()
-- from 0001 (re-apply 0001 before this if needed).
-- =============================================================================

begin;

-- 1) Delete contacts attached to junk-domain companies (emails not deliverable).
delete from contacts
where company_id in (select id from companies where is_generic_domain(domain));

-- 2) Delete the junk-domain companies themselves.
delete from companies
where is_generic_domain(domain);

commit;
