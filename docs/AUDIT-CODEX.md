# Auditoría técnica y de arquitectura — Unprospect GTM OS

Fecha: 2026-07-16
Base auditada: `main` en `10a8f95`
Alcance: arquitectura, instrucciones para agentes, skills activos y de referencia, scripts,
datos, migraciones, seguridad, pruebas y eficiencia operativa.

## Veredicto ejecutivo

La idea central es buena: Markdown guarda conocimiento cualitativo versionable, Supabase guarda
eventos consultables y los skills convierten el proceso comercial en workflows repetibles. El diseño
de memoria por workspace y el loop de aprendizaje son diferenciadores reales.

Antes de este cambio, el repositorio no era descubrible por Codex: sólo tenía `.claude/skills/` y no
tenía `AGENTS.md`. La adaptación quedó resuelta de forma aditiva: Claude Code conserva intacto su
mecanismo y Codex usa adaptadores en `.agents/skills/` que cargan la misma fuente canónica.

La arquitectura es eficiente para exploración asistida, research y operaciones supervisadas. Todavía
no es suficientemente robusta para automatización desatendida de producción: los gates de gasto viven
principalmente en instrucciones, la sincronización de Instantly no es idempotente y no existe una
política de RLS declarada para datos sensibles.

## Snapshot del repositorio base

- 183 archivos trackeados; ~20 MB.
- 16 skills activos en `.claude/skills/`.
- 28 skills de referencia no activos en `reference/coldoutboundskills/`.
- 28 archivos Python.
- 7 migraciones Supabase en la base auditada; 8 después de este cambio.
- 19 artefactos Markdown en `workspaces/`.
- Las mayores piezas son datos generados: crawl comprimido (~7.5 MB), `segment_results.json`
  (~7.3 MB), `subagent_results.json` (~2.2 MB) y otros queues/resultados.

## Cómo funciona el sistema completo

1. `gtm-onboard` crea el perfil persistente del cliente.
2. El crawler y enrichment obtienen dominios, LinkedIn y contenido de sitios.
3. `gtm-classify-b2b` determina a quién vende cada empresa con verificación independiente.
4. `gtm-pain-segments` construye segmentos desde atributos observables.
5. `gtm-offer-ideation` y `gtm-campaign-ideation` convierten segmento + dolor en ofertas y ángulos.
6. GetLeads, AI Ark, Ocean o Prospeo enumeran empresas/personas bajo gates de costo.
7. `gtm-check-contact` deduplica contra la memoria histórica.
8. `gtm-copy` y `gtm-experiments` producen copy y tests con una sola variable.
9. Instantly ejecuta; `instantly_sync.py` trae envíos/replies a Supabase.
10. `gtm-reply-analysis` y `gtm-retro` convierten respuestas en aprendizaje de workspace y método.

La separación de responsabilidades es conceptualmente correcta. El principal hueco está entre las
instrucciones y la ejecución: falta una capa programática común que haga cumplir presupuestos,
idempotencia, manifests de corrida y gates de aprobación.

## Compatibilidad Claude Code y Codex

### Implementado

- `AGENTS.md`: guía durable de estructura, seguridad, gasto, subagentes y verificación para Codex.
- `.agents/skills/<skill>/SKILL.md`: 16 adaptadores de descubrimiento.
- `.claude/skills/`: sigue siendo la fuente canónica de lógica, scripts y `LEARNINGS.md`.
- `docs/CODEX-COMPATIBILITY.md`: equivalencias de invocación, herramientas y modelos.
- `scripts/check_agent_compat.py`: valida paridad uno-a-uno entre skills de Claude y Codex.
- Tests y CI: fallan si un skill queda disponible sólo en uno de los dos harnesses.

### Por qué no se copiaron los skills completos

Copiar 16 directorios a `.agents/skills/` habría creado dos fuentes de verdad. Los adaptadores permiten
que Codex descubra los workflows con `name`/`description`, pero cargan el skill, scripts y learnings
canónicos desde `.claude/skills/`. Esto preserva Claude Code y elimina drift de contenido.

### Límite conocido

`gtm-web-crawler/setup.sh` asume Bash/Linux, `apt-get`, un Chromium preinstalado y una topología de
proxy específica. Codex en Windows necesita WSL o un contenedor. El resto de los adaptadores no depende
de un shell específico, salvo comandos `python3` que Codex debe traducir a `python` en Windows.

## Auditoría de los 16 skills activos

