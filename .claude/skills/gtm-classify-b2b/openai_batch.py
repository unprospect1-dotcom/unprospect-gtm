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
            "max_completion_tokens": 6000,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": open(ctx, encoding="utf-8").read()},
            ],
        }
        if MODEL.startswith("gpt-5"):
            body["reasoning_effort"] = "low"
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


def collect_one(H, batch, outdir):
    """Parsea un batch completado -> escribe rcls_NNNN.jsonl. Devuelve (ok, bad)."""
    ok = bad = 0
    for file_key in ("output_file_id", "error_file_id"):
        fid = batch.get(file_key)
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
                bad += 1
                continue
            try:
                payload = json.loads(r["response"]["body"]["choices"][0]["message"]["content"])
                rows = payload["rows"]
                assert isinstance(rows, list) and rows
            except Exception:
                bad += 1
                continue
            open(os.path.join(outdir, f"rcls_{nn}.jsonl"), "w", encoding="utf-8").write(
                "\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n")
            ok += 1
    return ok, bad


def cmd_drain(a):
    """Drena TODA la cola respetando el límite de tokens encolados de la org:
    mini-batch de ~--budget tokens -> poll -> collect -> load_profiles -> repite."""
    import time, subprocess
    H = hdrs()
    rubric = open(os.path.join(SK, "PROMPT.md"), encoding="utf-8").read()
    system = SYSTEM.format(rubric=rubric)
    sys_tok = len(system) // 4 + 200
    round_n = 0
    while True:
        lots = pending_lots(a.outdir)
        if not lots:
            print("DRAIN DONE: no quedan lotes pendientes", flush=True)
            break
        shard, tok = [], 0
        for nn, ctx in lots:
            t = os.path.getsize(ctx) // 4 + sys_tok
            if shard and tok + t > a.budget:
                break
            shard.append((nn, ctx)); tok += t
        round_n += 1
        lines = []
        for nn, ctx in shard:
            body = {"model": MODEL, "max_completion_tokens": 6000,
                    "response_format": {"type": "json_object"},
                    "messages": [{"role": "system", "content": system},
                                 {"role": "user", "content": open(ctx, encoding="utf-8").read()}]}
            if MODEL.startswith("gpt-5"):
                body["reasoning_effort"] = "low"
            lines.append(json.dumps({"custom_id": nn, "method": "POST",
                                     "url": "/v1/chat/completions", "body": body}, ensure_ascii=False))
        tmp = os.path.join(a.outdir, "oai_drain.jsonl")
        open(tmp, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        with open(tmp, "rb") as fh:
            up = requests.post(f"{API}/files", headers=H, timeout=600,
                               files={"file": ("oai_drain.jsonl", fh)}, data={"purpose": "batch"})
        up.raise_for_status()
        b = requests.post(f"{API}/batches", headers=H, timeout=60, json={
            "input_file_id": up.json()["id"], "endpoint": "/v1/chat/completions",
            "completion_window": "24h"})
        if b.status_code >= 400:
            print(f"ronda {round_n}: submit {b.status_code} {b.text[:150]} — espero 180s", flush=True)
            time.sleep(180)
            continue
        bid = b.json()["id"]
        print(f"ronda {round_n}: {len(shard)} lotes (~{tok//1000}K tok) -> {bid} "
              f"(quedan {len(lots)-len(shard)} lotes después de esta)", flush=True)
        while True:
            time.sleep(60)
            st = requests.get(f"{API}/batches/{bid}", headers=H, timeout=60).json()
            if st["status"] in ("completed", "failed", "cancelled", "expired"):
                break
        if st["status"] != "completed":
            err = (st.get("errors") or {}).get("data") or [{}]
            print(f"ronda {round_n}: {st['status']} ({err[0].get('code')}) — espero 300s y sigo", flush=True)
            time.sleep(300)
            continue
        ok, bad = collect_one(H, st, a.outdir)
        print(f"ronda {round_n}: collected ok {ok} | bad {bad}", flush=True)
        try:
            out = subprocess.run(
                [sys.executable, os.path.join(SK, "load_profiles.py"),
                 "--classify", os.path.join(a.outdir, "rcls_*.jsonl"),
                 "--model", f"{MODEL.replace('.','').replace('-','')}-b12"],
                capture_output=True, text=True, timeout=600)
            print(f"ronda {round_n}: load -> {(out.stdout or out.stderr).strip().splitlines()[-1]}", flush=True)
        except Exception as e:
            print(f"ronda {round_n}: load ERROR {e} (rcls quedan en disco)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["make", "submit", "status", "collect", "drain"])
    ap.add_argument("--outdir", default=os.path.join(SK, "batches_prof"))
    ap.add_argument("--budget", type=int, default=1_800_000,
                    help="tokens encolados por mini-batch (límite org: 2M para nano)")
    a = ap.parse_args()
    {"make": cmd_make, "submit": cmd_submit, "status": cmd_status,
     "collect": cmd_collect, "drain": cmd_drain}[a.cmd](a)


if __name__ == "__main__":
    main()
