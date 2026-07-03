"""Ejecutor worker para el skill gtm-prompt-tuner.

Corre un prompt afinado (activo de workspaces/<ws>/prompts/) sobre un CSV
usando un modelo barato vía endpoint OpenAI-compatible (OpenRouter, Groq,
Together, etc.). El tuning NUNCA pasa por aquí — eso ocurre dentro de
Claude Code; este script solo ejecuta el prompt ya bloqueado.

Los defaults espejean config/providers.yaml (sección models.worker) — el skill
lee la config y pasa overrides por flag; este script no lee YAML.

Uso:
  python scripts/run_prompt.py \
    --prompt-file workspaces/unprospect/prompts/icp-fit-logistica.md \
    --in lists/unprospect/2026-07-03-logistica.csv \
    --out lists/unprospect/2026-07-03-logistica-scored.csv \
    --model google/gemma-3-27b-it --base-url https://openrouter.ai/api/v1

Auth: header Authorization Bearer con el valor de $WORKER_MODEL_KEY
(cambiable con --key-env). Cada request manda --batch-size filas y espera
un array JSON con un objeto por fila (mismo orden); las claves del objeto
se agregan como columnas nuevas al CSV de salida.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request


def read_prompt(path):
    """Extrae el cuerpo del activo (todo lo que sigue al frontmatter YAML)."""
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n.*?\n---\n", text, flags=re.DOTALL)
    return text[m.end():].strip() if m else text.strip()


def call(base_url, key, model, system_prompt, rows, fields, rps, retries=4):
    user_msg = (
        "Procesa estas filas y responde SOLO con un array JSON, un objeto por "
        "fila en el mismo orden, sin texto adicional:\n"
        + json.dumps([{f: r.get(f, "") for f in fields} for r in rows], ensure_ascii=False)
    )
    body = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
    }
    url = base_url.rstrip("/") + "/chat/completions"
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                time.sleep(1.0 / rps)
                content = json.loads(r.read().decode())["choices"][0]["message"]["content"]
                m = re.search(r"\[.*\]", content, flags=re.DOTALL)
                if not m:
                    raise ValueError(f"sin array JSON en la respuesta: {content[:200]}")
                return json.loads(m.group(0))
        except (urllib.error.HTTPError, ValueError, json.JSONDecodeError) as e:
            code = getattr(e, "code", None)
            if attempt < retries and (code == 429 or code is None or code >= 500):
                time.sleep(2 ** (attempt + 2))
                continue
            detail = e.read().decode()[:500] if isinstance(e, urllib.error.HTTPError) else str(e)
            sys.exit(f"fallo tras {attempt + 1} intentos: {detail}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-file", required=True, help="activo .md de workspaces/<ws>/prompts/")
    ap.add_argument("--in", dest="infile", required=True, help="CSV de entrada")
    ap.add_argument("--out", required=True, help="CSV de salida (columnas originales + las del prompt)")
    ap.add_argument("--base-url", default="https://openrouter.ai/api/v1")
    ap.add_argument("--model", default="google/gemma-3-27b-it")
    ap.add_argument("--key-env", default="WORKER_MODEL_KEY")
    ap.add_argument("--rps", type=float, default=2.0)
    ap.add_argument("--batch-size", type=int, default=10, help="filas por request — 10 mantiene la calidad")
    ap.add_argument("--fields", help="columnas a enviar, separadas por coma (default: todas)")
    args = ap.parse_args()

    key = os.environ.get(args.key_env) or sys.exit(f"falta la env var {args.key_env}")
    system_prompt = read_prompt(args.prompt_file)

    with open(args.infile, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit("CSV de entrada vacío")
    fields = args.fields.split(",") if args.fields else list(rows[0].keys())

    results = []
    for i in range(0, len(rows), args.batch_size):
        batch = rows[i:i + args.batch_size]
        scored = call(args.base_url, key, args.model, system_prompt, batch, fields, args.rps)
        if len(scored) != len(batch):
            sys.exit(f"lote {i // args.batch_size}: esperaba {len(batch)} objetos, llegaron {len(scored)}")
        results.extend(scored)
        print(f"{min(i + args.batch_size, len(rows))}/{len(rows)} filas", file=sys.stderr)

    new_cols = [k for k in results[0] if k not in rows[0]]
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) + new_cols)
        w.writeheader()
        for row, scored in zip(rows, results):
            w.writerow({**row, **{k: scored.get(k, "") for k in new_cols}})
    print(f"WROTE {len(results)} filas → {args.out}")


if __name__ == "__main__":
    main()
