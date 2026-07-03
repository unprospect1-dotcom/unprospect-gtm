# Auditoría de coldoutboundskills + roadmap de NUESTROS skills

> Los 28 skills de referencia (en `reference/coldoutboundskills/`) son inspiración, no producto.
> Este doc dice qué patrones robar, cuáles ignorar, y en qué orden construimos los nuestros.

## El patrón universal (el ADN de todos nuestros skills)

Lo que hace buenos a los mejores skills de referencia — y a los prompts de research de unprospect — es el mismo ciclo. **Todo skill nuestro lo implementa:**

1. **Inferir primero, preguntar después.** El skill investiga lo que puede (memoria, website, Supabase) y presenta su inferencia; solo pregunta lo que no puede inferir. (patrón de `icp-onboarding`: scrape → resumen → "¿correcciones?" → entrevista corta)
2. **Confirmación por pasos.** Decisiones grandes se aprueban una por una, estilo Typeform, con 2–3 opciones y una recomendación — nunca un mega-output de golpe. (patrón de `campaign-copywriting`)
3. **Loop de aprobación antes de escalar.** 1 muestra → corriges → lote de 10 → corriges → cuando hay 2 rondas seguidas sin ediciones, se escala al total con sub-agents paralelos. (patrón de `personalization-subagent-pattern` / `icp-prompt-builder`)
4. **El artefacto aprobado es el contrato.** Cada skill termina escribiendo UN artefacto con estado `aprobado` en `workspaces/<ws>/` — y es lo ÚNICO que el siguiente skill consume. Sin artefacto aprobado, la cadena no avanza.
5. **Las ediciones del usuario son el aprendizaje.** Cada corrección se registra textual en el `LEARNINGS.md` del skill ("nunca usar X", "los CTAs de pregunta > los de calendario"). La siguiente corrida arranca con esas reglas.

## Veredicto de la auditoría — qué robar de cada uno

