"""Carga la capa 2 (verificación con modelo más fuerte) sobre needs_review existentes.

Lee los rcls_*.jsonl del verificador (mismo formato de 6 campos) y los cruza con la
etiqueta ya guardada (capa 1) en company_gtm_profiles. Regla acordada (2026-07-20):

  - coinciden (verify_label == business_model)      -> accepted, decision_method=consensus
  - difieren, pero NINGUNO cambia a-quién-le-vendes
    (ambos dentro de b2b/mixed, o ambos b2c/noncommercial) -> accepted con el fallo del
    modelo fuerte, decision_method=stronger_model
  - difieren cruzando la frontera comercial (b2b/mixed <-> b2c/noncommercial/unclear)
    -> needs_review, decision_method=disagreement (decisión de negocio de Camilo)

  python load_capa2.py --verify "batches_capa2/rcls_*.jsonl" --verifier-model gpt54mini
"""
import argparse, glob, os, time, requests
from datetime import datetime, timezone
from load_supabase import U, K, read_jsonl, validate_rows, norm_conf
from load_profiles import IS_B2B, known_domains

COMERCIAL = {"b2b", "mixed"}  # lado "le vende a empresas"


def fetch_layer1(domains):
    H = {"apikey": K, "authorization": f"Bearer {K}"}
    out = {}
    doms = sorted(domains)
    for i in range(0, len(doms), 100):
        chunk = doms[i:i + 100]
        r = requests.get(f"{U}/rest/v1/company_gtm_profiles",
                         params={"select": "domain,business_model,outbound_fit",
                                 "domain": "in.(%s)" % ",".join(chunk)},
                         headers=H, timeout=120)
        for row in r.json():
            out[row["domain"]] = row
    return out


def upsert(rows):
    hdr = {"apikey": K, "Authorization": f"Bearer {K}", "Content-Type": "application/json",
           "Prefer": "resolution=merge-duplicates,return=minimal"}
    for i in range(0, len(rows), 200):
        chunk = rows[i:i + 200]
        for attempt in range(4):
            r = requests.post(f"{U}/rest/v1/company_gtm_profiles", json=chunk, headers=hdr, timeout=60)
            if r.status_code < 400:
                break
            if attempt == 3:
                raise RuntimeError(f"{r.status_code}: {r.text[:200]}")
            time.sleep(2 ** attempt)
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", required=True)
    ap.add_argument("--verifier-model", default="gpt54mini")
    args = ap.parse_args()

    V = read_jsonl(args.verify)
    valid = known_domains(args.verify)
    if valid:
        V = {d: v for d, v in V.items() if d in valid}
    # reusa validate_rows tratando la capa 2 como "classify"
    bad = validate_rows(V, {})
    if bad:
        bad_doms = {s.split(":")[0] for s in bad}
        print(f"descartadas {len(bad_doms)} filas inválidas (quedan needs_review): "
              + ", ".join(sorted(bad_doms)[:10]))
        V = {d: v for d, v in V.items() if d not in bad_doms}
    if not V:
        raise RuntimeError("no quedan filas válidas que cargar")

    l1 = fetch_layer1(V)
    rows, consensus, stronger, disagree = [], 0, 0, 0
    for dom, v in V.items():
        base = l1.get(dom)
        if not base:
            continue
        vlabel = str(v.get("business_model", "")).strip().lower()
        l1label = base["business_model"]
        agree = vlabel == l1label
        cross = (vlabel in COMERCIAL) != (l1label in COMERCIAL)
        if agree:
            status, method = "accepted", "consensus"; consensus += 1
        elif not cross:
            status, method = "accepted", "stronger_model"; stronger += 1
        else:
            status, method = "needs_review", "disagreement"; disagree += 1
        # el fallo del modelo fuerte gana la etiqueta (excepto cuando queda en review).
        # decision_method ya codifica el acuerdo (consensus/stronger_model/disagreement);
        # consensus_fields guarda la etiqueta de capa 1 para auditar el cambio.
        rows.append({
            "domain": dom,
            "business_model": vlabel,
            "is_b2b": IS_B2B.get(vlabel),
            "outbound_fit": str(v.get("outbound_fit", "")).strip().lower() or None,
            "what_they_sell": v.get("sells"),
            "primary_customer": v.get("primary_customer"),
            "confidence": norm_conf(v.get("confidence")),
            "verifier_model": args.verifier_model,
            "decision_method": method,
            "consensus_fields": [f"layer1:{l1label}", f"verify:{vlabel}", f"agree:{agree}"],
            "profile_status": status,
            "needs_review": status == "needs_review",
            "profiled_at": datetime.now(timezone.utc).isoformat(),
        })
    n = upsert(rows)
    print(f"capa 2: {n} filas | consenso {consensus} | resuelto por modelo fuerte {stronger} "
          f"| a revisión de negocio (frontera comercial) {disagree}")


if __name__ == "__main__":
    main()
