"""Centraliza Supabase: construye las tablas canónicas `company` y `contact`
desde las tablas crudas (staging), fusionando por dominio normalizado.

Fuentes (prioridad de firmografía declarada en docs/SUPABASE-ARCHITECTURE.md):
  - list_companies (ocean|aiark)  -> base firmográfica + staff_linkedin + señal GTM
  - companies (parallel)          -> employee_count/industry duros + linkedin_url
  - company_gtm_profiles / b2b_classification -> business_model / outbound_fit
  - contacts                      -> personas, religadas POR DOMINIO

Idempotente: TRUNCATE + rebuild de las tablas derivadas en cada corrida. Las tablas
crudas NO se tocan. Corre server-side via la Management API ($SUPABASE_TOKEN); no
transfiere las ~70k filas por red.

Uso:
  python scripts/centralize_supabase.py --apply     # aplica DDL 012 + ETL + reporte
  python scripts/centralize_supabase.py             # solo reporte (no escribe)
"""
import argparse
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(__file__)
DDL_PATH = os.path.join(HERE, "..", "supabase", "migrations",
                        "012_canonical_company_contact.sql")

# Expresión de normalización de dominio inline (misma lógica que norm_domain()).
ND = ("lower(split_part(split_part("
      "regexp_replace(regexp_replace(trim({c}),'^https?://',''),'^www\\.',''),"
      "'/',1),':',1))")


def sql(query):
    base = os.environ["SUPABASE_URL"].rstrip("/")
    tok = os.environ["SUPABASE_TOKEN"]
    ref = base.split("//")[1].split(".")[0]
    url = f"https://api.supabase.com/v1/projects/{ref}/database/query"
    req = urllib.request.Request(
        url, data=json.dumps({"query": query}).encode(), method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {tok}", "User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode())


# ── ETL: llenado de `company` ────────────────────────────────────────────────
# Paso 1: base desde list_companies, agregando duplicados por dominio normalizado.
ETL_COMPANY_FROM_LIST = f"""
truncate table contact;
truncate table company cascade;

with lc as (
  select {ND.format(c='domain')} as nd, *
  from list_companies
  where {ND.format(c='domain')} like '%.%'
),
agg as (
  select nd,
    max(staff_linkedin)   as employees_on_linkedin,
    max(sales_count)      as sales_count,
    max(marketing_count)  as marketing_count,
    array_remove(array_agg(distinct niche), null)  as niches,
    array_remove(array_agg(distinct source), null) as sources
  from lc group by nd
),
best as (  -- fila representativa por dominio: la de mayor headcount / más reciente
  select distinct on (nd) nd, name, company_size, sales_bucket, marketing_bucket, meta
  from lc
  order by nd, staff_linkedin desc nulls last, updated_at desc nulls last
)
insert into company (
  domain, name, description, linkedin_url, has_linkedin, employees_on_linkedin,
  size_bucket, industry, revenue_range, founded_year, hq_country, hq_state, hq_city,
  sales_count, sales_bucket, marketing_count, sources, niches, meta)
select
  a.nd,
  b.name,
  b.meta->>'description',
  nullif(b.meta->>'linkedin',''),
  (nullif(b.meta->>'linkedin','') is not null),
  a.employees_on_linkedin,
  b.company_size,
  coalesce(b.meta->>'industry_label', b.meta->>'linkedin_industry', b.meta->>'industry_categories'),
  b.meta->>'revenue_range',
  coalesce(b.meta->>'founded_year', b.meta->>'year_founded'),
  b.meta->>'country',
  b.meta->>'state',
  b.meta->>'city',
  a.sales_count, b.sales_bucket, a.marketing_count,
  a.sources, a.niches, b.meta
from agg a join best b using (nd);
"""

# Paso 2: fusionar universo A (companies/parallel). Rellena huecos y marca fuente parallel.
ETL_MERGE_COMPANIES = f"""
with co as (
  select distinct on ({ND.format(c='domain')}) {ND.format(c='domain')} as nd, *
  from companies
  where {ND.format(c='domain')} like '%.%'
  order by {ND.format(c='domain')}, updated_at desc nulls last
)
insert into company (
  domain, name, website, description, linkedin_url, has_linkedin, employee_count,
  size_bucket, industry, hq_country, hq_state, hq_city, sources, created_at)
select
  co.nd, co.name, co.website, coalesce(co.description, co.description_short),
  co.linkedin_url, (co.linkedin_url is not null), co.employee_count,
  co.size_bucket, co.industry, co.hq_country, co.hq_state,
  co.hq_city, array['parallel'], co.created_at
from co
on conflict (domain) do update set
  name             = coalesce(company.name, excluded.name),
  website          = coalesce(company.website, excluded.website),
  description      = coalesce(company.description, excluded.description),
  linkedin_url     = coalesce(company.linkedin_url, excluded.linkedin_url),
  has_linkedin     = company.has_linkedin or excluded.has_linkedin,
  employee_count   = coalesce(excluded.employee_count, company.employee_count),
  size_bucket      = coalesce(company.size_bucket, excluded.size_bucket),
  industry         = coalesce(company.industry, excluded.industry),
  hq_country       = coalesce(company.hq_country, excluded.hq_country),
  hq_state         = coalesce(company.hq_state, excluded.hq_state),
  hq_city          = coalesce(company.hq_city, excluded.hq_city),
  sources          = (select array(select distinct unnest(company.sources || excluded.sources))),
  updated_at       = now();
"""

