-- =============================================================================
-- 0099_rollback.sql
-- Undo 0001 + 0002. Drops ONLY the new objects. outbound_leads_master and the
-- rest of the existing schema are untouched. Run only if you want to start over.
-- =============================================================================

begin;

drop view  if exists contacts_enriched;
drop table if exists contacts;
drop table if exists companies;

drop function if exists set_updated_at();
drop function if exists norm_domain(text);

commit;
