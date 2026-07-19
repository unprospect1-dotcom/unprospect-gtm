"""Carga resultados del schema mínimo a `company_gtm_profiles` (upsert por dominio).

Es el loader para la corrida masiva de perfiles (cola durable de gtm-profile-company)
usando los mismos rcls_/rver_ del clasificador mínimo.

  python load_profiles.py --classify "batches_prof/rcls_*.jsonl" --model haiku-b12
  python load_profiles.py --classify ... --verify "batches_prof/rver_*.jsonl" --model haiku-b12

Regla de aceptación (espejo del skill gtm-profile-company):
  - sin verify:  accepted si confidence=high y business_model no es mixed/unclear
                 (decision_method=first_pass_clear); si no -> needs_review.
  - con verify:  accepted si verify_label == business_model (decision_method=consensus);
                 si difieren -> needs_review (decision_method=disagreement).
"""
import argparse, glob, os, time, requests
from datetime import datetime, timezone
from load_supabase import U, K, read_jsonl, validate_rows, norm_conf


def known_domains(classify_pattern):
    """Dominios legítimos = los de los re_*.txt junto a los rcls. Un worker puede
    escribir un dominio con typo; esas filas se descartan (el dominio real sigue
    pending en la cola y se auto-repara en un tramo posterior)."""
    dirs = {os.path.dirname(p) for p in glob.glob(classify_pattern)} or \
           ({classify_pattern} if os.path.isdir(classify_pattern) else set())
    doms = set()
    for d in dirs:
        for re_path in glob.glob(os.path.join(d, "re_*.txt")):
            doms |= {l.strip() for l in open(re_path, encoding="utf-8") if l.strip()}
    return doms

IS_B2B = {"b2b": True, "mixed": True, "b2c": False, "noncommercial": False, "unclear": None}


def upsert(rows):
    hdr = {"apikey": K, "Authorization": f"Bearer {K}", "Content-Type": "application/json",
           "Prefer": "resolution=merge-duplicates,return=minimal"}
    for i in range(0, len(rows), 200):
        chunk = rows[i:i+200]
        for attempt in range(4):
            r = requests.post(f"{U}/rest/v1/company_gtm_profiles", json=chunk, headers=hdr, timeout=60)
            if r.status_code < 400: break
            if attempt == 3: raise RuntimeError(f"{r.status_code}: {r.text[:200]}")
            time.sleep(2 ** attempt)
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classify", required=True)
    ap.add_argument("--verify")
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--verifier-model", default="sonnet")
    args = ap.parse_args()

    C = read_jsonl(args.classify)
    V = read_jsonl(args.verify) if args.verify else {}
    valid = known_domains(args.classify)
    if valid:
        typos = sorted(set(C) - valid)
        if typos:
            print(f"descartados {len(typos)} dominios no presentes en los lotes (typo del worker): "
                  + ", ".join(typos[:10]))
            C = {d: c for d, c in C.items() if d in valid}
    bad = validate_rows(C, V)
    if bad:
        preview = ", ".join(bad[:20]); suffix = " ..." if len(bad) > 20 else ""
        raise RuntimeError(f"schema validation failed for {len(bad)} field(s): {preview}{suffix}")

    rows = []
    for dom, c in C.items():
        v = V.get(dom)
        label = str(c.get("business_model", c.get("label", ""))).strip().lower()
        conf = norm_conf(c.get("confidence"))
        if v:
            agree = str(v["verify_label"]).strip().lower() == label
            status = "accepted" if agree else "needs_review"
            decision = "consensus" if agree else "disagreement"
        else:
            clear = conf == "high" and label not in ("mixed", "unclear")
            status = "accepted" if clear else "needs_review"
            decision = "first_pass_clear" if clear else None
        rows.append({
            "domain": dom,
            "business_model": label,
            "is_b2b": IS_B2B.get(label),
            "outbound_fit": str(c.get("outbound_fit", "")).strip().lower() or None,
            "what_they_sell": c.get("sells"),
            "primary_customer": c.get("primary_customer"),
            "confidence": conf,
            "producer_model": args.model,
            "verifier_model": args.verifier_model if v else None,
            "decision_method": decision,
            "profile_status": status,
            "needs_review": status == "needs_review",
            "profiled_at": datetime.now(timezone.utc).isoformat(),
        })
    n = upsert(rows)
    acc = sum(1 for r in rows if r["profile_status"] == "accepted")
    print(f"upsert {n} filas | accepted {acc} | needs_review {n - acc}")


if __name__ == "__main__":
    main()
