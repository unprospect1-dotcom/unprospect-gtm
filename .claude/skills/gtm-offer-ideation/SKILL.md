---
name: gtm-offer-ideation
description: Idea front-end offers (lead magnets) por segmento de dolor — el "sí fácil" que el prospecto acepta antes de la oferta principal. Produce un catálogo priorizado en OFFERS.md. Usar después de gtm-pain-segments y antes de gtm-campaign-ideation.
argument-hint: <workspace> [segmento]
---

# GTM Offer Ideation — front-end offers / lead magnets

## Antes de empezar (contrato de memoria)
1. Lee `LEARNINGS.md` en este directorio (qué tipos de offer han funcionado antes, en cualquier cliente).
2. Lee `workspaces/<ws>/PROFILE.md`, `SEGMENTS.md` y `OFFERS.md` (no re-idees lo que ya existe).
3. Lee `workspaces/<ws>/LEARNINGS.md` para saber qué offers ya se probaron y su resultado.

## Concepto clave
Un front-end offer NO es la oferta principal con descuento. Es un entregable de valor inmediato, específico al **dolor del segmento**, que:
- Se consume en < 15 minutos y deja al prospecto más inteligente sobre SU problema.
- Demuestra la capacidad del negocio sin pedir compromiso.
- Tiene un puente natural hacia la oferta principal.

## Pasos

### 1. Generar por segmento
Para cada segmento activo de `SEGMENTS.md`, genera 3–5 offers usando estas familias (una idea por familia mínimo):
- **Auditoría/diagnóstico:** "te muestro tus 3 huecos de X" (personalizada, cara de producir, alta conversión).
- **Benchmark/dato:** "así se comparan 50 empresas como la tuya en X" (escalable, requiere datos que ya tenemos — la base de Supabase es un activo aquí).
- **Herramienta/calculadora:** algo que usan solos y les da un número que duele.
- **Playbook/teardown:** "cómo [competidor admirado] hace X, paso a paso".
- **Muestra del servicio:** una unidad pequeña del delivery real (ej. 10 leads calificados gratis).

### 2. Evaluar cada offer (score 1–5)
| Criterio | Pregunta |
|---|---|
| Especificidad al dolor | ¿Solo tiene sentido para ESTE segmento? (si sirve para todos, no sirve) |
| Costo de producir | ¿Podemos entregarlo sin morir si responden 30? |
| Puente a la oferta | ¿Consumirlo hace obvio el siguiente paso? |
| Prueba de capacidad | ¿Demuestra que sabemos hacer el trabajo? |

### 3. Persistir
Actualiza `workspaces/<ws>/OFFERS.md`: offer, segmento, familia, score, costo de producción, estado (`idea` / `en producción` / `activo` / `retirado`) y — cuando exista — su tasa de aceptación real por campaña.

## Al terminar (contrato de memoria)
- Registra en `LEARNINGS.md` de este skill los patrones transferibles (ej. "en logística, benchmark > playbook porque nadie comparte datos del sector").
