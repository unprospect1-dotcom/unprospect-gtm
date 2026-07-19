#!/usr/bin/env python3
"""Golden gate de modelos para el clasificador mínimo. Corre los dominios VERIFICADOS
(b2b_classification verified=true y verify_agree=true) por cada modelo candidato de
OpenAI y mide acuerdo. Regla del repo: gana el más barato con >=90% en casos claros.

  OPENAI_API_KEY=... python3 golden_eval.py --models gpt-4o-mini gpt-5-nano gpt-5.4-nano gpt-5.4-mini
"""
import os, sys, json, argparse, random, concurrent.futures as cf, requests

SK = os.path.dirname(os.path.abspath(__file__))
API = "https://api.openai.com/v1"
SYSTEM = (
    "Sigue este rubro al pie de la letra:\n\n{rubric}\n\n"
    "Recibirás varias empresas en bloques '=== dominio ==='. Devuelve SOLO un objeto JSON "
    '{{"rows":[...]}} con UNA entrada por dominio, cada una exactamente '
    '{{"domain","business_model","outbound_fit","sells","primary_customer","confidence"}}. '
    "Sin citas, sin justificación, sin campos extra."
)


def sb_get(path, params):
    U = os.environ["SUPABASE_URL"].rstrip("/"); K = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    H = {"apikey": K, "authorization": f"Bearer {K}"}
    out, off = [], 0
    while True:
        p = dict(params); p["limit"] = "1000"; p["offset"] = str(off)
        js = requests.get(f"{U}/rest/v1/{path}", params=p, headers=H, timeout=120).json()
        if not isinstance(js, list) or not js: break
        out += js
        if len(js) < 1000: break
        off += 1000
    return out


def golden(n, seed=7):
    rows = sb_get("b2b_classification", {"select": "domain,label",
                                         "verified": "eq.true", "verify_agree": "eq.true"})
    random.Random(seed).shuffle(rows)
    by = {}
    for r in rows:
        by.setdefault(r["label"], []).append(r)
    picked = []
    while len(picked) < min(n, len(rows)):        # round-robin por etiqueta (estratificado)
        for lbl in list(by):
            if by[lbl] and len(picked) < n:
                picked.append(by[lbl].pop())
    return {r["domain"]: r["label"] for r in picked}


def contexts(domains, maxchars=8000):
    texts = {}
    for i in range(0, len(domains), 100):
        chunk = domains[i:i+100]
        for row in sb_get("site_crawls", {"select": "domain,clean_text",
                                          "domain": "in.(%s)" % ",".join(chunk)}):
            texts[row["domain"]] = (row.get("clean_text") or "")[:maxchars]
    return texts


def call_model(model, system, ctx_block):
    body = {"model": model, "max_completion_tokens": 6000,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": ctx_block}]}
    if model.startswith("gpt-5"):
        body["reasoning_effort"] = "low"
    r = requests.post(f"{API}/chat/completions", json=body, timeout=300,
                      headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"})
    r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])["rows"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--n", type=int, default=48)
    ap.add_argument("--size", type=int, default=12)
    a = ap.parse_args()

    gold = golden(a.n)
    doms = sorted(gold)
    texts = contexts(doms)
    lots = [doms[i:i+a.size] for i in range(0, len(doms), a.size)]
    blocks = ["\n".join(f"=== {d} ===\n{texts.get(d,'')}\n" for d in lot) for lot in lots]
    rubric = open(os.path.join(SK, "PROMPT.md"), encoding="utf-8").read()
    system = SYSTEM.format(rubric=rubric)
    clear = {d for d, l in gold.items() if l in ("b2b", "b2c")}

    print(f"golden: {len(doms)} dominios ({len(lots)} lotes) | claros (b2b/b2c): {len(clear)}\n")
    for model in a.models:
        preds = {}
        try:
            with cf.ThreadPoolExecutor(max_workers=4) as ex:
                for rows in ex.map(lambda b: call_model(model, system, b), blocks):
                    for x in rows:
                        preds[x.get("domain")] = str(x.get("business_model", "")).strip().lower()
        except Exception as e:
            print(f"{model}: ERROR {e}")
            continue
        hit = sum(1 for d in doms if preds.get(d) == gold[d])
        hit_clear = sum(1 for d in clear if preds.get(d) == gold[d])
        missing = sum(1 for d in doms if d not in preds)
        print(f"{model}: acuerdo total {hit}/{len(doms)} ({hit/len(doms):.0%}) | "
              f"claros {hit_clear}/{len(clear)} ({hit_clear/len(clear):.0%}) | sin respuesta {missing}")


if __name__ == "__main__":
    main()
