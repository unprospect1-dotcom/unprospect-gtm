#!/usr/bin/env python3
"""Puente con spawn_agents_on_csv de Codex para correr los lotes en masa. Stdlib puro.

Flujo (opción C del repo, ver docs/SUBAGENTS.md):
  1) python3 make_context.py --unverified            # materializa re_NN.txt + ctx_NN.txt
  2) python3 codex_csv.py make --layer classify      # escribe batches/codex_classify.csv
     e imprime el prompt EXACTO para pegarle a Codex (1 fila = 1 LOTE, no 1 empresa)
  3) Codex corre spawn_agents_on_csv y exporta un CSV de resultados
  4) python3 codex_csv.py collect --layer classify --results <export.csv>
     -> valida y escribe batches/rcls_NN.jsonl (o rver_NN.jsonl con --layer verify)
  5) python3 load_supabase.py --classify "batches/rcls_*.jsonl" ... (igual que siempre)

El estado del job vive en el SQLite de Codex (resumable) y la fuente durable sigue siendo
Supabase: carga cada corrida apenas colectes.
"""
import os, csv, json, argparse, glob, sys

SK = os.path.dirname(os.path.abspath(__file__))
PREFIX = {"classify": "rcls", "verify": "rver"}
FIELDS = {
    "classify": '{"domain","label","confidence","primary_customer","evidence","reason"}',
    "verify": '{"domain","verify_label","confidence","evidence"}',
}
ROLE = {
    "classify": ("Clasificas el MODELO DE NEGOCIO (b2b/b2c/mixed/unclear) de empresas "
                 "leyendo SOLO el clean_text."),
    "verify": ("Eres un VERIFICADOR independiente y CIEGO: etiqueta (b2b/b2c/mixed/unclear) "
               "desde cero, sin ver ni pedir respuestas previas de otro worker."),
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "nn": {"type": "string"},
        "count": {"type": "integer"},
        "jsonl": {"type": "string"},
    },
    "required": ["nn", "count", "jsonl"],
}


def pending_lots(outdir, layer):
    lots = []
    for re_path in sorted(glob.glob(os.path.join(outdir, "re_*.txt"))):
        nn = os.path.basename(re_path)[3:-4]
        ctx = os.path.join(outdir, f"ctx_{nn}.txt")
        out = os.path.join(outdir, f"{PREFIX[layer]}_{nn}.jsonl")
        if os.path.exists(ctx) and not os.path.exists(out):
            n = sum(1 for l in open(re_path, encoding="utf-8") if l.strip())
            lots.append((nn, re_path, ctx, n))
    return lots


def cmd_make(a):
    lots = pending_lots(a.outdir, a.layer)
    if not lots:
        sys.exit("No hay lotes pendientes (corre make_context.py primero o ya está todo).")
    csv_path = os.path.join(a.outdir, f"codex_{a.layer}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["nn", "ctx_path", "n_domains"])
        for nn, _re, ctx, n in lots:
            w.writerow([nn, ctx, n])

    instruction = (
        f"{ROLE[a.layer]} "
        f"Lee el rubro completo {SK}/PROMPT.md y aplícalo al pie de la letra (regla 6: objeto "
        "social != producto; no abusar de mixed). Luego lee el archivo {ctx_path}: contiene "
        "{n_domains} empresas en bloques '=== dominio ==='. Etiqueta CADA dominio. No navegues "
        "la web ni uses conocimiento de marca; evidence = cita textual LITERAL del clean_text; "
        "bloque vacío -> unclear. Reporta con report_agent_job_result un JSON con: nn=\"{nn}\", "
        f"count=el número de dominios etiquetados, y jsonl=las {{n_domains}} líneas JSON "
        f"(una por dominio, separadas por \\n) con el shape {FIELDS[a.layer]}."
    )
    print(f"CSV: {csv_path}  ({len(lots)} lotes pendientes)\n")
    print("=== Pégale esto a Codex (modelo barato, ej. gpt-5.4-mini low) ===\n")
    print(f"Usa spawn_agents_on_csv con csv_path={csv_path}, id_column=nn, "
          f"max_concurrency=6, output_csv_path={a.outdir}/codex_{a.layer}_results.csv,")
    print(f"output_schema={json.dumps(OUTPUT_SCHEMA)}")
    print(f"e instruction=\"{instruction}\"")
    print(f"\nAl terminar: python3 {SK}/codex_csv.py collect --layer {a.layer} "
          f"--results {a.outdir}/codex_{a.layer}_results.csv")


def cmd_collect(a):
    ok = bad = 0
    with open(a.results, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            nn = row.get("nn") or row.get("item_id") or ""
            if row.get("status") and row["status"] not in ("ok", "success", "succeeded", "completed"):
                print(f"lote {nn}: status={row['status']} error={row.get('last_error','')!r} -> re-despachar")
                bad += 1
                continue
            try:
                payload = json.loads(row["result_json"])
                lines = [l for l in payload["jsonl"].splitlines() if l.strip()]
                for l in lines:
                    json.loads(l)  # cada línea debe ser JSON válido
            except Exception as e:
                print(f"lote {nn}: result_json inválido ({e}) -> re-despachar")
                bad += 1
                continue
            expected = sum(1 for l in open(os.path.join(a.outdir, f"re_{nn}.txt"), encoding="utf-8") if l.strip())
            if len(lines) != expected:
                print(f"lote {nn}: {len(lines)} líneas, esperaba {expected} -> re-despachar")
                bad += 1
                continue
            out = os.path.join(a.outdir, f"{PREFIX[a.layer]}_{nn}.jsonl")
            open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
            ok += 1
    print(f"\nlotes colectados: {ok} | con error (re-despachar con `make`): {bad}")
    if ok:
        flag = "--classify" if a.layer == "classify" else "--verify"
        print(f"Carga ya: python3 {SK}/load_supabase.py {flag} \"{a.outdir}/{PREFIX[a.layer]}_*.jsonl\" ...")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["make", "collect"])
    ap.add_argument("--layer", choices=["classify", "verify"], default="classify")
    ap.add_argument("--outdir", default=os.path.join(SK, "batches"))
    ap.add_argument("--results")
    a = ap.parse_args()
    if a.cmd == "collect" and not a.results:
        sys.exit("collect requiere --results <export.csv>")
    (cmd_make if a.cmd == "make" else cmd_collect)(a)


if __name__ == "__main__":
    main()
