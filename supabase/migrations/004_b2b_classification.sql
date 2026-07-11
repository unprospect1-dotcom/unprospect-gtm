-- Clasificación B2B/B2C de empresas crawleadas (input: site_crawls.clean_text).
-- Una fila por dominio. Producida por gtm-classify-b2b (clasificador + verificación).

create table if not exists b2b_classification (
  domain            text primary key,
  label             text,          -- b2b | b2c | mixed | unclear
  confidence        text,          -- high | med | low
  primary_customer  text,          -- a quién le vende, en una frase
  evidence          text,          -- cita textual del clean_text
  reason            text,          -- una frase de justificación
  model             text,          -- modelo/procesador que clasificó (haiku, parallel-lite, ...)

  -- capa de verificación independiente (re-lee SOLO el clean_text)
  verified          boolean not null default false,
  verify_label      text,          -- etiqueta del verificador
  verify_agree      boolean,       -- coincide con label
  verify_note       text,          -- nota si difiere

  classified_at     timestamptz not null default now()
);

create index if not exists b2b_classification_label_idx  on b2b_classification(label);
create index if not exists b2b_classification_verify_idx  on b2b_classification(verify_agree);

-- Join natural con el crawl y el registro SOFOM:
--   site_crawls.domain = b2b_classification.domain = sofoms.domain
