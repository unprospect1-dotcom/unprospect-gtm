# LEARNINGS — gtm-classify-b2b

## Validación inicial (sample de 40 dominios SOFOM, estratificado por tamaño de clean_text)

Verdad-base: 40 dominios etiquetados a mano leyendo el clean_text completo (`golden`).
Distribución tras adjudicar: 23 b2b · 7 b2c · 7 mixed · 3 unclear.

| comparación | acuerdo |
|---|---|
| haiku (capa 1) ↔ sonnet (capa 2), ciego | **95%** (38/40) |
| haiku ↔ verdad-base | 92% (37/40) |
| sonnet ↔ verdad-base | 92% (37/40) |
| los tres coinciden | 90% (36/40) |

**Todas** las discrepancias cayeron en casos marcados "hard" — empresas de frontera que de
verdad sirven a varios segmentos (afalianza, cualli, inyecta, patrimonio). **Ningún caso
claro se clasificó mal.** Conclusión: la precisión residual es ambigüedad irreducible, no un
bug del prompt. Por eso el diseño no busca 100% — busca **coincidencia de dos capas** y
marca el resto para revisión.

## Reglas que costó aprender (están en PROMPT.md)

1. **Objeto social ≠ producto.** `solvantia.com` dice en su texto legal "otorgamiento de
   crédito, arrendamiento y factoraje" (suena b2b) pero su único producto real/hero es
   "préstamo vía nómina" a la persona → **b2c**. El objeto social es boilerplate; clasificar
   por lo que el sitio OFRECE, no por lo que la razón social permite.
2. **No truncar el clean_text.** La verdad-base inicial se hizo con 1.6K chars y falló en
   `lumofinancieradelcentro.com`: los primeros 1.6K eran puro banner de cookies; el hero real
   ("Sector Gobierno, Estados y Municipios" → b2b) venía después. Alimentar ≥7–8K chars.
   Los subagentes que vieron 7K acertaron donde la verdad-base truncada falló.
3. **Nómina depende del destinatario.** `impulso-mas`/`solvantia` (al trabajador) → b2c;
   `vinlasofom` (a la empresa como prestación para empleados) → b2b.
4. **Casos b2b no obvios:** software para financieras (`flexcapital.lendus`), captable/SPV
   para founders (`arcafinanciera`, "no damos créditos"), sector gobierno (`lumo`,
   `infratek`), y el que declara "no atendemos personas físicas" (`opcr`).

## Diseño que quedó "a prueba de balas"

- **Solo subagentes del harness** (agnóstico Claude Code ↔ Codex): nada de servicios externos.
- Capa 1 barata en masa: subagentes con el modelo más barato (haiku / codex-mini / …).
- Capa 2 verificación **ciega** e independiente (subagentes de otro modelo, idealmente más
  fuerte), sobre sample + todos los `low`/`mixed`/`unclear`.
- **verify_agree** en Supabase: `true` = confiar; `false` = cola de revisión humana
  (en la validación fue solo el 5%, todo frontera).
- El conteo B2B se reporta con banda: consenso (ambas capas b2b) … cualquiera (alguna b2b).

## Corrida completa (962 SOFOMs) y el hallazgo del tamaño de lote

Primera corrida masiva: subagentes haiku a **40 dominios/lote**. La verificación ciega
(sonnet, muestra estratificada de 160) reveló el problema:

- Acuerdo capa1↔capa2 en el run masivo: **solo 61%** (vs 95% en el sample de 40 con lotes
  de 10). El modelo barato, con 40 items por subagente, trabaja sloppy y **se sesga a b2b**.
- Matriz de confusión: de lo que haiku marcó "b2b", sonnet confirmó 61%, movió 18% a b2c,
  15% a mixed, 6% a unclear. Adjudiqué 6/6 desacuerdos a mano → **sonnet tenía razón las 6
  veces** (gocredit=jubilados/nómina→b2c; impulsofinanciero/invex=PyME+personal→mixed; etc.).
- Conteo B2B: crudo **60%** (579/962) → corregido por confusión **~46%** (443/962).
  Distribución corregida: b2b 46% · b2c 28% · mixed 15% · unclear 10%.

**Regla dura:** el clasificador barato corre en **lotes ≤12-15**. A 40 se degrada y sobre-
llama b2b. `make_batches.py` ahora usa `--size 12` por defecto. Los `b2c`/`unclear` del
modelo barato son más confiables que sus `b2b`/`mixed` (esos hay que verificar sí o sí).

**Estado de los datos en Supabase:** 200 filas con verificación real (40 golden + 160
muestra masiva); el resto son capa1 haiku-40 (sesgado, `verified=false`). Para etiquetas
per-dominio confiables en los 762 restantes hay que re-correr la capa 1 a lotes chicos.

## Patrón de subagente (capa 1 haiku o capa 2 sonnet)

Cada subagente: (1) corre un fetch que baja clean_text de `site_crawls` a `ct_<dom>.txt`,
(2) lee cada archivo, (3) clasifica con el rubro de PROMPT.md, (4) escribe un array JSON.
Los verificadores van **ciegos** (no ven las etiquetas de la capa 1). Batch máximo de
12–15 dominios por subagente.

## Validación Codex GPT-5.4 Mini — 2026-07-16

Prueba controlada con dos subagentes ciegos `gpt-5.4-mini`, esfuerzo `low`, sobre 8 casos
del golden deliberadamente cargados de fronteras: 3 b2b, 3 b2c y 2 mixed.

- Con el prompt anterior, ambos agentes coincidieron 8/8 entre sí pero solo 6/8 contra el
  golden. Los dos errores fueron sistemáticos: `afalianza.com` se fue a b2b en vez de mixed
  y `patrimonio.com.mx` a mixed en vez de b2c.
- Agregar las reglas 9 y 10 de prominencia corrigió ambos casos: los dos agentes quedaron
  8/8 contra el golden y 8/8 entre sí. Es una muestra pequeña; antes de corrida masiva hay
  que repetir en una muestra mayor y variada.
- La evidencia necesita validación literal automática. En Windows PowerShell 5,
  `Get-Content` sin `-Encoding UTF8` puede mostrar texto sano como mojibake
  (`nómina` → `nÃ³mina`). Un worker leyó así el archivo y devolvió citas no literales.
  El `clean_text` original estaba bien al comprobar sus bytes como UTF-8. No aceptar
  evidencia sin comprobar que la cita esté contenida en el `clean_text`, y leer siempre
  los archivos con UTF-8 explícito.
