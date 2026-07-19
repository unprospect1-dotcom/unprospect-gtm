"""Carga clasificaciones a Supabase `b2b_classification` (upsert por dominio).

Schema mínimo v2 (2026-07-18): sin citas ni reason. El gate de calidad pre-carga es la
validación de enums/forma; el control de fondo es la doble pasada ciega (verify_agree).

  python load_supabase.py --classify "batches/rcls_*.jsonl"
  python load_supabase.py --classify batches --verify "batches/rver_*.jsonl" --model haiku

Formatos (una línea JSON por dominio):
  classify: {domain,business_model,outbound_fit,sells,primary_customer,confidence}
  verify:   {domain,verify_label,verify_fit,confidence}
"""
import os, sys, json, re, argparse, time, glob, requests

U = os.environ["SUPABASE_URL"].rstrip("/"); K = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TOK = os.environ.get("SUPABASE_TOKEN", "")
REF = re.search(r"https://([a-z0-9]+)\.supabase", U).group(1)

SK = os.path.dirname(os.path.abspath(__file__))
MIGRATIONS = os.path.join(SK, "..", "..", "..", "supabase", "migrations")
DDL_FILES = ("004_b2b_classification.sql", "009_b2b_minimal_schema.sql")

LABELS = {"b2b", "b2c", "mixed", "noncommercial", "unclear"}
FITS = {"high", "medium", "low", "unclear"}
CONF = {"high", "medium", "med", "low"}

def mgmt_sql(sql):
    r = requests.post(f"https://api.supabase.com/v1/projects/{REF}/database/query",
                      json={"query": sql}, headers={"Authorization": f"Bearer {TOK}"}, timeout=60)
    return r.status_code, r.text[:200]

def read_jsonl(pattern):
    """Acepta un archivo, un glob (rcls_*.jsonl) o un directorio. Fusiona todo."""
    out = {}
    if not pattern: return out
    paths = []
    if os.path.isdir(pattern):
        paths = sorted(glob.glob(os.path.join(pattern, "*.jsonl")))
    elif any(c in pattern for c in "*?["):
        paths = sorted(glob.glob(pattern))
    elif os.path.exists(pattern):
        paths = [pattern]
    for path in paths:
        for line in open(path, encoding="utf-8"):
            try:
                r = json.loads(line)
                if r.get("domain") and not r.get("error"): out[r["domain"]] = r
            except Exception: pass
    return out

def norm_conf(v):
    v = str(v or "").strip().lower()
    return "medium" if v == "med" else v

def validate_rows(C, V):
    """Enums y forma. Reemplaza al gate de citas: filas inválidas detienen la carga."""
    bad = []
    for dom, c in C.items():
        if not re.fullmatch(r"[A-Za-z0-9.-]+", dom or ""):
            bad.append(f"{dom}:domain"); continue
        if str(c.get("business_model", c.get("label", ""))).strip().lower() not in LABELS:
            bad.append(f"{dom}:business_model")
        if str(c.get("outbound_fit", "")).strip().lower() not in FITS:
            bad.append(f"{dom}:outbound_fit")
        if str(c.get("confidence", "")).strip().lower() not in CONF:
            bad.append(f"{dom}:confidence")
        if len(str(c.get("sells") or "").split()) > 14:
            bad.append(f"{dom}:sells>14w")
        if len(str(c.get("primary_customer") or "").split()) > 16:
            bad.append(f"{dom}:primary_customer>16w")
    for dom, v in V.items():
        if str(v.get("verify_label", "")).strip().lower() not in LABELS:
            bad.append(f"{dom}:verify_label")
        if v.get("verify_fit") is not None and str(v["verify_fit"]).strip().lower() not in FITS:
            bad.append(f"{dom}:verify_fit")
    return bad

def upsert(rows):
    hdr = {"apikey": K, "Authorization": f"Bearer {K}", "Content-Type": "application/json",
           "Prefer": "resolution=merge-duplicates,return=minimal"}
    for i in range(0, len(rows), 200):
        chunk = rows[i:i+200]
        for attempt in range(4):
            r = requests.post(f"{U}/rest/v1/b2b_classification", json=chunk, headers=hdr, timeout=60)
            if r.status_code < 400: break
            if attempt == 3: raise RuntimeError(f"{r.status_code}: {r.text[:200]}")
            time.sleep(2 ** attempt)
    return len(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classify", required=True, help="archivo, glob (rcls_*.jsonl) o directorio")
    ap.add_argument("--verify", help="archivo, glob o directorio (opcional)")
    ap.add_argument("--model", default="haiku", help="modelo/subagente que clasificó, p.ej. haiku, codex-mini")
    args = ap.parse_args()

    if TOK:
        for name in DDL_FILES:
            path = os.path.join(MIGRATIONS, name)
            if os.path.exists(path):
                print(f"DDL {name}:", mgmt_sql(open(path, encoding="utf-8").read()))

    C = read_jsonl(args.classify)
    V = read_jsonl(args.verify) if args.verify else {}
    bad = validate_rows(C, V)
    if bad:
        preview = ", ".join(bad[:20]); suffix = " ..." if len(bad) > 20 else ""
        raise RuntimeError(f"schema validation failed for {len(bad)} field(s): {preview}{suffix}")

    rows = []
    for dom, c in C.items():
        v = V.get(dom)
        label = str(c.get("business_model", c.get("label", ""))).strip().lower()
        vlabel = str(v["verify_label"]).strip().lower() if v else None
        rows.append({
            "domain": dom,
            "label": label,
            "confidence": norm_conf(c.get("confidence")),
            "primary_customer": c.get("primary_customer"),
            "sells": c.get("sells"),
            "outbound_fit": str(c.get("outbound_fit", "")).strip().lower() or None,
            "evidence": None,
            "reason": None,
            "model": args.model,
            "verified": bool(v),
            "verify_label": vlabel,
            "verify_fit": (str(v["verify_fit"]).strip().lower() if v and v.get("verify_fit") else None),
            "verify_agree": (vlabel == label) if v else None,
            "verify_note": None,
        })
    n = upsert(rows)
    agree = sum(1 for r in rows if r["verify_agree"])
    ver = sum(1 for r in rows if r["verified"])
    print(f"upsert {n} filas | verificadas {ver} | acuerdo {agree}/{ver if ver else '-'}")

if __name__ == "__main__":
    main()