# Paso 3: clasificación B2B/fit desde company_gtm_profiles (crawl+clasificación).
ETL_MERGE_PROFILES = f"""
with p as (
  select distinct on ({ND.format(c='domain')}) {ND.format(c='domain')} as nd, *
  from company_gtm_profiles
  where {ND.format(c='domain')} like '%.%'
  order by {ND.format(c='domain')}, updated_at desc nulls last
)
insert into company (domain, business_model, is_b2b, outbound_fit, what_they_sell,
                     primary_customer, classified, crawled, sources)
select p.nd, p.business_model, p.is_b2b, p.outbound_fit, p.what_they_sell,
       p.primary_customer, (p.profile_status = 'accepted'), p.source_crawl_ok,
       array['crawl']
from p
on conflict (domain) do update set
  business_model   = coalesce(excluded.business_model, company.business_model),
  is_b2b           = coalesce(excluded.is_b2b, company.is_b2b),
  outbound_fit     = coalesce(excluded.outbound_fit, company.outbound_fit),
  what_they_sell   = coalesce(excluded.what_they_sell, company.what_they_sell),
  primary_customer = coalesce(excluded.primary_customer, company.primary_customer),
  classified       = company.classified or excluded.classified,
  crawled          = company.crawled or excluded.crawled,
  sources          = (select array(select distinct unnest(company.sources || excluded.sources))),
  updated_at       = now();
"""

# Paso 3b: crawl presente aunque no haya perfil aceptado (site_crawls).
ETL_MARK_CRAWLED = f"""
update company c set crawled = true
from (select distinct {ND.format(c='domain')} as nd from site_crawls where ok) s
where s.nd = c.domain and c.crawled is not true;
"""

# ── ETL: llenado de `contact`, religado por dominio ──────────────────────────
ETL_CONTACTS = f"""
insert into contact (company_domain, full_name, first_name, last_name, title,
  headline, seniority, department, email, email_status, linkedin_url, mobile_phone,
  location, country, state, city, ai_ark_people_id, source, legacy_contact_id)
select
  d.nd, ct.full_name, ct.first_name, ct.last_name, ct.title, ct.headline,
  ct.seniority, ct.department, ct.email, ct.email_status, ct.linkedin_url,
  ct.mobile_phone, ct.location, ct.country, ct.state, ct.city, ct.ai_ark_people_id,
  coalesce(ct.dedupe_basis, 'ai_ark'), ct.id
from contacts ct
join lateral (
  select coalesce(
    (select {ND.format(c='co.domain')} from companies co where co.id = ct.company_id),
    {ND.format(c='ct.email_domain')}
  ) as nd
) d on true
where d.nd like '%.%'
  and exists (select 1 from company c where c.domain = d.nd);
"""

# Paso 5: back-fill de señales derivadas de contactos hacia company.
ETL_BACKFILL_CONTACT_SIGNALS = """
with agg as (
  select company_domain,
         count(*)                                        as n,
         count(*) filter (where linkedin_url is not null) as n_li
  from contact group by company_domain
)
update company c set
  has_contacts      = true,
  linkedin_contacts = agg.n_li
from agg
where agg.company_domain = c.domain;
"""

REPORT = """
select 'company (canónica)'      as metric, count(*)::text as value from company
union all select 'con LinkedIn URL',            count(*)::text from company where has_linkedin
union all select 'con headcount LinkedIn (>0)', count(*)::text from company where employees_on_linkedin > 0
union all select 'con contactos con LinkedIn',  count(*)::text from company where linkedin_contacts > 0
union all select 'con employee_count duro',     count(*)::text from company where employee_count is not null
union all select 'con >=1 contacto',            count(*)::text from company where has_contacts
union all select 'crawleadas',                  count(*)::text from company where crawled
union all select 'clasificadas B2B/fit',        count(*)::text from company where classified
union all select 'B2B',                         count(*)::text from company where is_b2b
union all select 'outbound_fit high/medium',    count(*)::text from company where outbound_fit in ('high','medium')
union all select 'contact (personas)',          count(*)::text from contact
union all select '  con email',                 count(*)::text from contact where email is not null
union all select '  con LinkedIn',              count(*)::text from contact where linkedin_url is not null
union all select 'v_outbound_ready',            count(*)::text from v_outbound_ready;
"""


def run_etl():
    steps = [
        ("DDL 012 (norm_domain + company + contact + vistas)", open(DDL_PATH).read()),
        ("company <- list_companies (agregado por dominio)", ETL_COMPANY_FROM_LIST),
        ("company <- companies (parallel, rellena huecos)", ETL_MERGE_COMPANIES),
        ("company <- company_gtm_profiles (clasificación)", ETL_MERGE_PROFILES),
        ("company.crawled <- site_crawls", ETL_MARK_CRAWLED),
        ("contact <- contacts (religado por dominio)", ETL_CONTACTS),
        ("company back-fill señales de contacto", ETL_BACKFILL_CONTACT_SIGNALS),
    ]
    for name, q in steps:
        sql(q)
        print(f"  ✓ {name}", flush=True)


def report():
    rows = sql(REPORT)
    print("\n── Cobertura canónica ──")
    for r in rows:
        print(f"  {r['metric']:32} {r['value']:>8}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="aplica DDL + ETL (escribe en Supabase). Sin esto, solo reporte.")
    a = ap.parse_args()
    if a.apply:
        print("Aplicando centralización (idempotente)…")
        run_etl()
    report()


if __name__ == "__main__":
    main()
