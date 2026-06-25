-- Phase 3 (enrichment) — dedicated column for Parallel Task API category output.
--
-- Holds the structured free-text classification produced by db/enrich/parallel_enrich.py:
--   { categoria, oferta, vertical, tamano, sources[], field_confidence{},
--     anchored_to_domain, source_policy[], run_id, processor, generated_at }
--
-- Why a dedicated column instead of reusing description_basis: description_basis
-- is polymorphic — the prior ICP enrichment stored a jsonb *array* of citation
-- objects there, so merging an object under a key is unsafe. parallel_cat is
-- always a clean object and is the idempotency marker for the enrichment job
-- (rows are processed only while parallel_cat IS NULL).
alter table companies add column if not exists parallel_cat jsonb;

comment on column companies.parallel_cat is
  'Parallel Task API enrichment (categoria/oferta/vertical/tamano + sources/confidence). Written by db/enrich/parallel_enrich.py.';
