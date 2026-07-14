"""Carga veredictos de subcategoría (subcat_NN.jsonl / verify_NN.jsonl) a list_companies.

  python scripts/subcat_to_supabase.py --classify "batches-transporte/subcat_*.jsonl" \
      --niche autotransporte-mx --model haiku [--verify "batches-transporte/vsubcat_*.jsonl"]

- classify: upsert de subcat, subcat_confidence, subcat_evidence, subcat_model.
- verify: setea subcat_verify y subcat_agree = (subcat == subcat_verify).
- Solo actualiza filas existentes del niche (PATCH por dominio en lotes vía upsert
  merge-duplicates con las columnas provistas — las demás columnas no se tocan).
"""
import argparse
import glob
import json
import os
import urllib.request

def req(url, body, headers, method="POST"):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), method=method,
                               headers={"Content-Type": "application/json",
                                        "User-Agent": "curl/8.5.0", **headers})
    with urllib.request.urlopen(r, timeout=180) as resp:
        return resp.status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classify", required=True)
    ap.add_argument("--verify")
    ap.add_argument("--niche", required=True)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--batch", type=int, default=500)
    a = ap.parse_args()

    base = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    hdr = {"apikey": key, "Authorization": f"Bearer {key}",
           "Prefer": "resolution=merge-duplicates"}
    url = f"{base}/rest/v1/list_companies?on_conflict=niche,domain"

    cls = {}
    for f in glob.glob(a.classify):
        for line in open(f):
            d = json.loads(line)
            cls[d["domain"]] = {"niche": a.niche, "domain": d["domain"],
                                "subcat": d.get("subcat"),
                                "subcat_confidence": d.get("confidence"),
                                "subcat_evidence": (d.get("evidence") or "")[:500],
                                "subcat_model": a.model}
    rows = list(cls.values())
    for i in range(0, len(rows), a.batch):
        st = req(url, rows[i:i + a.batch], hdr)
        print(f"classify upsert {min(i+a.batch,len(rows))}/{len(rows)} -> {st}", flush=True)

    if a.verify:
        ver = {}
        for f in glob.glob(a.verify):
            for line in open(f):
                d = json.loads(line)
                ver[d["domain"]] = d.get("verify_label") or d.get("subcat")
        vrows = []
        for dom, vlabel in ver.items():
            row = {"niche": a.niche, "domain": dom, "subcat_verify": vlabel}
            if dom in cls:
                row["subcat_agree"] = (cls[dom]["subcat"] == vlabel)
            vrows.append(row)
        # llaves idénticas por batch (PGRST102)
        keys = set()
        for r in vrows:
            keys.update(r)
        vrows = [{k: r.get(k) for k in keys} for r in vrows]
        for i in range(0, len(vrows), a.batch):
            st = req(url, vrows[i:i + a.batch], hdr)
            print(f"verify upsert {min(i+a.batch,len(vrows))}/{len(vrows)} -> {st}", flush=True)

    print(f"LISTO: {len(rows)} clasificaciones" + (f", {len(ver)} verificaciones" if a.verify else ""))


if __name__ == "__main__":
    main()
