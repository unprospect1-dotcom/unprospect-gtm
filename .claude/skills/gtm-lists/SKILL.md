---
name: gtm-lists
description: El punto de entrada de list building. A partir del segmento, buyer map o lo que el usuario describa, decide qué proveedor usar (AI Ark, Prospeo u Ocean), garantiza el dedupe con gtm-check-contact y aplica el control de calidad antes de aprobar la lista. Úsalo cuando quieras "una lista" sin haber decidido aún la fuente.
argument-hint: <workspace> <segmento | descripción de la lista | dominios seed>
---

# GTM Lists — router de list building

Una lista pasa SIEMPRE por 5 pasos, sin importar el proveedor:
**fuente → dedupe → calificación AI → control de calidad → artefacto aprobado en `lists/<ws>/`**.
Este skill decide la fuente y garantiza los demás.

## 1. Elegir la fuente

| Qué tienes | Usa | Por qué |
|---|---|---|
| 3–10 dominios de clientes reales | `/gtm-lists-aiark` (`lookalikeDomains`) o `/gtm-ocean` | AI Ark primero: no cobra por resultado de búsqueda. Ocean cuando quieres similitud semántica de producto/servicio y aceptas el costo (1 crédito por resultado + 1 por email). |
| Filtros firmográficos claros (títulos, industria, tamaño, geo) | `/gtm-lists-aiark` o `/gtm-prospeo` | AI Ark exporta con verificación BounceBan incluida. Prospeo cuando el segmento pide sus filtros (funding, tech) o >10K con crawl por estado. |
| Un CSV existente sin emails / incompleto | `/gtm-prospeo` (modo enriquecer) | 1 crédito por email verificado, NO_MATCH gratis, re-enriquecer gratis 90 días. |
| Todavía no hay segmento definido | Regresa a research: `/gtm-pain-segments` | Una lista sin hipótesis de dolor no tiene ángulo de copy. |

**Waterfall:** los leads sin match de un proveedor pasan al siguiente (ej. enriquecer con Prospeo lo que AI Ark devolvió sin email verificado) — nunca se descartan sin intentar la segunda fuente.

**Departamentos y seniority (a quién dentro de la empresa):**
- **AI Ark filtra nativo** por `contact.departmentAndFunction` (ventas, marketing, ops...) × `contact.seniority` (founder, c_suite, vp, director, manager) — úsalo como primer corte cuando el buyer map pide un departamento; es el proveedor con mejor accuracy para esto.
- **Prospeo NO tiene filtro de departamento** — solo `person_job_title` include/exclude. Aproxima el departamento con listas de títulos y deja el veredicto fino al paso 3.
- El título nunca es confiable solo (dispersión: "Gerente de Tráfico" = ops en logística MX): el corte de filtros acerca, el prompt `title-buyer` decide.

## 2. Dedupe (no negociable)

Antes de cualquier export grande, corre `/gtm-check-contact` sobre la muestra/dominios:
los ya contactados van a la lista de exclusión del proveedor. No pagues por leads que vas a tirar.

## 3. Calificación AI (cuando el corte de filtros no basta)

Los filtros del proveedor cortan por atributos; no saben si la empresa encaja en el ICP ni si el contacto es EL decisor. Para eso, prompts afinados con `/gtm-prompt-tuner`:
- **`icp-fit`** — score de encaje por empresa (`qualified`, `confidence`, `reason`). Quedarse con `qualified: true` y `confidence ≥ 0.6`.
- **`title-buyer`** — con títulos dispersos: normaliza el rol y clasifica `decisor | influencer | descartar` según el buyer map (en <50 empleados el decisor suele ser el dueño aunque el título diga otra cosa).

Primera vez por segmento: correr el tuner (10 filas, dos rondas limpias). Corridas siguientes: reutilizar el prompt de `workspaces/<ws>/prompts/` con fan-out de sub-agents de modelo barato (config `execution` de `providers.yaml`).

## 4. Control de calidad (gate antes de aprobar)

Sobre la muestra y el CSV final:
- **Duplicados internos** (por email Y por dominio) = 0.
- **Diversidad de títulos:** ¿la distribución coincide con el buyer map, o se coló un título dominante que no es el decisor?
- **% catch-all:** si supera ~20%, separarlos a un CSV aparte marcado — no se mezclan con verificados.
- **Fit vs ICP:** revisa 10 filas al azar contra `SEGMENTS.md`/`PROFILE.md`. Si ≥2 no encajan, el filtro está mal — corrígelo y re-muestrea.

Una lista mala quema inboxes aunque el copy sea perfecto: si falla el gate, se ajusta el filtro; nunca se lanza "así".

## 5. Artefacto

Igual para los 3 proveedores (lo escriben ellos, este skill lo verifica):
CSV normalizado al `csv_schema` de `config/providers.yaml` en `lists/<ws>/<YYYY-MM-DD>-<slug>.csv`
+ `-REPORT.md` con filtros reproducibles, totales, % verificados, excluidos por dedupe, créditos gastados y estado **aprobado**.
Sin `-REPORT.md` aprobado, la lista no avanza a copywriting/launch.
