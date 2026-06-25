#!/usr/bin/env python3
"""Fase B — consolidate free-text verticals into a closed 'broad' taxonomy.

Two inputs feed companies.vertical_broad:
  1. Companies WITH a domain (enriched by parallel_enrich.py): their free-text
     parallel_cat.vertical was classified into the taxonomy by subagents, one
     batch each, producing mapeo_N.json files ({vertical_cruda: vertical_broad}).
     This script merges those files and applies them by joining on subniche.
  2. Companies WITHOUT a domain (no site for Parallel to read): classified here
     directly from their LinkedIn `industry` via keyword rules (lower quality ->
     needs_company_review=true).

Idempotent and non-destructive. Env: SUPABASE_URL, SUPABASE_TOKEN, MAPS_DIR
(folder with mapeo_*.json + lote_*.json, default '.').

TAXONOMY (18): Automotriz | Manufactura/Industrial | Logística y Transporte |
Software/TI | Salud y Farma | Alimentos y Bebidas | RRHH/Talento | Energía |
Construcción/Inmobiliario | Finanzas/Seguros | Retail/Consumo | Agroindustria |
Química | Servicios profesionales | Educación | Telecom/Medios | Gobierno/ONG |
Otros   (+ 'Sin clasificar' for Morado / unknown)."""
import os, json, glob, unicodedata, subprocess, urllib.parse
from collections import Counter

SUPA = os.environ['SUPABASE_URL']; STOK = os.environ['SUPABASE_TOKEN']
REF = urllib.parse.urlparse(SUPA).hostname.split('.')[0]
SQL_URL = f"https://api.supabase.com/v1/projects/{REF}/database/query"
MAPS_DIR = os.environ.get("MAPS_DIR", ".")

TAXONOMY = ["Automotriz", "Manufactura/Industrial", "Logística y Transporte", "Software/TI",
            "Salud y Farma", "Alimentos y Bebidas", "RRHH/Talento", "Energía",
            "Construcción/Inmobiliario", "Finanzas/Seguros", "Retail/Consumo", "Agroindustria",
            "Química", "Servicios profesionales", "Educación", "Telecom/Medios",
            "Gobierno/ONG", "Otros"]
def _norm(s): return ''.join(c for c in unicodedata.normalize('NFD', s.lower())
                             if unicodedata.category(c) != 'Mn').strip()
TAX_NORM = {_norm(t): t for t in TAXONOMY}

def sql(query):
    p = subprocess.run(["curl", "-s", "-w", "\n__H_%{http_code}__", SQL_URL,
        "-H", f"Authorization: Bearer {STOK}", "-H", "Content-Type: application/json",
        "--data-binary", "@-"], input=json.dumps({"query": query}), capture_output=True, text=True)
    o = p.stdout; code = None
    if "\n__H_" in o:
        o, _, t = o.rpartition("\n__H_"); code = t.replace("__", "").strip()
    try: return code, json.loads(o)
    except Exception: return code, o

def q(s): return "'" + str(s).replace("'", "''") + "'"

def consolidate():
    """Merge subagent mapeo_*.json (validated against lote_*.json keys)."""
    mapping = {}
    for lote_path in sorted(glob.glob(os.path.join(MAPS_DIR, "lote_*.json"))):
        n = lote_path.split("lote_")[-1].split(".")[0]
        mp = json.load(open(os.path.join(MAPS_DIR, f"mapeo_{n}.json")))
        for item in json.load(open(lote_path)):
            v = item["v"]
            b = mp.get(v, "Otros")
            if b not in TAXONOMY:
                b = TAX_NORM.get(_norm(b), "Otros")
            mapping[v] = b
    return mapping

def apply_with_domain(mapping):
    items = list(mapping.items())
    for k in range(0, len(items), 500):
        vals = ",".join(f"({q(c)},{q(b)})" for c, b in items[k:k+500])
        sql(f"update companies as c set vertical_broad=v.broad, updated_at=now() "
            f"from (values {vals}) as v(cruda,broad) "
            f"where c.subniche=v.cruda and c.parallel_cat is not null;")
    sql("update companies set vertical_broad='Sin clasificar' "
        "where subniche='Morado' and parallel_cat is not null;")

def apply_without_domain():
    """Companies without a domain: classify from LinkedIn industry (keyword rules)."""
    sql("""update companies set
      vertical_broad = case
        when industry ~* 'human resourc|staffing|recruit|executive search|offshoring' then 'RRHH/Talento'
        when industry ~* 'insurance|financial|accounting|banking' then 'Finanzas/Seguros'
        when industry ~* 'information technology|it services|software|computer' then 'Software/TI'
        when industry ~* 'telecommunication' then 'Telecom/Medios'
        when industry ~* 'advertis|public relations|communications|marketing|entertainment|media' then 'Telecom/Medios'
        when industry ~* 'transport|logistics|supply chain' then 'Logística y Transporte'
        when industry ~* 'construction|real estate' then 'Construcción/Inmobiliario'
        when industry ~* 'retail|consumer' then 'Retail/Consumo'
        when industry ~* 'consulting|training|coaching|operations|professional' then 'Servicios profesionales'
        when industry ~* 'manufactur|industrial|machinery' then 'Manufactura/Industrial'
        when industry ~* 'health|medical|pharma|hospital|biotech' then 'Salud y Farma'
        when industry ~* 'food|beverage|restaurant' then 'Alimentos y Bebidas'
        when industry ~* 'automotive|automobile' then 'Automotriz'
        when industry ~* 'energy|oil|gas|utilities|renewable' then 'Energía'
        when industry ~* 'education|university|e-learning' then 'Educación'
        when industry ~* 'agricultur|farming|agro' then 'Agroindustria'
        when industry ~* 'chemical' then 'Química'
        when industry is null then 'Sin clasificar'
        else 'Otros' end,
      enrichment_source = coalesce(enrichment_source, 'linkedin_industry'),
      needs_company_review = true, updated_at = now()
    where domain is null;""")

if __name__ == "__main__":
    m = consolidate()
    print(f"verticales crudas: {len(m)} | distribucion: {dict(Counter(m.values()).most_common())}")
    apply_with_domain(m)
    apply_without_domain()
    code, rows = sql("select count(*) total, count(vertical_broad) clasificadas, "
                     "count(*) filter (where vertical_broad is null) sin_clasificar from companies;")
    print("cobertura:", rows)
