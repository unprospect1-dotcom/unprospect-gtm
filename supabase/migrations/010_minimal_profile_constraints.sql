-- Schema mínimo v2 (2026-07-18): un perfil accepted requiere SOLO los 5 campos del
-- clasificador mínimo. Los checks del rubro gordo (entity_type, b2b_line_present,
-- sales_economics, outbound_scope obligatorios) quedan fuera; esas columnas siguen
-- existiendo para perfiles profundos opcionales.

alter table company_gtm_profiles drop constraint if exists company_gtm_profiles_accepted_complete_check;
alter table company_gtm_profiles drop constraint if exists company_gtm_profiles_accepted_relationships_check;
alter table company_gtm_profiles add constraint company_gtm_profiles_accepted_minimal_check
  check (profile_status <> 'accepted' or
         (business_model is not null and outbound_fit is not null and confidence is not null));

alter table company_gtm_profiles drop constraint if exists company_gtm_profiles_decision_method_check;
alter table company_gtm_profiles add constraint company_gtm_profiles_decision_method_check
  check (decision_method is null or decision_method in
         ('consensus','arbiter','human','first_pass_clear','disagreement'));
