# Unprospect GTM OS — Arquitectura del Cold Outbound Machine

> Objetivo: una máquina de cold outbound que **recuerda todo**, **aprende de cada uso**
> y **encadena skills** desde la segmentación hasta el análisis de replies.

## 1. Principios de diseño

1. **Memoria antes que nada.** Nada se contacta sin consultar el historial. Nada se aprende sin registrarse.
2. **Híbrido Supabase + Markdown.**
   - **Supabase** = datos consultables a escala: quién fue contactado, cuándo, con qué ángulo, qué respondió.
   - **Markdown (este repo)** = conocimiento cualitativo: perfiles de cliente, ofertas, aprendizajes, playbooks. Versionado en git, legible por humanos y por skills.
3. **Cada skill aprende.** Todo skill tiene un `LEARNINGS.md` junto a su `SKILL.md`. Lo lee al empezar, lo actualiza al terminar. Así el sistema mejora con cada uso.
4. **Separación por workspace.** Cada cliente (empezando por `unprospect`) tiene su carpeta en `workspaces/` con su propia memoria. Los skills siempre operan sobre un workspace explícito.
5. **El A/B testing prueba hipótesis de dolor, no cosméticos.** La variable de un experimento es el dolor probable que ataca el copy — no el subject line ni el CTA.
6. **Dolor probable observable ≠ señales de intención.** Segmentamos por atributos observables hoy (tamaño de equipo comercial, si corren Google Ads, stack visible, # de reviews) — no por eventos como contrataciones o funding.

## 2. Mapa del sistema

```
┌─────────────────────────────  ONBOARDING (1 vez por cliente)  ─────────────────────────────┐
│  /gtm-onboard  →  lee website + fuentes, analiza el negocio  →  workspaces/<ws>/PROFILE.md │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
┌─────────────────────────────  ESTRATEGIA (por ciclo)  ─────────────────────────────────────┐
│  /gtm-pain-segments     →  segmentos por dolor observable      →  SEGMENTS.md + Supabase   │
│  /gtm-offer-ideation    →  front-end offers / lead magnets     →  OFFERS.md                │
│  /gtm-campaign-ideation →  ángulos (segmento × dolor × oferta) →  ANGLES.md + tabla angles │
│  /gtm-experiments       →  diseño del A/B de dolor probable    →  brief de experimento     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
┌─────────────────────────────  EJECUCIÓN (por campaña)  ────────────────────────────────────┐
│  /gtm-check-contact  →  ¿ya está en la base? ¿cuándo y con qué ángulo?  (Supabase)         │
│  /unprospect-recipes → /unprospect-research → /unprospect-messages   (skills existentes)   │
│  /gtm-copy           →  copy por framework + variantes A/B por hipótesis de dolor          │
│  Subida a Instantly  →  registrar cada envío en outreach_log                               │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                            │
┌─────────────────────────────  APRENDIZAJE (continuo)  ─────────────────────────────────────┐
│  /gtm-reply-analysis →  clasifica replies de Instantly, liga reply → ángulo → dolor        │
│  /gtm-retro          →  destila resultados en LEARNINGS.md (workspace y skills)            │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 3. Estructura del repo

```
unprospect-gtm/
├── ARCHITECTURE.md              ← este documento
├── AGENTS.md                    ← reglas persistentes para Codex
├── .agents/skills/              ← adaptadores Codex (descubrimiento; sin lógica duplicada)
├── .claude/skills/              ← fuente canónica de los skills para ambos agentes
│   ├── gtm-onboard/             SKILL.md + LEARNINGS.md
│   ├── gtm-check-contact/
│   ├── gtm-pain-segments/
│   ├── gtm-offer-ideation/
│   ├── gtm-campaign-ideation/
│   ├── gtm-copy/
│   ├── gtm-experiments/
│   ├── gtm-reply-analysis/
│   ├── gtm-retro/
│   └── ...                      16 skills activos en total
├── workspaces/
│   ├── _template/               ← plantilla para clientes nuevos (copiar y renombrar)
│   └── unprospect/              ← tu propio workspace
│       ├── PROFILE.md           negocio, ICP, análisis del website
│       ├── OFFERS.md            catálogo de front-end offers / lead magnets
│       ├── SEGMENTS.md          segmentos por dolor observable
│       ├── ANGLES.md            ángulos probados y su estado
│       ├── LEARNINGS.md         qué funciona y qué no (destilado)
│       └── campaigns/           un directorio por campaña (BRIEF, COPY, RESULTS)
├── supabase/migrations/         ← esquema de la capa de memoria consultable
├── scripts/                     ← sync con Instantly, clasificación local
└── segment_*.py                 ← clasificadores existentes (Supabase → subsegmentos)
```

La compatibilidad es aditiva: Claude Code sigue leyendo `.claude/skills/`. Codex descubre
`.agents/skills/`, y cada adaptador carga el workflow canónico correspondiente. El checker
`scripts/check_agent_compat.py` impide que aparezca un skill en un harness y falte en el otro.

## 4. Capa de memoria en Supabase

Tabla existente: `companies` (id, name, domain, parallel_cat, vertical_broad, industry).
La migración `supabase/migrations/001_outreach_memory.sql` agrega:

| Tabla / vista | Responde a |
|---|---|
| `angles` | ¿Qué ángulos existen, qué dolor atacan, qué framework usan, cómo van? |
| `campaigns` | ¿Qué campañas corren, en qué workspace, contra qué segmento, con qué ángulo? Liga con `instantly_campaign_id`. |
| `outreach_log` | ¿A quién contactamos, cuándo, en qué step, con qué ángulo y campaña? **La fuente de verdad del dedupe.** |
| `replies` | Replies crudos + clasificación (positive / objection / referral / negative / ooo) ligados a campaña y ángulo. |
| `v_last_contact` | Vista: último toque por lead con su ángulo — la pregunta "¿cuándo fue la última vez y con qué ángulo?" en un query. |
| `companies.pain_signals` (jsonb) + `companies.pain_segment` | Señales de dolor observable por empresa y el segmento asignado. |

Regla: **todo envío desde Instantly se refleja en `outreach_log`** (vía `scripts/instantly_sync.py` o al subir la campaña). Si no está en el log, no pasó.

## 5. Ciclo de auto-aprendizaje (cómo "se vuelve mejor cada que se usa")

Tres niveles de memoria, del más volátil al más destilado:

1. **Datos crudos (Supabase):** cada envío, cada reply, cada métrica. Nunca se resume, siempre consultable.
2. **Memoria de workspace (`workspaces/<ws>/LEARNINGS.md` y `ANGLES.md`):** qué ángulos/dolores/segmentos funcionan *para este cliente*. Lo actualiza `/gtm-retro` y `/gtm-reply-analysis`.
3. **Memoria de skill (`.claude/skills/<skill>/LEARNINGS.md`):** qué funciona *como método*, independiente del cliente (ej. "los lead magnets de benchmark superan a los templates en logística"). Es canónica y compartida por Claude Code y Codex; cada skill la lee al arrancar y agrega entradas al terminar.

Contrato de todo skill:
- **Al empezar:** leer su `LEARNINGS.md` + el `PROFILE.md` y `LEARNINGS.md` del workspace activo.
- **Al terminar:** si hubo un hallazgo, decisión o corrección del usuario → registrarla con fecha en el `LEARNINGS.md` correspondiente.

## 6. Separación por cliente

- Un cliente nuevo = copiar `workspaces/_template/` → `workspaces/<cliente>/` y correr `/gtm-onboard <cliente> <website>` en Claude Code o `$gtm-onboard <cliente> <website>` en Codex.
- Todas las tablas de Supabase llevan columna `workspace` — un solo esquema, datos separados por filas.
- Los skills piden el workspace como primer argumento; si no se da, asumen `unprospect`.
- El conocimiento *transferible entre clientes* sube al `LEARNINGS.md` del skill; lo *específico del cliente* se queda en su workspace.

## 7. Relación con los skills existentes y con coldoutboundskills

- `/unprospect-recipes` → `/unprospect-research` → `/unprospect-messages` siguen siendo la cadena de ejecución por lead. Los skills nuevos los envuelven: `gtm-check-contact` filtra antes, `gtm-copy` y la memoria alimentan después. Cuando quieras, se migran a `.claude/skills/` de este repo para que todo viva junto.
- **Los 28 skills de Owoslawski viven en `reference/coldoutboundskills/`** (github.com/growthenginenowoslawski/coldoutboundskills) como **inspiración, no producto**: no son skills activos — construimos los nuestros uno por uno robando sus mejores patrones (ver `docs/SKILL-AUDIT.md` para la auditoría y el orden de construcción). Cómo se relacionan con los `gtm-*`:
  - **Equivalentes conceptuales** (nuestra versión agrega memoria por workspace + auto-aprendizaje, la de él no lo tiene): `icp-onboarding`→`gtm-onboard`, `lead-magnet-brainstorm`→`gtm-offer-ideation`, `campaign-strategy`→`gtm-campaign-ideation`, `positive-reply-scoring`→`gtm-reply-analysis`, `experiment-design`→`gtm-experiments`. Usar los `gtm-*` como default; los de él como segunda opinión / checklist.
  - **Adoptables tal cual** (no tenemos equivalente): `spam-word-checker`, `smartlead-spintax` (el spintax aplica igual en Instantly), `list-quality-scorecard`, `icp-prompt-builder`, `personalization-subagent-pattern` (fan-out de personalización con sub-agents — clave para escalar), `cold-email-weekly-rhythm` (la cadencia operativa), `deliverability-incident-response`, `email-deliverability-audit`.
  - **List building** (`disco-like`, `blitz-list-builder`, `google-maps-list-builder`, `competitor-engagers`, `prospeo-*`): requieren keys de esos proveedores (Blitz, DiscoLike, Prospeo, RapidAPI). Nuestro stack disponible hoy: **Apify** (scraping LinkedIn/Maps/Ads) y **Parallel** (research a escala) pueden cubrir lo mismo.
  - **Atados a Smartlead** (`smartlead-api`, `smartlead-inbox-manager`, `smartlead-campaign-upload-public`, `deliverability-test-public`): referencia de patrones; nuestro sender es Instantly. Al portar un flujo, traducir Smartlead API → Instantly API v2.
  - Convención de ellos `profiles/<slug>/` ≙ nuestra `workspaces/<ws>/`.
- **Estado de keys en el entorno (verificado 2026-07-02):** Supabase ✓, Apify ✓, Attio ✓ (CRM, scopes read-write), Parallel ✓. **Instantly: la key autentica pero la API v2 responde 402** — el plan del workspace no incluye acceso API (requiere Hypergrowth). Hasta subir el plan, el fallback es export CSV.

## 8. Roadmap sugerido

1. **Ya (este commit):** arquitectura, skills, workspaces, migración SQL.
2. **Siguiente:** correr la migración en Supabase, poner `INSTANTLY_API_KEY` en el entorno, probar `scripts/instantly_sync.py` con una campaña real.
3. **Después:** backfill del historial de Instantly a `outreach_log` (para que el dedupe conozca el pasado), y migrar los 3 skills unprospect-* a este repo.
4. **Luego:** poblar `companies.pain_signals` (tamaño de equipo comercial vía LinkedIn, Google Ads vía transparencia de anuncios/BuiltWith) y correr `/gtm-pain-segments` sobre la base ya clasificada.
