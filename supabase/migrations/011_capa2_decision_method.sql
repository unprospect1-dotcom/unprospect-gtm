-- Capa 2 (2026-07-20): el verificador (modelo más fuerte) puede resolver un dudoso cuando
-- difiere de la capa 1 sin cruzar la frontera comercial. Se registra como 'stronger_model'.

alter table company_gtm_profiles drop constraint if exists company_gtm_profiles_decision_method_check;
alter table company_gtm_profiles add constraint company_gtm_profiles_decision_method_check
  check (decision_method is null or decision_method in
         ('consensus','arbiter','human','first_pass_clear','disagreement','stronger_model'));
