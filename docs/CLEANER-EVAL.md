# Evaluación del cleaner v2 — GTM web crawler

## Objetivo

Dar al LLM suficiente evidencia para decidir industria, ICP/audiencia, qué vende la
empresa, a quién le vende, si es B2B y si parece fit para outbound. Logos, clientes y
casos de éxito deben quedar localizables, sin meter todo el sitio en el prompt.

El cleaner no clasifica ni resume. Sólo crea una vista extractiva, determinista y
limitada a 10,000 caracteres. El raw/fit completo queda recuperable.

## Contrato de datos

| Campo | Propósito | Se manda al LLM |
|---|---|---:|
| `pages[].raw_markdown` | Render original por página, cuando difiere del fit | No |
| `pages[].markdown` | Contenido fit completo por página | No |
| `combined_markdown` | Fit concatenado; fallback para reprocesar datos históricos | No |
| `pages[].visual_assets` | URL, alt y página de logos/imágenes candidatas | Sólo hasta 5 pistas |
| `pages[].evidence_links` | Links a casos, clientes, portfolio o documentos | Si tienen señal útil |
| `clean_text` | Contexto priorizado y acotado para segmentación | Sí |
| `clean_meta` | Versión, tamaños y categorías presentes | Sólo para control |

## Loop de evaluación

Se usó una muestra estratificada del corpus histórico (sitios cortos, medianos, largos y
outliers) y un baseline congelado del cleaner anterior. Cada iteración se comparó contra
entidades extraídas del texto visible y seis familias de señal: `identity`, `industry`,
`offer`, `audience`, `b2b` y `proof`.

| Iteración | Muestra | Contexto mediano | Recall de entidades en clean | Recall de señales | Ruido mediano |
|---|---:|---:|---:|---:|---:|
| Baseline anterior | 240 | 8.1K chars | — | — | 6 líneas |
| v2 inicial | 80 | 6.1K chars | 98.41% | 99.79% | 0 |
| v2 corregido | 80 | 6.0K chars | 99.67% | 99.54% | 0 |
| v2.1 final | 240 | 4.8K chars | **99.92%** | **99.10%** | **0** |

Resultados finales sobre 240 sitios:

- Fuente mediana: 18,784 caracteres.
- Contexto mediano: 4,805; percentil 90: 9,926; máximo: 9,996.
- Evidencia visual localizada: 227/240 sitios.
- Enlaces de prueba/casos localizados: 203/240 sitios.
- Categorías presentes: oferta 234, identidad 226, industria 226, prueba 219,
  audiencia 207 y B2B 191.
- Todos los gates pasaron: recall de entidades >=99.5%, señales >=98%, p90 <=10K y
  ruido mediano igual a cero.

Los outliers de formato revisados no perdían evidencia visible: eran diferencias de
normalización en teléfonos, guiones Unicode y emails con énfasis Markdown. Se corrigieron
los casos generalizables. Queda un mínimo estadístico de 80% en un sitio que concatena
dos teléfonos en una sola línea; ambos números siguen visibles en el clean y el raw.

El mayor outlier tenía 5.6M caracteres por URLs de tracking repetidas. Quedó en 9.2K de
contexto; además, el crawler ahora descarta páginas que sólo difieren por parámetros
`utm`, `_ga`, `gclid` o `fbclid`.

## Gates reproducibles

```bash
python .claude/skills/gtm-web-crawler/benchmark_cleaner.py \
  --data .claude/skills/gtm-web-crawler/data/sofoms_crawls.jsonl.gz \
  --sample 240
python -m unittest tests.test_clean_markdown
```

El benchmark termina con código distinto de cero si una regresión rompe un gate. Los
tests golden cubren hechos cortos, B2B/B2C, industria/oferta/audiencia, certificaciones,
emails/teléfonos, formularios, navegación, URLs malformadas, logos y límite visual.

## Límite honesto

Una imagen sin `alt`, nombre descriptivo, link o contexto de página no permite atribuir
con seguridad qué logo o cliente representa. Se conserva su URL y página en metadata,
pero no se inventa una identidad. Si más adelante esa atribución importa, debe añadirse
una segunda pasada selectiva de DOM/OCR sólo para los candidatos ambiguos; no conviene
meter OCR masivo en este pipeline.
