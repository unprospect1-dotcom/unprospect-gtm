"""Carga clasificaciones a Supabase `b2b_classification` (upsert por dominio).

Fusiona la salida del clasificador (capa 1) con la del verificador (capa 2, opcional) y
calcula verify_agree. La tabla se crea sola si no existe (DDL idempotente).

  python load_supabase.py --classify "batches/cls_*.jsonl"
  python load_supabase.py --classify batches --verify "batches/verify_*.jsonl" --model haiku

Formatos (una línea JSON por dominio):
  classify: {domain,label,confidence,primary_customer,evidence,reason}
  verify:   {domain,verify_label,confidence,evidence}
"""
import os, sys, json, re, argparse, time, glob, requests
from validate_evidence import find_evidence_failures

U = os.environ["SUPABASE_URL"].rstrip("/"); K = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TOK = os.environ.get("SUPABASE_TOKEN", "")
REF = re.search(r"https://([a-z0-9]+)\.supabase", U).group(1)

DDL = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..",
           "supabase", "migrations", "004_b2b_classification.sql"), encoding="utf-8").read() \
      if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),
           "..","..","..","supabase","migrations","004_b2b_classification.sql")) else None

def mgmt_sql(sql):
    r = requests.post(f"https://api.supabase.com/v1/projects/{REF}/database/query",
                      json={"query": sql}, headers={"Authorization": f"Bearer {TOK}"}, timeout=60)
    return r.status_code, r.text[:200]

def read_jsonl(pattern):
    """Acepta un archivo, un glob (cls_*.jsonl) o un directorio. Fusiona todo."""
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

def fetch_clean_texts(domains):
    """Fetch source text in chunks so model evidence can be checked before persistence."""
    hdr = {"apikey": K, "Authorization": f"Bearer {K}"}
    out = {}
    domains = sorted(set(domains))
    invalid = [domain for domain in domains if not re.fullmatch(r"[A-Za-z0-9.-]+", domain or "")]
    if invalid:
        raise RuntimeError(f"invalid domain value(s): {', '.join(invalid[:20])}")
    for i in range(0, len(domains), 100):
        chunk = domains[i:i+100]
        r = requests.get(
            f"{U}/rest/v1/site_crawls",
            params={"select": "domain,clean_text", "domain": f"in.({','.join(chunk)})"},
            headers=hdr,
            timeout=120,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"clean_text fetch {r.status_code}: {r.text[:200]}")
        payload = r.json()
        if not isinstance(payload, list):
            raise RuntimeError("clean_text fetch returned a non-list payload")
        for row in payload:
            out[row.get("domain")] = row.get("clean_text")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classify", required=True, help="archivo, glob (cls_*.jsonl) o directorio")
    ap.add_argument("--verify", help="archivo, glob o directorio (opcional)")
    ap.add_argument("--model", default="haiku", help="modelo/subagente que clasificó, p.ej. haiku, codex-mini")
    args = ap.parse_args()

    if TOK and DDL:
        print("DDL:", mgmt_sql(DDL))

    C = read_jsonl(args.classify)
    V = read_jsonl(args.verify) if args.verify else {}
    clean_texts = fetch_clean_texts(C)
    evidence_failures = find_evidence_failures(C, V, clean_texts)
    if evidence_failures:
        preview = ", ".join(evidence_failures[:20])
        suffix = " ..." if len(evidence_failures) > 20 else ""
        raise RuntimeError(
            f"evidence validation failed for {len(evidence_failures)} row(s): {preview}{suffix}"
        )
    rows = []
    for dom, c in C.items():
        v = V.get(dom)
        vlabel = str(v["verify_label"]).strip().lower() if v else None
        rows.append({
            "domain": dom,
            "label": str(c.get("label", "")).strip().lower(),
            "confidence": c.get("confidence"),
            "primary_customer": c.get("primary_customer"),
            "evidence": c.get("evidence"),
            "reason": c.get("reason"),
            "model": args.model,
            "verified": bool(v),
            "verify_label": vlabel,
            "verify_agree": (vlabel == str(c.get("label", "")).strip().lower()) if v else None,
            "verify_note": (v.get("evidence") if v else None),
        })
    n = upsert(rows)
    agree = sum(1 for r in rows if r["verify_agree"])
    ver = sum(1 for r in rows if r["verified"])
    print(f"upsert {n} filas | verificadas {ver} | acuerdo {agree}/{ver if ver else '-'}")

if __name__ == "__main__":
    main()
