---
name: gtm-copy
description: Escribe cold email copy usando frameworks distintos (PAS, BAB, PPP, QVC, 1-2-3, observación directa) a partir de un BRIEF de campaña. Genera las variantes A/B donde la variable es la hipótesis de dolor, no cosméticos. Complementa a /unprospect-messages.
argument-hint: <workspace> <campaña>
---

# GTM Copy — copywriting por frameworks

## Antes de empezar (contrato de memoria)
1. Lee `LEARNINGS.md` en este directorio: qué frameworks han ganado por vertical.
2. Lee del workspace: `PROFILE.md` (tono y vocabulario del mercado), `LEARNINGS.md`, y el `BRIEF.md` de la campaña en `campaigns/`.
3. Si la campaña viene de un experimento, lee su diseño en el BRIEF: las variantes DEBEN respetar la matriz del experimento.

## Frameworks disponibles
Escribe cada secuencia en 2–3 frameworks distintos y compáralos antes de elegir:

| Framework | Estructura | Cuándo brilla |
|---|---|---|
| **Observación directa** | Observación específica del lead → implicación → pregunta | Cuando el dolor observable es visible lead por lead (el más fuerte para dolor observable) |
| **PAS** | Problema → Agitación → Solución | Dolor intenso y consciente |
| **BAB** | Before → After → Bridge | Cuando el "after" es vívido y medible |
| **PPP** | Praise → Picture → Push | Leads con logro público reciente |
| **QVC** | Question → Value prop → CTA | Emails ultra cortos, steps 2+ |
| **1-2-3** | "3 cosas que noté de tu X" | Auditorías/diagnósticos como offer |

## Reglas de copy (no negociables)
- El email 1 debe demostrar en la primera línea que vimos algo específico de SU empresa (ahí entra `/unprospect-research`).
- Menos de 90 palabras por email; una sola idea; un solo CTA de fricción baja (el front-end offer, no "una llamada de 30 min").
- Cero palabras de spam obvias; escribir como se habla — aplicar el test de la cena.
- El idioma y vocabulario salen del `PROFILE.md` del workspace, no del default.

## Variantes A/B
La variable del test es **la hipótesis de dolor** (definida en el BRIEF/experimento). Las variantes mantienen constante: framework, largo, CTA, offer. Si quieres testear framework, es OTRO experimento — nunca dos variables a la vez.

## Salida
Escribe `campaigns/<campaña>/COPY.md`: secuencia completa por variante (3–4 steps), framework usado, hipótesis de dolor de cada variante, y los campos de personalización esperados de `/unprospect-research`. Formato listo para subir a Instantly (con spintax si aplica).

## Al terminar (contrato de memoria)
- Registra en `LEARNINGS.md` de este skill: qué framework se eligió y por qué. Cuando `/gtm-retro` traiga resultados, aquí se registra qué framework ganó por segmento/vertical.
