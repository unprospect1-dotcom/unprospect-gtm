#!/usr/bin/env python3
"""Puente con spawn_agents_on_csv de Codex para perfilar en masa. Stdlib puro.

Flujo (opción C, ver docs/SUBAGENTS.md):
  1) export_supabase_queue.py + make_batches.py + rebatch_compact.py -> work/batches/batch_NN.json
  2) python3 codex_csv.py make --batches-dir work/batches_compact
     -> escribe codex_profile.csv (1 fila = 1 LOTE) e imprime el prompt para pegar a Codex
  3) Codex corre spawn_agents_on_csv (estado SQLite, resumable) y exporta resultados
  4) python3 codex_csv.py collect --batches-dir ... --results <export.csv>
     -> valida cada lote con validate_profiles y escribe prof_NN.json SOLO si pasa
  5) persistir los aceptados a company_gtm_profiles (flujo normal del skill)
"""
import os, sys, csv, json, glob, argparse
from pathlib import Path

SK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_profiles import validate  # noqa: E402

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "nn": {"type": "string"},
        "count": {"type": "integer"},
        "profiles_json": {"type": "string"},
    },
    "required": ["nn", "count", "profiles_json"],
}


def lot_number(path):
    return Path(path).stem.split("_")[-1]


def pending(batches_dir):
    lots = []
    for batch in sorted(glob.glob(os.path.join(batches_dir, "batch_*.json"))):
        nn = lot_number(batch)
        if not os.path.exists(os.path.join(batches_dir, f"prof_{nn}.json")):
            n = len(json.loads(Path(batch).read_text(encoding="utf-8"))["companies"])
            lots.append((nn, batch, n))
    return lots


def cmd_make(a):
    lots = pending(a.batches_dir)
    if not lots:
        sys.exit("No hay lotes pendientes en ese directorio.")
    csv_path = os.path.join(a.batches_dir, "codex_profile.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["nn", "batch_path", "n_companies"])
        for nn, batch, n in lots:
            w.writerow([nn, batch, n])

    rubric = SK / "references" / "rubric.md"
    instruction = (
        "Eres un worker de perfilado GTM. Lee el rubro completo "
        f"{rubric} y aplícalo al pie de la letra. Luego lee {{batch_path}}: JSON con "
        "{n_companies} empresas (domain + clean_text). Perfila CADA empresa siguiendo el "
        "esquema exacto del rubro. No navegues la web ni uses conocimiento de marca; toda "
        "cita en evidence debe ser substring LITERAL del clean_text de esa empresa; usa "
        "null/[]/unclear cuando la evidencia no alcance. Reporta con report_agent_job_result "
        "un JSON con: nn=\"{nn}\", count=el número de perfiles, y profiles_json=el array "
        "JSON completo de perfiles serializado como string."
    )
    print(f"CSV: {csv_path}  ({len(lots)} lotes pendientes)\n")
    print("=== Pégale esto a Codex (modelo barato, ej. gpt-5.4-mini low) ===\n")
    print(f"Usa spawn_agents_on_csv con csv_path={csv_path}, id_column=nn, max_concurrency=6, "
          f"output_csv_path={a.batches_dir}/codex_profile_results.csv,")
    print(f"output_schema={json.dumps(OUTPUT_SCHEMA)}")
    print(f"e instruction=\"{instruction}\"")
    print(f"\nAl terminar: python3 {Path(__file__).resolve()} collect "
          f"--batches-dir {a.batches_dir} --results {a.batches_dir}/codex_profile_results.csv")


def cmd_collect(a):
    ok = bad = 0
    tmp = Path(a.batches_dir) / "_collect_tmp.json"
    with open(a.results, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            nn = row.get("nn") or row.get("item_id") or ""
            batch = Path(a.batches_dir) / f"batch_{nn}.json"
            if row.get("status") and row["status"] not in ("ok", "success", "succeeded", "completed"):
                print(f"lote {nn}: status={row['status']} error={row.get('last_error','')!r} -> re-despachar")
                bad += 1
                continue
            try:
                profiles = json.loads(json.loads(row["result_json"])["profiles_json"])
                assert isinstance(profiles, list)
            except Exception as e:
                print(f"lote {nn}: result_json inválido ({e}) -> re-despachar")
                bad += 1
                continue
            tmp.write_text(json.dumps(profiles, ensure_ascii=False), encoding="utf-8")
            errors = validate(batch, tmp)
            if errors:
                print(f"lote {nn}: {len(errors)} errores de validación (ej. {errors[0]}) -> re-despachar")
                bad += 1
                continue
            out = Path(a.batches_dir) / f"prof_{nn}.json"
            out.write_text(json.dumps(profiles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            ok += 1
    if tmp.exists():
        tmp.unlink()
    print(f"\nlotes válidos: {ok} | rechazados (re-despachar con `make`): {bad}")
    if ok:
        print("Persiste ya los prof_*.json aceptados a company_gtm_profiles (flujo del skill).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["make", "collect"])
    ap.add_argument("--batches-dir", required=True)
    ap.add_argument("--results")
    a = ap.parse_args()
    if a.cmd == "collect" and not a.results:
        sys.exit("collect requiere --results <export.csv>")
    (cmd_make if a.cmd == "make" else cmd_collect)(a)


if __name__ == "__main__":
    main()
