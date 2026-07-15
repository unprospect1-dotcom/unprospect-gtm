# Capa de señales — Contratación de roles comerciales (Apify → calificador → Instantly)

> Diseño del flujo automático semanal. Estado: **borrador para aprobación** (2026-07-15).
> Tesis: si una empresa está **contratando** un rol de prospección/ventas, está invirtiendo
> justo donde Unprospect vende ("el poder operativo de un equipo entero a una fracción del
> costo"). El posting nos da el dolor **con sus propias palabras** y timing fresco.

## 0. Por qué esta señal es distinta (y mejor) que un lookalike
- Un lookalike dice "esta empresa se parece a un cliente". Una vacante dice "esta empresa
  **tiene el dolor AHORA** y está por gastar dinero en resolverlo".
- Encaja nativo con el PLAYBOOK v2, ángulo **bucket 0-1 "antes de tu primera contratación
  comercial"** y bucket 6-15 "estandarización" (según sea primera contratación o escalar equipo).
- La descripción del puesto ES el `{{observacion}}` de este universo: sustituye a la
  observación del crawl con algo aún más fuerte (lo que el prospecto mismo escribió que necesita).

## 1. Arquitectura (7 etapas, corre semanal)

```
[1 HARVEST]  Apify LinkedIn Jobs (últimos 7 días, MX, N roles)  →  postings crudos
     │                                                              $0.001/posting
[2 DEDUPE]   vs job_signals (posting visto) + outreach_log (empresa ya contactada)
     │
[3 QUALIFY]  LLM 2 capas: ¿Unprospect puede ayudar con el dolor/actividades del posting?
     │        fit ∈ {alto, medio, no} + problema_extraido + bucket_hint + confianza
     │        (patrón gtm-classify-b2b: clasificador + verificador ciego; acuerdo = confía)
     │
[4 ENRICH]   DM(s) por dominio (ya viene companyWebsite): dueño de la función comercial
     │        (founder/CEO si chico, VP/Director Comercial si grande) + email verificado
     │
[5 COPY]     Copywriter de 1 línea: del posting → {{observacion_contratacion}} + bridge
     │        al value prop (reglas de estilo del PLAYBOOK: sin em dash, sin halago, afirmar)
     │
[6 PUSH]     Instantly: campaña dedicada, custom fields (rol, observacion, one-liner, bucket, fit)
     │
[7 LOG]      Upsert a Supabase (job_signals + outreach_log) para memoria y dedupe futuro
```

## 2. Fuente de datos — VALIDADA (2026-07-15)
- **Actor: `curious_coder/linkedin-jobs-scraper`** — pay-per-result **$0.001/vacante**
  (391K corridas exitosas, ⭐4.4). Input: array de URLs de búsqueda LinkedIn Jobs +
  `scrapeCompany:true` + `count`.
- **Frescura semanal nativa:** parámetro `f_TPR=r604800` en la URL (posted last 7 days).
- **Campos que devuelve (probado, 10 vacantes MX de ventas):** `title`, `descriptionText`
  (completa), `companyName`, `companyWebsite` (dominio directo), `companyDescription`,
  `companyEmployeesCount`, `companyLinkedinUrl`, `location`, `postedAt`, `seniorityLevel`,
  `jobFunction`, `industries`, `applicantsCount`, `salary`.
- **El dominio viene en el posting** → muchas empresas NO necesitan un paso extra de
  resolución de dominio (ahorro grande).
- Fallback / fuentes MX adicionales evaluadas: OCC Mundial (`unfenced-group/occ-com-mx-scraper`)
  y Computrabajo (`santamaria-automations/computrabajo-scraper`, 19 países LATAM) — para
  PyMEs que no publican en LinkedIn. Fase 2 si LinkedIn deja huecos.

## 3. Set de keywords del HARVEST (CONFIRMADO por el usuario 2026-07-15)
Una URL de búsqueda LinkedIn Jobs por keyword (ES+EN), location=Mexico, `f_TPR=r604800`.
Decisión: **barrer amplio** (Tier 1 + Tier 2 completo + growth/demand gen); el costo es
trivial ($0.001/resultado) y el **calificador poda** el ruido. Dedupe por `job_id` colapsa
los duplicados entre búsquedas.

**Tier 1 — señal directa de prospección/nuevo negocio:**
`SDR`, `BDR`, `sales development representative`, `business development representative`,
`business development manager`, `desarrollo de negocios`, `desarrollo de nuevos negocios`,
`desarrollo comercial`, `desarrollo de mercado`, `hunter`, `ventas hunter`, `prospección`,
`prospectador`, `generación de leads`, `generación de demanda`, `demand generation`,
`lead generation`, `outbound`, `apertura de cuentas`, `apertura de mercado`,
`alianzas comerciales`, `alianzas estratégicas`, `inside sales`, `ventas internas`

**Tier 2 — comercial general (recall alto, el calificador poda):**
`ventas B2B`, `comercial`, `ejecutivo comercial`, `ejecutivo de ventas`,
`representante de ventas`, `asesor comercial`, `asesor de ventas`, `gerente comercial`,
`gerente de ventas`, `director comercial`, `director de ventas`, `ejecutivo de cuentas`,
`account executive`, `key account manager`, `consultor comercial`, `coordinador comercial`,
`expansión comercial`, `partnerships`, `strategic partnerships`

**Adyacentes aprobados — marketing de crecimiento / demand gen (fit MEDIO salvo outbound explícito):**
`growth`, `growth marketing`, `mercadotecnia de crecimiento`, `demand generation`

> `comercial` a secas es la de mayor recall y mayor ruido (jala analista/coordinador/retail);
> se queda porque el calificador ya sabe tirar enterprise y reclutadoras.
> El calificador (etapa 3) decide fit real leyendo la descripción — las keywords son la
> **red amplia**; la precisión la pone el LLM, no el keyword.

**NOTA de la muestra 2026-07-15:** el dashboard inicial se corrió solo con 5 keywords
(sales development representative, ejecutivo de ventas, gerente comercial, desarrollo de
negocios, inside sales) — NO era el set completo. La próxima corrida usa el set de arriba.

## 4. El CALIFICADOR (corazón del flujo)
**Pregunta que responde:** ¿el problema/las actividades del puesto son los que Unprospect
resuelve? Unprospect = sistema de prospección outbound (research de cuentas, listas, mensajes,
secuencias, follow-up, apertura de cuentas nuevas).

| Veredicto | Señales en la descripción |
|---|---|
| **fit ALTO** | prospección, cold outreach, generación de pipeline, abrir cuentas nuevas, outbound, armar listas, desarrollo de mercado, nuevo logo, cuotas de reuniones agendadas |
| **fit MEDIO** | ventas mixtas (algo de prospección + cuenta), growth, demand gen con componente outbound |
| **NO fit** | puro account management / cuentas existentes, inbound-only, ventas de piso/retail, preventa técnica (SE), customer success, canal/partner sin prospección, "ventas" de mostrador |

**Salidas por posting:**
- `fit` (alto/medio/no) + `fit_confianza`
- `problema_extraido`: la actividad/dolor textual que Unprospect ataca (insumo del one-liner)
- `bucket_hint`: ¿primera contratación comercial (founder-led, 0-1) o escalar equipo (6-15+)?
  Se cruza con `companyEmployeesCount` y con `sales_count` si la empresa ya está en Supabase.
- **2 capas (patrón gtm-classify-b2b):** clasificador barato en masa + verificador ciego
  independiente. Coinciden → se confía. Difieren → cola de revisión. NUNCA inventar fit.

## 5. ENRIQUECIMIENTO del DM
El target del email NO es quien publicó la vacante: es **quien es dueño de la función comercial**.
Routing por tamaño (`companyEmployeesCount`):
- **≤ ~20 empleados** → founder / CEO / director general (venta founder-led).
- **> ~20** → VP Sales / Director Comercial / Head of Sales / CRO.
- Herramienta: GetLeads `decision-makers` por dominio + diccionario ES (o AI Ark/Prospeo) →
  email verificado. Ya tenemos el dominio del posting, así que es directo.

## 6. El COPYWRITER de 1 línea
- Input: `{title, descriptionText, companyName, problema_extraido, bucket_hint}`.
- Output: UNA línea en español que (a) nombra la señal de contratación de forma natural y
  (b) puentea al value prop sin vender todavía. Se guarda como custom field `observacion`
  (reusa el slot del PLAYBOOK) para el Email 1.
- **Reglas de estilo del PLAYBOOK (duras):** sin em dashes, sin comillas, sin halago, afirmar
  lo observable (la vacante es pública, no hay que hedge-arla), humildad solo si inferimos algo.
- Ejemplo (bucket 0-1, primera contratación): *"Vi que están sumando un BDR para abrir mercado
  cross-border. Antes de esa primera contratación suele ayudar validar qué cuentas y mensajes
  generan conversaciones reales."* → engancha con el ángulo pre-contratación ya aprobado.

## 7. Esquema Supabase nuevo — `job_signals`
```
job_signals (
  id, workspace, job_id (LinkedIn id, único), posted_at, harvested_at,
  role_title, job_function, seniority, description_text,
  company_name, company_domain, company_linkedin, company_employees, industries, location,
  fit, fit_confianza, problema_extraido, bucket_hint,      -- del calificador
  dm_email, dm_name, dm_title,                              -- del enrich
  observacion_oneliner,                                     -- del copywriter
  instantly_campaign_id, pushed_at, status                 -- estado del pipeline
)
unique(workspace, job_id)  -- dedupe de postings
```
El dedupe de EMPRESA (no recontactar) sigue siendo `outreach_log` (fuente de verdad).

## 8. Scheduling semanal
- Routine/cron semanal (ej. lunes 8am). Cada corrida:
  1. Apify con `f_TPR=r604800` (solo última semana) sobre todas las URLs de roles.
  2. Etapas 2-7 en pipeline. Dedupe garantiza cero recontacto.
- Idempotente y con resume (mismo patrón que los pulls de Ocean).

## 9. Modelo de costo (semanal)
| Etapa | Costo | Nota |
|---|---|---|
| Apify harvest | ~$1 por 1,000 postings | 5K postings/sem ≈ $5 |
| Calificador LLM | va en Codex (subagentes, modelo barato) | fuera de este presupuesto |
| Enrich DM (GetLeads) | 1 crédito por DM devuelto | solo sobre fit alto/medio |
| Copywriter LLM | va en Codex | |
| Instantly | incluido en el plan | |
**El gasto duro es Apify (~$5/sem) + créditos GetLeads solo sobre los calificados.**

## 10. Decisiones abiertas (para el usuario)
1. Set de roles final (§3) — ¿lo dejo como propuesto o agregas/quitas?
2. Estrictez del calificador — ¿solo fit ALTO a campaña, o también MEDIO?
3. Target del DM — ¿confirmas el routing por tamaño (§5)?
4. Instantly — ¿una campaña única "señales-contratacion" o segmentada por bucket/industria?
5. Geografía — ¿solo México, o también LATAM/US-nearshore que contrata en español?
6. ¿El calificador + copywriter corren en Codex (subagentes) y este flujo solo orquesta harvest+enrich+push?
```
```