| Skill | Qué hace | Entradas y salidas | Dependencias / riesgo principal |
|---|---|---|---|
| `gtm-onboard` | Investiga negocio, ICP, pricing, competidores y dolores observables. | URL + workspace → `PROFILE.md`. | Usa web; requiere confirmar inferencias con el usuario. |
| `gtm-pain-segments` | Convierte atributos observables en segmentos accionables. | Perfil/base → `SEGMENTS.md` + señales en `companies`. | El scoring es heurístico; necesita sizing real. |
| `gtm-offer-ideation` | Diseña lead magnets/front-end offers por segmento. | Segmentos → `OFFERS.md`. | Debe controlar costo de fulfillment si escala. |
| `gtm-campaign-ideation` | Combina segmento, dolor, offer y credibilidad en ángulos. | Memoria + métricas → `ANGLES.md`, `angles`, `BRIEF.md`. | Depende de que `angles` y Markdown estén sincronizados. |
| `gtm-experiments` | Pre-registra y evalúa A/B de hipótesis de dolor. | Brief/resultados → matriz y `RESULTS.md`. | La regla de ≥300 por variante es práctica, no cálculo estadístico formal. |
| `gtm-check-contact` | Dedupe e historial antes de campaña. | Lead/CSV → veredicto + CSV filtrado. | Depende de que Instantly esté sincronizado de forma completa e idempotente. |
| `gtm-copy` | Produce secuencias y variantes con frameworks definidos. | Brief + voz del cliente → `COPY.md`. | Referencia skills `/unprospect-*` que no están en este repo. |
| `gtm-reply-analysis` | Clasifica replies y extrae lenguaje/objeciones. | Instantly/Supabase/CSV → clases, rates y learnings. | Guarda cuerpo de emails: dato sensible que requiere RLS/retención. |
| `gtm-retro` | Destila evidencia a memoria de cliente y método. | Resultados + correcciones → `LEARNINGS.md`. | Las escrituras concurrentes deben fusionarse sólo por el agente principal. |
| `gtm-getleads` | Conteos gratis, DM-unión, lists, enrichment y señales. | Buyer map/filtros → CSV + report + Supabase. | Workflow excelente, pero presupuesto/aprobación no se fuerza en el ejecutor. |
| `gtm-lists-aiark` | Búsqueda/export con email, lookalikes y exclusiones. | Segmento/filtros → CSV normalizado. | Search consume 0.5 crédito por perfil; riesgo de paginar de más. |
| `gtm-ocean` | Lookalikes semánticos y reveal de contactos. | 3–10 seeds → empresas/personas/emails. | La documentación tenía costos contradictorios; este cambio la alinea a 0.2 por company result medido. |
| `gtm-prospeo` | Search y enrichment de personas/empresas. | Filtros o CSV → lista/enrichment. | Search, email y mobile tienen economías distintas; mobile requiere gate fuerte. |
| `gtm-enrich-web` | Encuentra dominio/LinkedIn con Parallel y verificación agentic. | CSV/tabla incompleta → datos verificados. | Costoso en tokens; batches y persistencia deben ser resumibles. |
| `gtm-web-crawler` | Renderiza sitios, prioriza páginas útiles y limpia contenido. | Dominio(s) → JSON/`site_crawls.clean_text`. | Bootstrap POSIX y dependencias pesadas; Cloudflare requiere capa B. |
| `gtm-classify-b2b` | Clasifica B2B/B2C/mixed/unclear con verificación ciega. | `clean_text` → `b2b_classification`. | Buen patrón de doble pasada; el costo crece con muchos subagentes. |

## Auditoría de scripts y ejecutores

### Clientes de proveedor

| Archivo | Función |
|---|---|
| `scripts/getleads.py` | CLI genérico para health, créditos, count, search, export, lookup, enrich, filtros y señales. |
| `scripts/aiark.py` | CLI para saldo, búsqueda de companies/people, export, resultados y exclusion lists. |
| `scripts/ocean.py` | CLI para balance, warmup, company/people search, reveal y enrich. |
| `scripts/prospeo.py` | CLI para search paginado, enrichment simple/bulk y cuenta. |

Los cuatro repiten auth, retries, timeouts y parsing. Funcionan como adaptadores delgados, pero no leen
directamente `providers.yaml` ni fuerzan `credit_budget`; los skills deben pasar parámetros correctos.
Recomendación: una librería `provider_runtime.py` con config, rate limit, dry-run, ledger y hard caps.

### Pipelines operativos

