"""Discovery de taxonomía emergente ($0): descubre categorías/subcategorías reales del
universo agrupando lo que las empresas dicen que venden (company.what_they_sell, ya
extraído por el batch previo). No impone nada — deja que los conceptos emerjan.

Método:
  1. Por niche (=industria), junta todos los what_they_sell.
  2. Normaliza (minúsculas, sin acentos), tokeniza en unigramas + bigramas.
  3. Quita stopwords ES y genéricos del dominio.
  4. Rankea por frecuencia → los conceptos dominantes = subcategorías candidatas.
  5. Reporta cada concepto con cuántas empresas lo mencionan (evidencia de tamaño).

Uso: python scripts/discover_taxonomy.py [--niche autotransporte-mx] [--top 12]
"""
import argparse
import json
import os
import re
import unicodedata
import urllib.request
from collections import Counter

STOP = set("""
de la el los las y o a en con para por un una que se su sus del al lo como mas más es son
servicio servicios empresa empresas solucion soluciones solutions nacional internacional
integral integrales cliente clientes venta ventas oferta ofrece brinda proveedor sector
mexico méxico mx nivel alta calidad todo tipo tipos gama linea línea producto productos
""".split())


def norm(t):
    t = unicodedata.normalize("NFKD", (t or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", t)


def tokens(text):
    words = [w for w in norm(text).split() if len(w) > 2 and w not in STOP]
    grams = list(words)
    grams += [f"{a} {b}" for a, b in zip(words, words[1:])]  # bigramas
    return grams


def sql(query):
    base = os.environ["SUPABASE_URL"].rstrip("/")
    tok = os.environ["SUPABASE_TOKEN"]
    ref = base.split("//")[1].split(".")[0]
    url = f"https://api.supabase.com/v1/projects/{ref}/database/query"
    req = urllib.request.Request(
        url, data=json.dumps({"query": query}).encode(), method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {tok}", "User-Agent": "curl/8.5.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode())


def discover(niche, top):
    rows = sql(f"""select what_they_sell wts, count(*) n from company
      where '{niche}' = any(niches) and what_they_sell is not null
      group by 1""")
    total = sum(r["n"] for r in rows)
    # cuenta cada concepto ponderado por # de empresas que usan esa frase
    concept = Counter()
    seen_phrases = {}
    for r in rows:
        for g in set(tokens(r["wts"])):
            concept[g] += r["n"]
            seen_phrases.setdefault(g, r["wts"])
    # los bigramas ganan a los unigramas contenidos (más específicos); filtra redundantes
    ranked = [(c, n) for c, n in concept.most_common(top * 4) if n >= 3]
    print(f"\n{'='*70}\nINDUSTRIA: {niche}   ({total} empresas con what_they_sell)\n{'='*70}")
    print(f"{'concepto emergente':32} {'empresas':>8}   ejemplo")
    shown = 0
    for c, n in ranked:
        if " " not in c and any(c in bg and bg != c and cn >= n * .6
                                for bg, cn in ranked if " " in bg):
            continue  # unigrama ya cubierto por un bigrama fuerte
        print(f"  {c:30} {n:8}   \"{seen_phrases[c][:34]}\"")
        shown += 1
        if shown >= top:
            break


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--niche")
    ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args()
    if a.niche:
        niches = [a.niche]
    else:
        niches = [r["niche"] for r in sql(
            "select unnest(niches) niche, count(*) n from company "
            "where what_they_sell is not null group by 1 order by 2 desc")]
    for n in niches:
        discover(n, a.top)


if __name__ == "__main__":
    main()
