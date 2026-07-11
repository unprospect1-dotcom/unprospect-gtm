# WORKER: verificador B2B (lote chico) — para despachar como subagente CIEGO

Reemplaza NN por el número de lote que te dieron. Eres un VERIFICADOR independiente:
das tu propio juicio desde cero, SIN ver la etiqueta de la capa 1. Lees SOLO el clean_text.
No navegues la web ni uses conocimiento de la marca. Usa un modelo DISTINTO (idealmente más
fuerte) que el de la capa 1.

SK=<ruta absoluta a>/.claude/skills/gtm-classify-b2b

1. Lee el rubro: SK/PROMPT.md. Al pie de la letra. OJO regla 6 y NO abuses de "mixed".
2. Baja los textos:  python3 SK/fetch_ct.py --batch SK/batches/re_NN.txt --outdir SK/batches/tv_NN
3. Léelos:  for f in SK/batches/tv_NN/ct_*.txt; do echo "=== $f ==="; cat "$f"; echo; done
4. Clasifica CADA dominio de SK/batches/re_NN.txt.
5. Escribe SK/batches/rver_NN.jsonl, UNA línea JSON por dominio:
   {"domain","verify_label","confidence","evidence"}   (evidence = cita textual corta).

NO pegues el JSON en tu mensaje. Reporta cuántos verificaste y la distribución.
