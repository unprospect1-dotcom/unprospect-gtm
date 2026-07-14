# WORKER: subcategoría transporte (lote chico) — para despachar como subagente

Reemplaza NN por el número de lote. Clasificas la SUBCATEGORÍA de empresas del universo
transporte/logística MX leyendo SOLO el clean_text. No navegues ni uses conocimiento de marca.
Funciona igual en Claude Code (model: haiku) y Codex (modelo más barato).

SK=<ruta absoluta a>/.claude/skills/gtm-classify-b2b
BD=<ruta absoluta al dir de batches>   # ej. <scratch>/batches-transporte

1. Lee el rubro completo: SK/PROMPT-transporte-subcat.md. Aplícalo al pie de la letra.
   OJO reglas 1 (negocio central, no menciones) y 3 (refrigerado exige frío como identidad).
2. Baja los textos:  python3 SK/fetch_ct.py --batch BD/batch_NN.txt --outdir BD/tc_NN
3. Léelos:  for f in BD/tc_NN/ct_*.txt; do echo "=== $f ==="; cat "$f"; echo; done
4. Clasifica CADA dominio del lote.
5. Escribe BD/subcat_NN.jsonl, UNA línea JSON por dominio con el formato del rubro.
   ct vacío o placeholder -> "sin-sitio".

NO pegues el JSON en tu mensaje. Reporta solo cuántos clasificaste y la distribución
de subcategorías. Confirma que las líneas de subcat_NN.jsonl == dominios del lote.
