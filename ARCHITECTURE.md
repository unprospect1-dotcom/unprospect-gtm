# Unprospect GTM OS — decisiones de diseño

> El mapa operativo del sistema (etapas, skills, contratos) vive en [CLAUDE.md](CLAUDE.md).
> Este documento guarda el **porqué**: principios, esquema de datos y roadmap.

## 1. Principios de diseño

1. **Memoria antes que nada.** Nada se contacta sin consultar el historial. Nada se aprende sin registrarse.
2. **Híbrido Supabase + Markdown.**
   - **Supabase** = datos consultables a escala: quién fue contactado, cuándo, con qué ángulo, qué respondió.
   - **Markdown (este repo)** = conocimiento cualitativo: perfiles de cliente, ofertas, aprendizajes. Versionado en git, legible por humanos y por skills.
3. **Cada skill aprende.** Todo skill tiene un `LEARNINGS.md` junto a su `SKILL.md` (contrato en CLAUDE.md).
4. **Separación por workspace.** Cada cliente tiene su carpeta en `workspaces/` con su propia memoria; en Supabase, columna `workspace` en todas las tablas — un esquema, datos separados por filas.
5. **El A/B testing prueba hipótesis de dolor, no cosméticos.**
6. **Dolor probable observable ≠ señales de intención.** Atributos estructurales visibles hoy (tamaño de equipo comercial, Google Ads, stack visible) — no eventos que expiran (funding, contrataciones).
7. **Skills planos, agrupados por etapa.** El pipeline tiene 5 etapas (research → list building → copywriting → launch → feedback); los skills viven planos en `.claude/skills/` y CLAUDE.md los agrupa. Sin jerarquías: un skill largo se parte en `references/` dentro de su carpeta, no en sub-skills.

## 2. Estructura del repo

```
unprospect-gtm/
├── CLAUDE.md                    ← el router: pipeline de 5 etapas, contratos, reglas duras
├── ARCHITECTURE.md              ← este documento
├── .claude/skills/gtm-*/        ← skills planos: SKILL.md + LEARNINGS.md (+ references/ si hace falta)
├── workspaces/
│   ├── _template/               ← plantilla para clientes nuevos
│   └── unprospect/              ← PROFILE, OFFERS, SEGMENTS, ANGLES, LEARNINGS, campaigns/
├── config/providers.yaml        ← toda la config de proveedores de listas (keys, límites, csv_schema)
├── lists/<ws>/                  ← CSVs generados + REPORT.md por lista (CSVs gitignoreados)
├── supabase/migrations/         ← esquema de la capa de memoria consultable
├── scripts/                     ← ejecutores de APIs (aiark, prospeo, ocean, instantly_sync)
└── segment_*.py                 ← clasificadores locales (Supabase → subsegmentos)
```

## 3. Capa de memoria en Supabase

Tabla existente: `companies` (id, name, domain, parallel_cat, vertical_broad, industry).
La migración `supabase/migrations/001_outreach_memory.sql` agrega:

| Tabla / vista | Responde a |
|---|---|
| `angles` | ¿Qué ángulos existen, qué dolor atacan, cómo van? |
| `campaigns` | ¿Qué campañas corren, en qué workspace, contra qué segmento/ángulo? Liga con `instantly_campaign_id`. |
| `outreach_log` | ¿A quién contactamos, cuándo, en qué step, con qué ángulo y campaña? **La fuente de verdad del dedupe.** |
| `replies` | Replies crudos + clasificación, ligados a campaña y ángulo. |
| `v_last_contact` | Último toque por lead con su ángulo, en un query. |
| `companies.pain_signals` (jsonb) + `companies.pain_segment` | Señales de dolor observable y segmento asignado. |

## 4. Ciclo de auto-aprendizaje

Tres niveles de memoria, del más volátil al más destilado:

1. **Datos crudos (Supabase):** cada envío, cada reply. Nunca se resume, siempre consultable.
2. **Memoria de workspace (`workspaces/<ws>/LEARNINGS.md`, `ANGLES.md`):** qué funciona *para este cliente*. La actualizan `/gtm-retro` y `/gtm-reply-analysis`.
3. **Memoria de skill (`.claude/skills/<skill>/LEARNINGS.md`):** qué funciona *como método*, transferible entre clientes.

## 5. Patrones adoptados de coldoutboundskills

Los 28 skills de Owoslawski (github.com/growthenginenowoslawski/coldoutboundskills) se auditaron y destilaron;
el vendoring se eliminó — esto es lo que quedó incorporado:

- **El contrato de aprobación** (CLAUDE.md): inferir → confirmar → muestra → 2 rondas limpias → escalar. (de `icp-onboarding`, `campaign-copywriting`, `personalization-subagent-pattern`)
- **El artefacto aprobado es el contrato:** cada skill termina en UN artefacto con estado `aprobado`; es lo único que consume el siguiente skill.
- **Positive reply rate como métrica norte** (positivos / enviados), referrals cuentan como positivo. (de `positive-reply-scoring`)
- **Una variable por experimento** — lista O copy, nunca ambas. (de `experiment-design`)
- **Gate de calidad de lista** antes de enviar: duplicados, diversidad de títulos, catch-all, fit vs ICP. (de `list-quality-scorecard`, vive en `/gtm-lists`)
- **Hard filters vs soft preferences** en ICP: tratar todo como obligatorio deja 200 leads en vez de 5,000. (de `icp-onboarding`)
- Referencia técnica de Prospeo (crawl por estado, taxonomía de industrias) → `.claude/skills/gtm-prospeo/references/`.
- Los skills atados a Smartlead sirven solo como mapa de endpoints; nuestro sender es Instantly (API v2).

## 6. Roadmap (única fuente de verdad)

Cada skill se construye, se usa en una campaña real, se afina — y hasta entonces se construye el siguiente.

1. **Hecho:** las 5 etapas con sus skills (ver CLAUDE.md); list building completo con router (`/gtm-lists`) + 3 proveedores + dedupe.
2. **Siguiente:** correr la migración en Supabase, backfill del historial de Instantly a `outreach_log`, y estrenar el ciclo completo con UNA campaña real de principio a fin.
3. **Después (etapa launch):** `/gtm-launch` — verifica artefactos `aprobado` + gate de calidad → crea la campaña en Instantly (API si el plan la incluye; mientras: paquete CSV+copy y checklist manual) → registra todo en Supabase.
4. **Luego, según lo pida el uso real:**
   - `gtm-buyer-map` — matriz de decisores por segmento (títulos exactos por proveedor, decide vs influye) → `BUYER-MAP.md`.
   - `gtm-personalize` — personalización a escala con approval loop y fan-out de sub-agents.
   - `gtm-pulse` — positive reply rate por ángulo × persona, recomendación escalar/matar/iterar.
   - Poblar `companies.pain_signals` a escala (LinkedIn, Ads Transparency, BuiltWith).

**Regla del roadmap:** no se agrega arquitectura nueva hasta que el ciclo completo haya corrido al menos una vez con una campaña real.

## 7. Estado del entorno (verificado 2026-07-02)

- Keys: Supabase ✓, Apify ✓, Attio ✓, Parallel ✓. Pendientes: `PROSPEO_KEY`, `AIARK_KEY`, `OCEAN` (ver `config/providers.yaml`).
- **Instantly:** la key autentica pero la API v2 responde 402 — el plan no incluye API (requiere Hypergrowth). Fallback: export CSV.