| Archivo | Función | Observación |
|---|---|---|
| `scripts/instantly_sync.py` | Copia envíos y replies de Instantly a Supabase. | No probado en vivo; los envíos no tienen ID único y pueden duplicarse al re-sincronizar. |
| `scripts/lists_to_supabase.py` | Normaliza CSV de empresas y upserta `list_companies`. | Buen punto de persistencia durable; los campos no conocidos van a `meta`. |
| `scripts/sales_counts.py` | Cuenta ventas por dominio/nicho en GetLeads. | Resumible, pero duplicado por el contador unificado. |
| `scripts/marketing_counts.py` | Cuenta marketing por dominio/nicho. | Espejo de ventas; también sustituible por el unificado. |
| `scripts/dept_counts.py` | Cuenta ventas + marketing sobre dominios únicos y propaga a nichos. | Debe ser el camino canónico; reduce llamadas duplicadas. |
| `scripts/ads_transparency.py` | Detecta Google Ads vía Apify y persiste flags. | Rota tokens y tiene costo real; ahora sus columnas viven en migración 008. |
| `scripts/aiark_rescue.py` | Revisa falsos cero de ventas de GetLeads con AI Ark. | Acotado a sospechosos; gasto de 0.5 por dominio con perfiles. |
| `scripts/subcat_to_supabase.py` | Fusiona clasificación y verificación de subcategoría. | Ahora su contrato de columnas está en migración 008. |

### Scripts raíz / legado

| Archivo | Función | Veredicto |
|---|---|---|
| `segment_companies.py` | Clasificador determinista de subsegmentos logísticos y export JSON/CSV. | Es el único dominio con tests unitarios previos. |
| `subagent_workflow.py` | Simula especialistas por keywords y priorización. | No crea subagentes reales; el nombre induce a error. |
| `segment_industries.py` | Cuenta/bucketiza verticales desde Supabase. | Ejecuta red al importarse; conviene convertirlo a CLI. Su encoding roto quedó corregido. |
| `count_transport.py` | Cuenta empresas con señales de transporte. | Exploratorio; también ejecuta al importarse y se solapa con clasificadores posteriores. |

### Helpers dentro de skills

- `gtm-web-crawler`: `setup.sh`, `crawl.py`, `sandbox_browser.py`, `clean_markdown.py` y
  `load_supabase.py` forman un pipeline coherente de bootstrap → crawl → limpieza → persistencia.
- `gtm-classify-b2b`: `make_batches.py`, `fetch_ct.py`, worker prompts y `load_supabase.py` hacen el
  proceso resumible y verificable.
- `gtm-enrich-web`: `parallel_enrich.py`, `content_check.py` y `full_domain_run.py` implementan la
  capa masiva y el triage. El skill es más maduro que la documentación raíz.

## Auditoría de Supabase

| Migración | Qué crea/cambia |
|---|---|
| `001_outreach_memory.sql` | `angles`, `campaigns`, `outreach_log`, `replies`, `v_last_contact` y pain signals. |
| `002_sofoms.sql` | Padrón SOFOM y liga opcional a `companies`. |
| `003_site_crawls.sql` | Crawl crudo y `clean_text`; este cambio corrige el contrato faltante. |
| `004_b2b_classification.sql` | Etiqueta B2B/B2C y verificación independiente. |
| `005_list_companies.sql` | Registro durable de empresas por nicho. |
| `006_marketing_counts.sql` | Conteo/bucket de marketing. |
| `007_aiark_sales_count.sql` | Conteo alterno de ventas para blind spots. |
| `008_operational_signals.sql` | Flags de Ads y clasificación/verificación de subcategoría usados por scripts. |

### Hallazgos de datos

- La separación por `workspace` es consistente en outreach, campañas y replies, pero no todas las
  tablas de research usan workspace; `site_crawls` y `b2b_classification` son globales por dominio.
  Esto es razonable si el dominio es conocimiento compartido, pero debe quedar explícito.
- `outreach_log` no tiene una clave idempotente del proveedor. `instantly_sync.py` reinsertará envíos
  al repetir una sincronización porque el UUID se genera de nuevo.
- El sync deja `campaign_id` y `angle_slug` nulos aunque el comentario dice que se resuelven mediante
  `instantly_campaign_id`; no existe ese join en el código.
- Las migraciones no habilitan RLS ni documentan políticas. `replies.body` y `lead_email` requieren una
  decisión explícita de acceso y retención antes de exponer estas tablas a clientes anon/authenticated.
- No hay tests de migración contra un Postgres/Supabase efímero; los tests nuevos verifican contrato de
  columnas, no ejecución SQL real.

## Memoria y artefactos Markdown

- `workspaces/_template/` define PROFILE, SEGMENTS, OFFERS, ANGLES y LEARNINGS.
- `workspaces/unprospect/` contiene la memoria real, buyer map, signals y playbooks.
- `lists/<workspace>/*-REPORT.md` registra universos y resultados operativos.
- `.claude/skills/<skill>/LEARNINGS.md` guarda conocimiento transferible entre clientes.

Fortaleza: todo es legible, versionable y fácil de corregir. Debilidad: el estado `aprobado`, las
dependencias entre artefactos y el ID de corrida no tienen un esquema machine-readable común. Para
automatizar, conviene un `RUN.json` o frontmatter estándar con `run_id`, `workspace`, `status`,
`inputs`, `outputs`, `provider_cost`, `approved_by` y hashes de inputs.

