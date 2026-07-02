---
name: gtm-campaign-ideation
description: Idea campañas de cold email combinando segmento × dolor probable × front-end offer en ángulos concretos. Cada ángulo queda registrado en ANGLES.md y en la tabla angles de Supabase para nunca repetir ángulo con el mismo lead. Usar después de gtm-pain-segments y gtm-offer-ideation.
argument-hint: <workspace> [segmento]
---

# GTM Campaign Ideation — ángulos de campaña

## Antes de empezar (contrato de memoria)
1. Lee `LEARNINGS.md` en este directorio.
2. Lee del workspace: `PROFILE.md`, `SEGMENTS.md`, `OFFERS.md`, `ANGLES.md` y `LEARNINGS.md`. **`ANGLES.md` es crítico: no propongas ángulos ya quemados ni repitas contra el mismo segmento.**
3. Consulta la tabla `angles` de Supabase (filtrada por `workspace`) para ver métricas reales de ángulos pasados.

## Concepto clave
Un **ángulo** = (segmento, hipótesis de dolor, offer, mecanismo de credibilidad). El mismo segmento puede recibir campañas con ángulos distintos a lo largo del tiempo — por eso `outreach_log` registra el ángulo de cada envío: para recontactar con uno nuevo, nunca con el mismo.

## Pasos

### 1. Generar ángulos
Para el segmento elegido, 3–5 ángulos. Cada uno se escribe así:
- **Nombre corto** (slug único, ej. `logistica-cac-ads-benchmark`) — es la clave en Supabase.
- **Dolor:** la hipótesis observable que ataca (de `SEGMENTS.md`).
- **Apertura:** cómo el primer email evidencia que el dolor es real para ESE lead (la observación concreta, no un halago genérico).
- **Offer:** el front-end offer que se ofrece (de `OFFERS.md`).
- **Credibilidad:** por qué nos creerían (dato, caso, muestra).
- **Test de la cena:** ¿el email se podría leer en voz alta a un desconocido en una cena sin dar pena? Si no, el ángulo está forzado.

### 2. Priorizar y armar el plan
Recomienda 1–2 ángulos para lanzar y — si hay hipótesis de dolor en empate — pásalos a `/gtm-experiments` para diseñar el A/B. Estima el tamaño de lista por ángulo usando la base de Supabase.

### 3. Persistir
- Actualiza `workspaces/<ws>/ANGLES.md`: ángulo, fecha, estado (`propuesto` / `activo` / `ganador` / `quemado`), campañas donde se usó.
- Inserta el/los ángulos elegidos en la tabla `angles` de Supabase.
- Crea `workspaces/<ws>/campaigns/<YYYY-MM-slug>/BRIEF.md` con: segmento, ángulo, offer, lista estimada, hipótesis y criterio de éxito.

## Al terminar (contrato de memoria)
- Registra en `LEARNINGS.md` de este skill los patrones de ideación transferibles entre clientes.
