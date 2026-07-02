---
name: gtm-check-contact
description: Verifica contra Supabase si un lead/empresa ya está en la base y cuándo fue la última vez que lo contactamos, con qué ángulo y qué resultó. Úsalo SIEMPRE antes de agregar leads a una campaña — es el guardián del dedupe.
argument-hint: <workspace> <email|domain|nombre|archivo.csv>
---

# GTM Check Contact — historial y dedupe

## Antes de empezar (contrato de memoria)
1. Lee `LEARNINGS.md` en este directorio.
2. Requiere `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` en el entorno.

## Pasos

### 1. Normalizar la entrada
Acepta un lead suelto (email/dominio/nombre) o un CSV de leads. Normaliza: dominio en minúsculas sin `www.`, email en minúsculas.

### 2. Consultar la memoria
Contra la API REST de Supabase (mismo patrón que `segment_companies.py`):
- `companies`: ¿el dominio ya existe en la base? ¿con qué clasificación y `pain_segment`?
- `v_last_contact` / `outreach_log`: filtrando por `workspace` — último toque, campaña, ángulo, step y resultado.
- `replies`: ¿alguna vez respondió? ¿cómo se clasificó esa respuesta?

### 3. Veredicto por lead
| Veredicto | Regla |
|---|---|
| `NUEVO` | No existe en `companies` ni en `outreach_log`. |
| `EN_BASE_SIN_CONTACTAR` | Está en `companies` pero sin registros en `outreach_log`. |
| `CONTACTADO_FRIO` | Último toque > 90 días, sin reply negativo → recontactable **con ángulo distinto** (dilo explícitamente: qué ángulo se usó antes para no repetirlo). |
| `CONTACTADO_RECIENTE` | Último toque ≤ 90 días → excluir de la campaña. |
| `RESPONDIO_POSITIVO` | Tiene reply positivo → NO es cold outbound, va al pipeline. |
| `NO_CONTACTAR` | Reply negativo/unsubscribe en el historial → excluir siempre. |

### 4. Reporte
Para CSVs: tabla resumen por veredicto + archivo filtrado listo para campaña (solo `NUEVO`, `EN_BASE_SIN_CONTACTAR` y `CONTACTADO_FRIO`). Para leads sueltos: la historia completa en 5 líneas — cuándo, qué campaña, qué ángulo, qué pasó.

## Al terminar (contrato de memoria)
- Si detectaste huecos en la memoria (envíos que existieron en Instantly pero no están en `outreach_log`), repórtalo: significa que falta correr `scripts/instantly_sync.py`.
- Registra en `LEARNINGS.md` patrones útiles (ej. dominios con múltiples marcas, matching que falló).