### Tier 1 — el ADN (robar el patrón completo)
| Referencia | Qué robar |
|---|---|
| `campaign-copywriting` | El flujo de 4 pasos con confirmación: dirección → subject+primera línea → estructura del body → copy final. 2–3 opciones por paso con recomendación. |
| `icp-onboarding` | Scrape primero → resumen ancla → correcciones → entrevista; hard filters vs soft preferences (el error #1: tratar todo como obligatorio y quedarte con 200 leads en vez de 5,000). |
| `personalization-subagent-pattern` | El approval loop completo + fan-out con Task sub-agents (sin API externa). |
| `icp-prompt-builder` | Afinar un prompt de calificación por lotes de 10 con feedback hasta 2 rondas limpias; guardar el prompt como activo reutilizable. |

### Tier 2 — velocidad de campaña (robar conceptos)
| Referencia | Qué robar |
|---|---|
| `campaign-strategy` | Las dos palancas (lista y mensaje); niveles broad → focused → niche; entre más nicho la lista, más directo el mensaje; 4 categorías de value prop (ganar dinero / ahorrar tiempo / ahorrar dinero / mitigar riesgo). |
| `prospeo-search-api` | Directamente útil (usamos Prospeo): formato de filtros, rate limit 2–2.5 req/s, 25 resultados/página, límite 25K y el crawl estado-por-estado para romperlo. |
| `list-quality-scorecard` | Gate pre-envío con letter grade: duplicados, diversidad de títulos, catch-all density, fit vs ICP, verificación. Una mala lista quema inboxes aunque el copy sea perfecto. |
| `spam-word-checker` | Guardia always-on sobre TODO copy generado, no un chequeo opcional. |

### Tier 3 — learning loop (robar el esquema)
| Referencia | Qué robar |
|---|---|
| `positive-reply-scoring` | El norte: positive reply rate = positivos / enviados (no reply rate). Su esquema de 11 clases es más fino que el nuestro — adoptarlo. Referrals cuentan como positivo. |
| `experiment-design` | Una variable por experimento (lista O copy, nunca ambas); confidence weighting; el experimento combinado solo genera hipótesis, no conclusiones. |

### Ignorar (por ahora)
`smartlead-*` (nuestro sender es Instantly; solo sirven como mapa de qué endpoints necesitaremos), `zapmail-domain-setup`, `deliverability-*` (hasta tener problema real), `google-maps-list-builder` (SMB local, no es el ICP), `blitz`/`competitor-engagers`/`disco-like` (requieren keys que no tenemos; DiscoLike se agrega si se contrata).

## Roadmap: nuestros skills, uno por uno (orden de construcción)

Cadena completa: buyer map → lista → ángulos → copy → personalización → launch → pulse.
Cada uno se construye, se usa en una campaña real, se afina, y hasta entonces se construye el siguiente.

1. **`gtm-buyer-map`** — Encontrar a los tomadores de decisión. Input: segmento + workspace. Entrevista corta → matriz de personas (2–4 por segmento) con: títulos exactos para Prospeo/AI ARK (con variantes y seniority), quién decide vs quién influye, y fallback por tamaño de empresa ("en <50 empleados el título no existe, buscar al dueño"). Artefacto: `BUYER-MAP.md` aprobado.
2. **List building — CONSTRUIDO como dos skills por proveedor:** `gtm-lists-aiark` (búsqueda empresas/personas, lookalikes nativos vía `lookalikeDomains`, export con email verificado por BounceBan, listas de exclusión) y `gtm-prospeo` (modo buscar: 25K/búsqueda con crawl por estado; modo enriquecer: 1 crédito/email verificado, estimación de costo antes de gastar). También `gtm-ocean` (Ocean.io: lookalikes semánticos con 3–10 seeds, warmup gratis de seeds, reveal async de emails, y presupuesto de créditos duro — 1 crédito por resultado + 1 por email). Configuración en `config/providers.yaml`, ejecutores en `scripts/aiark.py`, `scripts/prospeo.py` y `scripts/ocean.py`, salida normalizada al `csv_schema` común. Pendiente de conectar: scorecard con letter grade (patrón `list-quality-scorecard`) como paso 6.5 y el prompt de calificación (patrón `icp-prompt-builder`).
3. **`gtm-angles`** (evolución de gtm-campaign-ideation) — **5 ángulos × persona**: la matriz completa. El mismo dolor de negocio se ve distinto por rol (dueño=crecimiento/riesgo, ops=tiempo/caos, finanzas=costo). Cada celda: dolor observable + apertura + offer + credibilidad. Artefacto: `ANGLES.md` aprobado + tabla `angles`.
4. **`gtm-copy` v2** — Copy con TUS frameworks. Se agrega `workspaces/<ws>/copy-library/`: frameworks que el usuario apruebe, CTAs favoritos, emails ejemplo que le gustaron, positive replies reales. Flujo stepwise de 4 confirmaciones (patrón campaign-copywriting) + spam-check integrado + **cada edición del usuario se registra como regla**. Artefacto: `COPY.md` aprobado por variante.
5. **`gtm-personalize`** — Personalización a escala con aprobación. Input: la lista + una fuente scrapeable por lead (ej. si ofrecemos lookalikes, scrapear el sitio del lead para citar a quién se parece). Loop: 1 muestra → 10 → 10 → 2 rondas limpias → fan-out con sub-agents. Artefacto: CSV con variables por lead.
6. **`gtm-launch`** — Ensamblar y lanzar en Instantly. Verifica que TODOS los artefactos previos estén `aprobado` + gate de spam/calidad → crea la campaña en Instantly (API cuando el plan la incluya; mientras: genera el paquete CSV+copy listo para pegar y checklist manual) → registra campaña/ángulo/envíos en Supabase. Nunca lanza sin registrar.
7. **`gtm-pulse`** — Qué está prendiendo. Positive reply rate por ángulo × persona (esquema de 11 clases), leído de Instantly (API o CSV export). Recomendación única: escalar / matar / iterar, con confidence weighting del experimento. Alimenta `gtm-retro`.

## Qué necesitamos del usuario para arrancar

- **Copy library seed:** 2–3 frameworks de copy que le gusten (con ejemplos), sus CTAs favoritos, 3–5 cold emails reales que él aprobaría, y positive replies pasadas si existen.
- **Keys que NO están en el entorno:** `PROSPEO_API_KEY`; cómo se accede a AI ARK (¿tiene API o es UI?); DiscoLike si se contrata.
- **Personas iniciales** del primer segmento para estrenar `gtm-buyer-map`.
- **Decisión Instantly:** upgrade a plan con API, o flujo CSV mientras tanto.
