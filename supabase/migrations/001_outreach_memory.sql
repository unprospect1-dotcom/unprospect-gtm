-- Capa de memoria consultable del GTM OS.
-- Responde: ¿a quién contactamos, cuándo, con qué ángulo, y qué respondió?
-- Todas las tablas llevan `workspace` para separar clientes en un solo esquema.

-- Señales de dolor observable sobre la tabla existente de empresas
alter table companies add column if not exists pain_signals jsonb default '{}'::jsonb;
alter table companies add column if not exists pain_segment text;

create index if not exists idx_companies_pain_segment on companies (pain_segment);

-- Ángulos: segmento × dolor × offer × credibilidad
create table if not exists angles (
  id uuid primary key default gen_random_uuid(),
  workspace text not null default 'unprospect',
  slug text not null,
  segment text,
  pain_hypothesis text not null,
  offer text,
  framework text,
  status text not null default 'propuesto', -- propuesto | activo | ganador | quemado
  notes text,
  created_at timestamptz not null default now(),
  unique (workspace, slug)
);

-- Campañas: liga el mundo Instantly con la memoria
create table if not exists campaigns (
  id uuid primary key default gen_random_uuid(),
  workspace text not null default 'unprospect',
  slug text not null,
  instantly_campaign_id text,
  angle_id uuid references angles (id),
  segment text,
  status text not null default 'draft', -- draft | activa | pausada | cerrada
  launched_at timestamptz,
  created_at timestamptz not null default now(),
  unique (workspace, slug)
);

create index if not exists idx_campaigns_instantly on campaigns (instantly_campaign_id);

-- Outreach log: LA fuente de verdad del dedupe. Un registro por envío (lead × step).
-- Regla del sistema: si no está aquí, no pasó.
create table if not exists outreach_log (
  id uuid primary key default gen_random_uuid(),
  workspace text not null default 'unprospect',
  company_id uuid references companies (id),
  lead_email text not null,
  lead_domain text,
  campaign_id uuid references campaigns (id),
  angle_slug text,
  sequence_step int not null default 1,
  channel text not null default 'email',
  sent_at timestamptz not null,
  result text, -- null | opened | replied_positive | replied_negative | bounced | unsubscribed
  created_at timestamptz not null default now()
);

create index if not exists idx_outreach_lead_email on outreach_log (lead_email);
create index if not exists idx_outreach_lead_domain on outreach_log (lead_domain);
create index if not exists idx_outreach_workspace_sent on outreach_log (workspace, sent_at desc);

-- Replies: crudo + clasificación, ligado a campaña y ángulo
create table if not exists replies (
  id uuid primary key default gen_random_uuid(),
  workspace text not null default 'unprospect',
  campaign_id uuid references campaigns (id),
  angle_slug text,
  lead_email text not null,
  lead_domain text,
  replied_at timestamptz,
  body text,
  classification text, -- positive_interesado | positive_timing | referral | objection | negative | ooo_auto
  pain_quote text,     -- frase textual donde el lead describe su dolor
  analyzed_at timestamptz,
  instantly_reply_id text unique,
  created_at timestamptz not null default now()
);

create index if not exists idx_replies_classification on replies (workspace, classification);

-- "¿Cuándo fue la última vez que contactamos a X y con qué ángulo?" en un solo query:
--   select * from v_last_contact where lead_domain = 'empresa.com';
create or replace view v_last_contact as
select distinct on (workspace, lead_email)
  workspace,
  lead_email,
  lead_domain,
  sent_at as last_contacted_at,
  angle_slug as last_angle,
  campaign_id as last_campaign_id,
  sequence_step as last_step,
  result as last_result
from outreach_log
order by workspace, lead_email, sent_at desc;
