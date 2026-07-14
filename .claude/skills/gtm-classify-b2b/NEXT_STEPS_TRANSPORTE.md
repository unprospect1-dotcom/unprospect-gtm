# HANDOFF: subcategorización del universo autotransporte-mx → correr en CODEX

> Estado al 2026-07-14. La corrida quedó PAUSADA a propósito — el usuario decidió
> terminarla en Codex. Lo hecho está en Supabase; lo pendiente se regenera con un comando.

## Estado

- Universo: niche `autotransporte-mx` en `list_companies` (8,410 dominios), de los cuales
  4,870 tienen crawl útil en `site_crawls` (clean_text listo).
- **Clasificados y cargados: ~420 dominios** (lotes 000–034 de la sesión Claude, modelo haiku).
  Están en `list_companies.subcat` — la regeneración de lotes los EXCLUYE sola (subcat is null).
- **Pendientes: ~4,450 dominios (~371 lotes de 12).**

## Cómo continuar (en Codex, con su modelo más barato)

```bash
cd .claude/skills/gtm-classify-b2b
# 1) regenerar lotes pendientes (resumible; excluye lo ya clasificado)
python3 make_batches_subcat.py --niche autotransporte-mx --size 12 --outdir batches-transporte

# 2) despachar UN subagente por lote con la instrucción de WORKER_SUBCAT_TRANSPORTE.md
#    (rubro: PROMPT-transporte-subcat.md — única fuente de verdad del criterio).
#    Validado en Claude: también funciona 2-3 lotes SECUENCIALES por worker (pasadas
#    independientes, escribe un jsonl por lote) — ahorra ~30% de overhead sin perder calidad.
#    NO subir de 12-15 dominios por PASADA (learning del run B2B: 40/pasada sesga).

# 3) cargar resultados (desde la raíz del repo; corre igual tras cada ola)
python3 ../../..//scripts/subcat_to_supabase.py \
    --classify "…/batches-transporte/subcat_*.jsonl" --niche autotransporte-mx --model <modelo>
```

## Capa 2 (verificación ciega) — al terminar la capa 1

Re-etiquetar SIN ver la capa 1: muestra ~10% estratificada por subcat + TODOS los
`subcat_confidence=low` + **el lote 022 completo** (quedó marcado sospechoso: 10/12
no-transporte con confianza med — puede ser tramo alfabético ruidoso legítimo, comprobar).
Salida `vsubcat_NN.jsonl` con `{domain, verify_label, confidence, evidence}` y cargar con
`--verify` (setea `subcat_agree`). Donde difieran → cola de revisión, NO se corrige a mano
sin leer el clean_text.

## Notas de la corrida Claude (para no re-aprender)

- Distribución observada en los primeros 420: ~50% transporte/logística real; densas
  forwarder-aduanal y 3pl-almacen; `refrigerado` es raro y el rubro lo protege bien
  (ej. alanis.com.mx sí; operadores con cámaras como servicio secundario → 3pl-almacen).
- Workers reportan solo conteos (el JSONL no se pega al chat) — mantenerlo así.
- La corrida en Claude se pausó por session limit del plan; los 3 workers que murieron
  a medias (019-020, 025-026, 033-034) pudieron dejar jsonl parciales en el scratchpad
  efímero — irrelevante: la regeneración por `subcat is null` limpia cualquier hueco.

## Al terminar todo

Query de distribución final:
```sql
select subcat, count(*) from list_companies
 where niche='autotransporte-mx' and subcat is not null group by subcat order by 2 desc;
```
Con eso: reporte al usuario + actualizar lists/unprospect/*-REPORT.md + LEARNINGS de este skill.
