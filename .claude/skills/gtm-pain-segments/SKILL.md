---
name: gtm-pain-segments
description: Segmenta el mercado por dolor probable OBSERVABLE (tamaño de equipo comercial, si corren Google Ads, stack visible, presencia digital) — no por señales de intención como contrataciones o funding. Produce segmentos accionables para campañas y los persiste en SEGMENTS.md y Supabase.
argument-hint: <workspace> [vertical o lista de empresas]
---

# GTM Pain Segments — segmentación por dolor observable

## Antes de empezar (contrato de memoria)
1. Lee `LEARNINGS.md` en este directorio.
2. Lee `workspaces/<ws>/PROFILE.md` (hipótesis de dolor del onboarding) y `SEGMENTS.md` (segmentos ya definidos — no dupliques).
3. Lee `workspaces/<ws>/LEARNINGS.md`: qué segmentos ya probaron y cómo les fue.

## Concepto clave
Un **dolor probable observable** es un atributo visible HOY desde fuera que implica un dolor con alta probabilidad:
- Equipo comercial de 2–5 en LinkedIn sin SDR → probablemente el founder prospecta a mano.
- Corren Google Ads (Ads Transparency Center) → pagan por demanda; el CAC les duele.
- Sitio sin caso de estudio del vertical X → les cuesta cerrar ese vertical.
- 40 camiones en la flota pero sin portal de tracking → servicio al cliente por WhatsApp/teléfono.

**NO son señales de intención** (contrataciones, funding, tech installs recientes). La diferencia: la señal expira, el atributo estructural no.

## Pasos

### 1. Generar la matriz de segmentos
Para el vertical objetivo, propone 4–8 segmentos como: **atributo observable → dolor probable → cómo verificarlo a escala**. Cada segmento debe cumplir:
- Verificable con datos que tenemos o podemos conseguir (Supabase `companies`, LinkedIn, Ads Transparency, el propio website).
- Suficientemente grande (estima el # de empresas de la base que caerían).
- Con un ángulo de copy obvio (si no puedes imaginar el primer email, el segmento no sirve).

### 2. Priorizar
Score 1–5 en: tamaño del segmento × intensidad del dolor × facilidad de verificación. Recomienda el top 2–3.

### 3. Persistir
- Escribe/actualiza `workspaces/<ws>/SEGMENTS.md` con la matriz, fecha y estado (`propuesto` / `verificando` / `activo` / `descartado`).
- Para segmentos verificables con la base actual: actualiza `companies.pain_signals` (jsonb) y `companies.pain_segment` vía la API de Supabase, o genera el script de clasificación (patrón de `segment_companies.py`).

## Al terminar (contrato de memoria)
- Registra en `LEARNINGS.md` de este skill: qué fuentes de verificación funcionaron, qué segmentos se descartaron y por qué (transferible entre clientes).
