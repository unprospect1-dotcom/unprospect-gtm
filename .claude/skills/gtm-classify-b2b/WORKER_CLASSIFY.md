# WORKER: clasificador B2B (lote chico) — para despachar como subagente

Reemplaza NN por el número de lote que te dieron. Clasificas el MODELO DE NEGOCIO
(b2b/b2c/mixed/unclear) de empresas financieras mexicanas leyendo SOLO el clean_text.
No navegues la web ni uses conocimiento de la marca.

SK=<ruta absoluta a>/.claude/skills/gtm-classify-b2b

1. Lee el rubro completo: SK/PROMPT.md. Aplícalo al pie de la letra. OJO regla 6
   (objeto social ≠ producto) y NO abuses de "mixed" (solo si hay dos clientes con peso
   REAL comparable, con productos descritos para ambos).
2. Baja los textos:  python3 SK/fetch_ct.py --batch SK/batches/re_NN.txt --outdir SK/batches/tc_NN
3. Léelos:  for f in SK/batches/tc_NN/ct_*.txt; do echo "=== $f ==="; cat "$f"; echo; done
4. Clasifica CADA dominio de SK/batches/re_NN.txt con foco.
5. Escribe SK/batches/rcls_NN.jsonl, UNA línea JSON por dominio:
   {"domain","label","confidence","primary_customer","evidence","reason"}
   evidence = cita textual corta del clean_text. ct vacío -> "unclear".

NO pegues el JSON en tu mensaje. Reporta solo cuántos clasificaste y la distribución.
Confirma que las líneas de rcls_NN.jsonl == el número de dominios del lote.
