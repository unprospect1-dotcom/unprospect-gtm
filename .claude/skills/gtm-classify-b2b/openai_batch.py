#!/usr/bin/env python3
"""Corrida masiva vía OpenAI Batch API (gpt-5.4-mini, 50% de descuento, sin límites de
sesión del harness). Mismo rubro (PROMPT.md), mismos ctx_NNNN.txt, misma salida
rcls_NNNN.jsonl que consumen load_profiles.py / load_supabase.py.

  export OPENAI_API_KEY=sk-...
  python3 openai_batch.py make    --outdir batches_prof   # arma shards de requests JSONL
  python3 openai_batch.py submit  --outdir batches_prof   # sube y crea los batches
  python3 openai_batch.py status  --outdir batches_prof   # estado de todos los batches
  python3 openai_batch.py collect --outdir batches_prof   # baja resultados -> rcls_NNNN.jsonl

Después: python3 load_profiles.py --classify "batches_prof/rcls_*.jsonl" --model gpt54mini-b12
Los lotes con filas faltantes/inválidas simplemente no se cargan completos: esos dominios
siguen pending en la cola y se barren en una pasada posterior (diseño auto-reparable).
"""
import os, sys, json, glob, argparse, requests

SK = os.path.dirname(os.path.abspath(__file__))
API = "https://api.openai.com/v1"
MODEL = os.environ.get("OPENAI_BATCH_MODEL", "gpt-5.4-mini")
SHARD_REQS = 700  # ~700 lotes por shard mantiene cada archivo << 200MB (límite de Batch)

SYSTEM = (
    "Sigue este rubro al pie de la letra:\n\n{rubric}\n\n"
    "Recibirás varias empresas en bloques '=== dominio ==='. Devuelve SOLO un objeto JSON "
    '{{"rows":[...]}} con UNA entrada por dominio, cada una exactamente '
    '{{"domain","business_model","outbound_fit","sells","primary_customer","confidence"}}. '
    "Sin citas, sin justificación, sin campos extra."
)


def hdrs():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("Falta OPENAI_API_KEY en el entorno.")
    return {"Authorization": f"Bearer {key}"}


def pending_lots(outdir):
    lots = []
    for ctx in sorted(glob.glob(os.path.join(outdir, "ctx_*.txt"))):
        nn = os.path.basename(ctx)[4:-4]
        if not os.path.exists(os.path.join(outdir, f"rcls_{nn}.jsonl")):
            lots.append((nn, ctx))
    return lots


def cmd_make(a):
    rubric = open(os.path.join(SK, "PROMPT.md"), encoding="utf-8").read()
    system = SYSTEM.format(rubric=rubric)
    lots = pending_lots(a.outdir)
    if not lots:
        sys.exit("No hay lotes pendientes (¿ya existe rcls para todos los ctx?).")
    for old in glob.glob(os.path.join(a.outdir, "oai_reqs_*.jsonl")):
        os.remove(old)
    shard, n_shards = [], 0
    def flush():
        nonlocal shard, n_shards
        if not shard: return
        path = os.path.join(a.outdir, f"oai_reqs_{n_shards:02d}.jsonl")
        open(path, "w", encoding="utf-8").write("\n".join(shard) + "\n")
        n_shards += 1; shard = []
    for nn, ctx in lots:
        body = {
            "model": MODEL,
            "reasoning_effort": "low",
            "max_completion_tokens": 6000,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": open(ctx, encoding="utf-8").read()},
            ],
        }
        shard.append(json.dumps({"custom_id": nn, "method": "POST",
                                 "url": "/v1/chat/completions", "body": body}, ensure_ascii=False))
        if len(shard) >= SHARD_REQS:
            flush()
    flush()
    print(f"lotes pendientes: {len(lots)} | shards: {n_shards} (oai_reqs_NN.jsonl en {a.outdir})")
    print("Sigue: python3 openai_batch.py submit --outdir", a.outdir)


def cmd_submit(a):
    H = hdrs()
    ids = []
    for path in sorted(glob.glob(os.path.join(a.outdir, "oai_reqs_*.jsonl"))):
        with open(path, "rb") as fh:
            up = requests.post(f"{API}/files", headers=H, timeout=600,
                               files={"file": (os.path.basename(path), fh)},
                               data={"purpose": "batch"})
        up.raise_for_status()
        b = requests.post(f"{API}/batches", headers=H, timeout=60, json={
            "input_file_id": up.json()["id"],
            "endpoint": "/v1/chat/completions",
            "completion_window": "24h",
        })
        b.raise_for_status()
        ids.append(b.json()["id"])
        print(f"{os.path.basename(path)} -> batch {b.json()['id']}")
    open(os.path.join(a.outdir, "oai_batch_ids.txt"), "w").write("\n".join(ids) + "\n")
    print(f"\n{len(ids)} batch(es) creados. Checa con: python3 openai_batch.py status --outdir {a.outdir}")


def batch_ids(outdir):
    path = os.path.join(outdir, "oai_batch_ids.txt")
    if not os.path.exists(path):
        sys.exit("No hay oai_batch_ids.txt (corre submit primero).")
    return [l.strip() for l in open(path) if l.strip()]


def cmd_status(a):
    H = hdrs()
    for bid in batch_ids(a.outdir):
        b = requests.get(f"{API}/batches/{bid}", headers=H, timeout=60).json()
        c = b.get("request_counts", {})
        print(f"{bid}: {b['status']} | ok {c.get('completed',0)}/{c.get('total',0)} | err {c.get('failed',0)}")


def cmd_collect(a):
    H = hdrs()
    ok = bad = 0
    for bid in batch_ids(a.outdir):
        b = requests.get(f"{API}/batches/{bid}", headers=H, timeout=60).json()
        if b["status"] != "completed":
            print(f"{bid}: {b['status']} (aún no; nada que colectar de este batch)")
            continue
        for file_key in ("output_file_id", "error_file_id"):
            fid = b.get(file_key)
            if not fid:
                continue
            content = requests.get(f"{API}/files/{fid}/content", headers=H, timeout=600).text
            for line in content.splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                nn = r["custom_id"]
                if file_key == "error_file_id" or r.get("error") or \
                   r.get("response", {}).get("status_code", 200) >= 400:
                    print(f"lote {nn}: error de request -> re-hacer (make/submit lo retoma)")
                    bad += 1
                    continue
                try:
                    payload = json.loads(r["response"]["body"]["choices"][0]["message"]["content"])
                    rows = payload["rows"]
                    assert isinstance(rows, list) and rows
                except Exception as e:
                    print(f"lote {nn}: JSON inválido ({e}) -> re-hacer")
                    bad += 1
                    continue
                out = os.path.join(a.outdir, f"rcls_{nn}.jsonl")
                open(out, "w", encoding="utf-8").write(
                    "\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n")
                ok += 1
    print(f"\nlotes colectados: {ok} | con error: {bad}")
    if ok:
        print(f"Carga: python3 {os.path.join(SK,'load_profiles.py')} --classify "
              f"\"{a.outdir}/rcls_*.jsonl\" --model gpt54mini-b12")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["make", "submit", "status", "collect"])
    ap.add_argument("--outdir", default=os.path.join(SK, "batches_prof"))
    a = ap.parse_args()
    {"make": cmd_make, "submit": cmd_submit, "status": cmd_status, "collect": cmd_collect}[a.cmd](a)


if __name__ == "__main__":
    main()
