---
name: gtm-retro
description: El ciclo de auto-aprendizaje del GTM OS. Destila resultados de campañas, replies y correcciones del usuario en los LEARNINGS.md del workspace Y de cada skill involucrado. Correr al cerrar una campaña, tras un reply-analysis, o cuando el usuario corrige algo importante.
argument-hint: <workspace> [campaña]
---

# GTM Retro — destilar aprendizaje en memoria

## Antes de empezar
Junta la evidencia del ciclo: `RESULTS.md` de la campaña, salida de `/gtm-reply-analysis`, métricas de `campaigns`/`replies` en Supabase, y cualquier corrección que el usuario hizo durante el ciclo.

## Principio
Un aprendizaje sin evidencia es una opinión. Cada entrada de LEARNINGS lleva: **fecha, evidencia (campaña/números/cita), el aprendizaje en una frase accionable, y confianza (hipótesis / señal / confirmado)**. Un aprendizaje se sube a `confirmado` solo cuando se repite en ≥2 campañas.

## Pasos

### 1. Extraer aprendizajes por nivel
- **Del workspace** (`workspaces/<ws>/LEARNINGS.md`): qué segmento/dolor/offer/ángulo funcionó para ESTE cliente. Actualiza también los estados en `SEGMENTS.md`, `OFFERS.md`, `ANGLES.md` para que reflejen la realidad.
- **De cada skill involucrado** (`.claude/skills/gtm-*/LEARNINGS.md`): lo transferible entre clientes — "los benchmarks ganan en verticales que no comparten datos", "muestras <300 nunca dieron señal". Pregúntate por cada skill de la cadena: ¿qué haría distinto la próxima vez?
- **Correcciones del usuario:** si el usuario corrigió un análisis, copy o segmento durante el ciclo, eso es el aprendizaje de mayor prioridad — regístralo textual.

### 2. Contradicciones
Si un aprendizaje nuevo contradice uno viejo, NO borres el viejo: márcalo `[superado <fecha>]` con referencia al nuevo. La historia de qué creíamos y por qué cambió es parte de la memoria.

### 3. Poda (mantener la memoria útil)
Si un `LEARNINGS.md` pasa de ~100 líneas: consolida entradas repetidas, promueve lo confirmado a la sección "Reglas" del archivo (arriba), y archiva lo obsoleto al final bajo "Archivo". La memoria sirve solo si se puede leer al inicio de cada skill sin ruido.

### 4. Reporte
Cierra con un resumen para el usuario: 3–5 aprendizajes del ciclo, qué cambia en la siguiente campaña por causa de ellos, y qué hipótesis nueva vale la pena testear.
