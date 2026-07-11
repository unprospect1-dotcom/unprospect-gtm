# NEXT STEPS — terminar la clasificación B2B per-dominio (handoff a Codex)

## Estado actual (en Supabase `b2b_classification`, 962 filas)

- **200 filas VERIFICADAS y confiables** (`verified=true`): 40 golden + 160 muestra masiva,
  ambas con segundo modelo (sonnet) + adjudicación. Estas NO se tocan.
- **762 filas SIN verificar** (`verified=false`): tienen etiqueta de la primera corrida
  masiva que se hizo con **lotes de 40**, la cual **se sesga a b2b** (ver LEARNINGS.md:
  acuerdo con verificación 61%). Sirven como estimado poblacional pero **no son confiables
  per-dominio**.
- **Conteo B2B**: crudo 60% → **corregido ~46%** (b2b 46% / b2c 28% / mixed 15% / unclear 10%).
  El corregido es el bueno a nivel población.

## Objetivo pendiente

Dar etiqueta per-dominio confiable a las **762 sin verificar**, con el diseño de dos capas a
**lotes de 10** (el fix de tamaño de lote). Se intentó pero el re-run se perdió por refresh
del contenedor (los artefactos viven en `batches/`, gitignoreado).

## ⚠️ REGLA OPERATIVA CRÍTICA

**Carga cada oleada a Supabase apenas termina.** Los archivos `batches/*.jsonl` son
gitignoreados y se PIERDEN si el contenedor se refresca. No acumules 20 lotes en disco: en
cuanto tengas ~5-10 `rcls_NN.jsonl`, córrelos con `load_supabase.py`. Supabase es la única
fuente de verdad durable.

## Receta (misma en Claude Code y Codex; usa el mecanismo de subagentes del harness)

```bash
SK=.claude/skills/gtm-classify-b2b
cd $SK

# 1) generar lotes de SOLO los no verificados (excluye los ya en la tabla verificados)
#    Nota: make_batches excluye lo que ya está en b2b_classification. Para re-clasificar los
#    762 (que YA están en la tabla) genera los lotes desde los verified=false:
python3 - <<'PY'
import os,requests,math
U=os.environ["SUPABASE_URL"].rstrip("/");K=os.environ["SUPABASE_SERVICE_ROLE_KEY"]
H={"apikey":K,"authorization":f"Bearer {K}"}
rows=[];off=0
while True:
    r=requests.get(f"{U}/rest/v1/b2b_classification",params={"select":"domain,verified","limit":"1000","offset":str(off)},headers=H,timeout=60);js=r.json()
    if not js:break
    rows+=js
    if len(js)<1000:break
    off+=1000
todo=sorted(x["domain"] for x in rows if not x["verified"])
os.makedirs("batches",exist_ok=True)
for i in range(math.ceil(len(todo)/10)):
    open(f"batches/re_{i:02d}.txt","w").write("\n".join(todo[i*10:(i+1)*10])+"\n")
print("lotes:",math.ceil(len(todo)/10),"de",len(todo),"dominios")
PY

# 2) CAPA 1: 1 subagente por lote (modelo barato: haiku / codex-mini), sigue WORKER_CLASSIFY.md
#    con su NN. Dispara en oleadas de ~10-15. Cada subagente escribe batches/rcls_NN.jsonl.
#    OJO límites de sesión: si truena, reanuda (los rcls_NN.jsonl ya hechos se conservan si
#    los cargaste a Supabase; si no, re-despacha los que falten).

# 3) CARGA capa 1 apenas tengas lotes hechos (repite seguido):
python3 load_supabase.py --classify "batches/rcls_*.jsonl" --model haiku-b10
#   (esto pone verified=false; es capa 1 mejorada. La verificación viene en el paso 4.)

# 4) CAPA 2 verificación CIEGA: 1 subagente por lote con modelo DISTINTO (sonnet / codex más
#    fuerte), sigue WORKER_VERIFY.md. Escribe batches/rver_NN.jsonl.

# 5) CARGA con verificación (calcula verify_agree):
python3 load_supabase.py --classify "batches/rcls_*.jsonl" --verify "batches/rver_*.jsonl" --model haiku-b10

# 6) ADJUDICAR desacuerdos (donde capa1 != capa2): léelos tú (el orquestador) y decide.
#    Son ~10-30% y casi siempre frontera b2b/mixed/b2c.
```

```sql
-- desacuerdos a adjudicar
select domain, label, verify_label, confidence from b2b_classification
where verified and not verify_agree;
-- conteo B2B confiable final
select label, count(*) from b2b_classification where verify_agree group by label;
```

## Consejo de escala
762 dominios a lotes de 10 = ~77 subagentes por capa. Es mucho para una sesión (topa
límites). Hazlo en tandas across resets, cargando a Supabase cada tanda. La alternativa
"1-a-1" (un subagente por dominio) da máxima precisión pero son ~1500 spawns.
