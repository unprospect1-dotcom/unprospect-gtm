---
name: gtm-reply-analysis
description: Analiza los replies de Instantly (especialmente positive replies) — los clasifica, los liga al ángulo y dolor que los generó, detecta patrones de lenguaje del mercado y persiste todo en Supabase y en la memoria del workspace. La mina de oro del aprendizaje.
argument-hint: <workspace> [campaña | "todas"]
---

# GTM Reply Analysis — aprender de las respuestas

## Antes de empezar (contrato de memoria)
1. Lee `LEARNINGS.md` en este directorio.
2. Lee del workspace: `ANGLES.md` (para ligar reply → ángulo) y `LEARNINGS.md`.
3. Fuente de replies: API de Instantly (`INSTANTLY_API_KEY`) vía `scripts/instantly_sync.py`, o la tabla `replies` de Supabase si ya se sincronizó. Fallback: CSV exportado que te pase el usuario.

## Pasos

### 1. Clasificar cada reply
| Clase | Definición | Acción |
|---|---|---|
| `positive_interesado` | Quiere el offer o saber más | → pipeline, responder < 24h |
| `positive_timing` | Interés real pero "ahora no" | → follow-up programado, registrar fecha |
| `referral` | Te redirige a la persona correcta | → nuevo lead CON contexto (¡el mejor tipo de lead!) |
| `objection` | Objeción concreta (precio, ya tienen, no creen) | → insumo de copy, no descartar |
| `negative` | No molestar | → `outreach_log` como no-contactar |
| `ooo/auto` | Automático | → ignorar para métricas, reintentar después |

Persiste la clasificación en la tabla `replies` (con `campaign_id`, `angle`, `workspace`).

### 2. Minar los positives (lo más valioso)
De cada positive extrae:
- **Palabras exactas** con las que describen su dolor → alimenta `/gtm-copy` (el mercado te escribe el copy).
- **Qué línea del email citaron o a qué reaccionaron** → valida (o no) la hipótesis de dolor del ángulo.
- **Rol y tipo de empresa del que respondió** → ¿coincide con el segmento diseñado o respondió otro perfil? (señal de re-segmentación).

### 3. Minar las objeciones
Agrupa objeciones recurrentes. Cada objeción repetida ≥3 veces = o un fix de copy (adelantarse a ella) o una verdad incómoda del offer (reportarla, no maquillarla).

### 4. Reporte y persistencia
- Resumen: replies por clase y por ángulo, positive rate por hipótesis de dolor, top 5 frases textuales del mercado, objeciones recurrentes, recomendación concreta (seguir / ajustar copy / cambiar ángulo / re-segmentar).
- Actualiza `workspaces/<ws>/LEARNINGS.md` (sección de voz del mercado y ángulos) y el `RESULTS.md` de la campaña.

## Al terminar (contrato de memoria)
- Registra en `LEARNINGS.md` de este skill mejoras al método de clasificación y patrones transferibles entre clientes.