## Los 28 skills de referencia

No son activos; sirven para patrones y comparación. Están bien aislados fuera de `.claude/skills` y
`.agents/skills`, así que no contaminan el descubrimiento de agentes.

- Estrategia/onboarding: `campaign-copywriting`, `campaign-strategy`, `cold-email-kickoff`,
  `icp-onboarding`, `lead-magnet-brainstorm`, `experiment-design`.
- List building/research: `auto-research-public`, `blitz-list-builder`, `competitor-engagers`,
  `disco-like`, `google-maps-list-builder`, `prospeo-full-export`, `prospeo-search-api`.
- Personalización/calidad: `icp-prompt-builder`, `personalization-subagent-pattern`,
  `positive-reply-scoring`, `list-quality-scorecard`, `spam-word-checker`, `smartlead-spintax`.
- Delivery/operación: `cold-email-starter-kit`, `cold-email-weekly-rhythm`,
  `deliverability-incident-response`, `deliverability-test-public`, `email-deliverability-audit`,
  `smartlead-api`, `smartlead-campaign-upload-public`, `smartlead-inbox-manager`,
  `zapmail-domain-setup-public`.

El repositorio es público y no contiene `LICENSE`/`NOTICE`. Antes de reutilizar o distribuir los
scripts de referencia, hay que confirmar la licencia del origen y definir una licencia para este repo.

## Hallazgos priorizados

### P1 — resolver antes de automatización desatendida

1. **Instantly sync no idempotente e incompleto.** Agregar `instantly_email_id` único a
   `outreach_log`, enviarlo desde el sync, resolver `campaign_id`/`angle_slug` y probar con fixtures
   reales anonimizados. No lanzar un cron hasta resolverlo.
2. **RLS/retención no declarados.** Definir si el acceso será sólo service role o por usuario/workspace;
   habilitar RLS y políticas, y fijar retención/redacción para cuerpos de replies.
3. **Gasto protegido sólo por prompts.** Llevar `max_per_run`, `reserve`, estimación y confirmación a
   código compartido; `--dry-run` debe ser default para exports/reveals/campañas.

### P2 — alto retorno de eficiencia y mantenibilidad

4. **Pruebas insuficientes.** La base tenía 4 tests de un clasificador. Añadir fixtures para provider
   clients, retries/429, paginación, normalización CSV y sync idempotente.
5. **Clientes HTTP duplicados.** Consolidar auth, retry/backoff, rate limit, redacción y telemetría.
6. **Scripts exploratorios con side effects al importar.** Convertir `count_transport.py` y
   `segment_industries.py` a `main()` + argparse; renombrar `subagent_workflow.py` a algo que refleje
   que es un ensemble determinista.
7. **Outputs grandes en Git.** Mover resultados regenerables a Supabase/objeto storage o Git LFS;
   mantener sólo manifests y muestras pequeñas versionadas.
8. **Crawler no portable.** Añadir contenedor reproducible o bootstrap separado POSIX/Windows.
9. **Artefactos sin contrato común.** Estandarizar estado, lineage, aprobación y costo por corrida.
10. **Licencia ausente.** Definir licencia propia y atribución/licencia del material de referencia.

### P3 — mejoras de producto

11. Implementar los gaps ya reconocidos: `gtm-personalize`, `gtm-launch`, `gtm-pulse` y un
    list-quality gate antes de lanzamiento.
12. Sustituir umbrales fijos de A/B por cálculo de potencia/confianza cuando haya suficiente volumen.
13. Añadir observabilidad por run: duración, créditos, filas, match rate, retries y errores por proveedor.

## Cambios realizados durante esta auditoría

- Compatibilidad Codex aditiva con 16 adaptadores y `AGENTS.md`.
- Checker de paridad Claude/Codex y GitHub Actions.
- Documentación de equivalencias y actualización de README/arquitectura.
- Corrección UTF-8 de `segment_industries.py`, que no compilaba bajo Python 3.
- Corrección de `site_crawls.clean_text` en migración y loader.
- Migración 008 para eliminar schema drift de Ads y subcategorías.
- Alineación del costo medido de Ocean company search en skill, config y plan.
- Dependencia `requests` declarada.
- Tests de compatibilidad y contrato de esquema.

## Orden recomendado de siguientes cambios

1. Idempotencia de Instantly + fixtures.
2. RLS y política de retención.
3. Runtime común de proveedores con dry-run y hard budgets.
4. Manifests de corrida/aprobación.
5. Consolidación de scripts y más tests.
6. Contenedor del crawler y limpieza de blobs del historial futuro.

Con esos seis pasos, el sistema pasa de “OS muy útil con operador humano” a una base razonablemente
segura para ejecución recurrente por Claude Code o Codex.
