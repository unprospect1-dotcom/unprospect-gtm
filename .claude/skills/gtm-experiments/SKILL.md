---
name: gtm-experiments
description: Diseña y evalúa A/B tests de cold email donde la variable es la hipótesis de dolor probable en el copy. Define matriz de variantes, tamaño de muestra mínimo y criterio de decisión ANTES de lanzar; después lee resultados y declara ganador o "sin señal".
argument-hint: <workspace> <campaña|"evaluar" campaña>
---

# GTM Experiments — A/B testing de dolor probable

## Antes de empezar
Además del contrato de memoria: lee del workspace `SEGMENTS.md`, `ANGLES.md` y el `BRIEF.md` de la campaña.

## Principio
**Se testea la hipótesis de dolor, no cosméticos.** Subject lines, CTAs y largo se fijan iguales entre variantes. Lo único que cambia entre A y B es QUÉ dolor ataca el copy. Ganar un test = aprender qué le duele al segmento, no qué palabra abre más emails.

## Modo 1: Diseñar (antes de lanzar)

### 1. Matriz del experimento
- **Hipótesis A vs B (máx. C):** dos dolores probables del mismo segmento, tomados de `SEGMENTS.md`.
- **Constantes:** framework, offer, CTA, largo, # de steps, horario de envío, calidad de lista.
- **Métrica de decisión:** positive reply rate (no open rate — con dolor observable, la reply es la señal).
- **Métricas de guardia:** bounce < 3%, unsubscribe/spam bajo control.

### 2. Tamaño de muestra (regla práctica)
Con reply rates positivos típicos de 1–3%, menos de ~300 leads por variante = ruido. Regla: **mínimo 300 por variante, ideal 500**. Si el segmento no da, NO hagas A/B — lanza una sola hipótesis y compara contra el histórico del workspace. Dilo explícitamente en vez de diseñar un test inválido.

### 3. Criterio de decisión pre-registrado
Escribe en el BRIEF antes de lanzar: "ganamos con A si su positive reply rate supera a B por ≥X% relativo con ≥N replies totales; si no, declaramos sin señal". Sin criterio previo, cualquier resultado se puede racionalizar.

## Modo 2: Evaluar (después de correr)
1. Trae métricas por variante desde Instantly (vía `scripts/instantly_sync.py` o la tabla `replies`/`campaigns` de Supabase).
2. Aplica el criterio pre-registrado. Resultados posibles: `A gana` / `B gana` / `sin señal` (di "sin señal" sin pena — es un resultado válido).
3. Escribe `campaigns/<campaña>/RESULTS.md` con números crudos, decisión y qué se aprendió del dolor.
4. Actualiza `ANGLES.md` (ángulo ganador → `ganador`, perdedor → estado que corresponda) y dispara `/gtm-retro`.

## Al terminar
- A `LEARNINGS.md` de este skill: fallas de diseño detectadas (variables contaminadas, muestras cortas) y umbrales que dieron señal limpia.
