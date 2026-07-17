# Plan: skills de list building para GetLeads / AI Ark / Ocean

> Investigación hecha el 2026-07-11. Costo de toda la investigación: **0.5 créditos de AI Ark, 0 de Ocean, 0 de GetLeads** (todo lo demás fue con endpoints gratuitos).
>
> **Estado 2026-07-13: Fases A, B y C completadas** — skill `gtm-getleads` creada (con la receta DM-unión validada en vivo sobre transporte MX), `providers.yaml` y scripts corregidos, learnings registrados en las 3 skills. Gasto acumulado de validación: 2.0 créditos AI Ark, 0 GetLeads, 0 Ocean. Falta Fase D (estreno con lista real del usuario).

## 1. Lo que verifiqué en vivo (las 3 keys funcionan)

| Plataforma | Saldo real | Auth | Costo real por operación | Lo gratis |
|---|---|---|---|---|
| **GetLeads** (`GETLEADS_API`) | **5,000** | `Authorization: Bearer glb_live_…` | 1 crédito por registro devuelto / enrichment exitoso; 0 si no hay match | **`search/count` (conteos), `filter-values`, `health` — 0 créditos** |
| **AI Ark** (`AI_ARK_API`) | **15,099.5** | header `X-TOKEN` | **La búsqueda SÍ gasta: 0.5 créditos por perfil devuelto** (verificado: 15,100 → 15,099.5 con un search de size=1). Export con email: 1 crédito (0.5 perfil + 0.5 email BounceBan), 0 si no hay email válido | `/v1/payments/credits` (saldo) |
| **Ocean** (`OCEAN_API`) | **~4,669** (4,368.8 one-time + 300 recurrentes) | header `x-api-token` | Company search medido en **0.2 créditos/resultado**; email revelado 1 crédito | `warmup` de seeds, `balance` |

Correcciones descubiertas vs lo que había en el repo:

- `config/providers.yaml` apunta a env vars que no existen (`AIARK_KEY`, `OCEAN_KEY`); las reales son `AI_ARK_API`, `OCEAN_API`, `GETLEADS_API`.
- `scripts/aiark.py` usa el path de créditos equivocado (`/credit`); el real es `/v1/payments/credits`.
- La skill de AI Ark asume que buscar es ~gratis; **cada perfil devuelto en search cuesta 0.5** — hay que sondear con `size:1` y nunca paginar de más.
- GetLeads no tiene docs públicas navegables — su documentación completa estaba embebida en el JS de su SPA; la extraje a `reference/getleads-api.md`.

## 2. Estrategia de créditos (quién hace qué)

**Regla de oro: todo lo que se pueda contar, se cuenta gratis en GetLeads antes de gastar en cualquier lado.**

| Uso | Plataforma | Por qué |
|---|---|---|
| Conteos / sizing (deptos, mercado, TAM por filtro) | **GetLeads `search/count`** | **$0**, 100 req/min → ~100 empresas/min gratis |
| Listas grandes con email verificado | **AI Ark export** (pot de 15k) | 1 crédito/lead con email BounceBan; refund si no hay email; hasta 10k por job |
| Lookalikes semánticos desde clientes reales | **Ocean** (exclusivo para esto) | Es su capacidad única; carísimo para todo lo demás |
| Decision-makers rápidos de un dominio | GetLeads `lookup/decision-makers` | 1 crédito/registro, filtro C-Team/VP/Director/Head ya hecho |
| Enrichment de un CSV existente (email/LinkedIn→persona) | GetLeads `enrich/*` | 1 crédito solo por acierto; batch de 100 |
| Señales (funding, adquisiciones) | GetLeads `signals` | 1 crédito/registro, nadie más lo tiene |
| Señal "corre Google Ads" para pain-segments | GetLeads `where_sql` (`MONTHLY_GOOGLE_ADSPEND_ORG > 0`) | conteo = gratis; encaja directo con gtm-pain-segments |

Presupuestos duros propuestos (van a `providers.yaml`, ajustables):

- GetLeads: `max_per_run: 1000`, `reserve: 1000` — los conteos no cuentan porque son gratis.
- AI Ark: `max_per_run: 3000`, `reserve: 2000`.
- Ocean: ya existe (`max_per_run: 800`, `reserve: 500`) — se queda.

## 3. Tu caso inmediato: tamaño del departamento de ventas de un set de empresas

**Se resuelve GRATIS** con GetLeads: por cada dominio, `POST /contacts/search/count` con `{domains: [X], job_functions: ["Sales & Business Development"]}` → `total_matching`. Verificado en vivo: hubspot.com → 1,636 contactos de ventas, `credits_used: 0`.

- Throughput: 100 req/min → 500 empresas ≈ 5 minutos, $0.
- Cross-check opcional: AI Ark `POST /v1/people` con `contact.departmentAndFunction: master_sales` + `size:1` → `totalElements` (hubspot.com → 3,179; taxonomía más amplia). Costo: 0.5 créditos por empresa — solo sobre una muestra (~10%) para calibrar la diferencia entre ambas bases.
- Entregable: CSV `dominio, sales_count_getleads, [sales_count_aiark], ratio_vs_headcount` + banderas (0 = sin presencia en la base, no necesariamente sin equipo).

Esto entra como **modo "contar"** de la nueva skill de GetLeads — no como skill aparte.

## 4. Trabajo propuesto (en orden)

