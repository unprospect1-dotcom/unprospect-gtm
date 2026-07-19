-- Schema mínimo 2026-07-18 (decisión de producto): el clasificador masivo responde
-- business_model + outbound_fit + sells + primary_customer + confidence. Las citas
-- (evidence) y reason quedan deprecadas: el control de calidad es la doble pasada ciega.

alter table b2b_classification add column if not exists sells text;          -- qué venden, <=10 palabras
alter table b2b_classification add column if not exists outbound_fit text;   -- high | medium | low | unclear
alter table b2b_classification add column if not exists verify_fit text;     -- outbound_fit del verificador

create index if not exists b2b_classification_fit_idx on b2b_classification(outbound_fit);