### Fase A — Cimientos (sin gastar créditos)
1. `reference/getleads-api.md` — doc extraída ✅ (ya está en este commit).
2. `providers.yaml`: corregir `env_key` de las 3 plataformas + agregar sección `getleads` (base_url, rate 100 rpm, budgets, costos).
3. `scripts/aiark.py`: corregir path de créditos; anotar el costo real del search.
4. `scripts/getleads.py`: ejecutor nuevo (subcomandos: `health`, `count`, `search`, `export`, `export-status`, `decision-makers`, `colleagues`, `enrich-email`, `enrich-linkedin`, `enrich-person`, `filter-values`, `signals`). Mismo estilo que los otros ejecutores (urllib, retries, rate limit).

### Fase B — Skill nueva `gtm-getleads`
`SKILL.md` + `LEARNINGS.md`, con el contrato universal (inferir → confirmar → muestra → escalar) y **modos** explícitos:
- **contar** (gratis): sizing por filtro — incluye el caso "tamaño de depto X para N dominios" (input: CSV o lista de dominios + departamento).
- **lista**: search/count gratis primero → muestra de 25 (25 créditos) → aprobación → export CSV asíncrono.
- **decision-makers**: input dominio(s) + límite.
- **enriquecer**: input CSV con emails o LinkedIn URLs; estimación de costo = filas (solo cobra aciertos).
- **señales**: funding/adquisiciones con filtros.
Inputs obligatorios por modo definidos en el argument-hint; presupuesto y saldo reportados antes de cualquier gasto.

### Fase C — Actualizar skills existentes con lo verificado
- `gtm-lists-aiark`: path de créditos, costo real de search (0.5/perfil → sondear con size 1, jamás traer páginas que no se van a usar), enum `master_sales` y el patrón de conteo por departamento, registrar en LEARNINGS.md.
- `gtm-ocean`: registrar en LEARNINGS.md el saldo verificado y que balance/warmup confirmados en vivo.
- Los tres skills se referencian entre sí: "para contar, usa GetLeads gratis".

### Fase D — Estreno con tu caso real (cuando pases la lista)
Correr el modo "contar" sobre tu set de empresas: gratis en GetLeads + cross-check AI Ark en muestra del 10% (≈0.5 × N/10 créditos). Ejemplo: 200 empresas = $0 GetLeads + ~10 créditos AI Ark.

## 5. Pipeline canónico de categorías (definido por el usuario, 2026-07-13)

El flujo NO verifica antes de enumerar — el web scraping propio ES la verificación y la segmentación:

1. **Enumerar empresas** en AI Ark por unión de lentes (industria ∪ NAICS). 0.1 créditos/empresa. Corte de tamaño (decisión del usuario 2026-07-13): **por personas EN LINKEDIN, no autoreportado — mínimo 3 (2 en transporte), máximo 700** — y resulta que `employeeSize` filtra nativo sobre ese conteo (`staff.total`), así que va en la query misma. Ojo: el filtro tira ~25% de empresas sin dato de staff — se dejan para una pasada de recuperación posterior si el segmento rinde. La respuesta trae dominio, staff.range (autoreportado), staff.total, NAICS y descripción — el autoreportado se conserva en el CSV como columna de contexto (regla: en transporte/manufactura es el más creíble del TAMAÑO REAL, aunque el corte de alcanzabilidad sea por LinkedIn).
2. **Dedupe** contra Supabase por dominio (gratis).
3. **Enriquecer con el crawler propio** (`gtm-web-crawler`, $0) → clean_text por sitio.
4. **Segmentar por subcategoría desde el sitio** (con subagentes estilo `gtm-classify-b2b`): en autotransporte → flota de carga general / refrigerado / freight forwarder / 3PL / software para transporte / paquetería. La etiqueta de LinkedIn NO decide la subcategoría; el sitio sí.
5. **Bucket por tamaño de equipo comercial EN EL MISMO PASO** (GetLeads count por dominio con job_functions Sales, gratis, ~50 empresas/min): 0 (sin señal) / 1–2 / 3–10 / 11–50 / 50+. Nota: el conteo de depto es LinkedIn-based — en transporte el personal comercial/administrativo SÍ suele tener LinkedIn aunque los operadores no; aún así 0 se marca "sin señal", nunca "sin equipo".
6. Salida: companies CSV con `dominio, subcategoría, sales_count, sales_bucket, staff_range_autoreportado` → alimenta `gtm-pain-segments` y de ahí la receta DM-unión por segmento.

Universos medidos (sondeos 2026-07-13, sin enterprise donde se indica):
- **Autotransporte MX**: industria 7,649 ∪ NAICS 484 3,880 (∩ 1,423) ≈ **10,100 total / ~7,500 sin enterprise**. Núcleo de precisión (∩): 1,423. Mundo real (SICT 2024): ~38,400 pequeñas+medianas formales (LinkedIn ve ~25%).
- **Comercio al por mayor MX**: industria "wholesale" 14,053 ∪ NAICS 423/424/425 39,052 (∩ 2,596) ≈ **50,500 total** — enumerarlo completo costaría ~5,000 créditos: se hace por etapas (núcleo ∩ → etiqueta industria sin enterprise → expansión NAICS por sub-vertical).

## 6. Qué NO se hace sin aprobación explícita

- Ningún export, search con size>1, reveal ni enrichment masivo — cualquier llamada que gaste >5 créditos se reporta antes con costo estimado y saldo.
- Ocean queda intacto (4,669) hasta que haya un caso lookalike real.
