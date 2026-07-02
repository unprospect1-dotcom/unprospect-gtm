---
name: gtm-onboard
description: Onboarding de un workspace (cliente nuevo o Unprospect). Lee el website y fuentes públicas, analiza el negocio a fondo y crea la memoria persistente en workspaces/<ws>/PROFILE.md para que nada se olvide. Usar al arrancar con un cliente nuevo o para refrescar el perfil de uno existente.
argument-hint: <workspace> <website-url>
---

# GTM Onboard — crear/refrescar la memoria de un workspace

## Antes de empezar (contrato de memoria)
1. Lee `LEARNINGS.md` en este directorio y aplica lo aprendido en onboardings pasados.
2. Si `workspaces/<workspace>/` no existe, cópialo desde `workspaces/_template/`.
3. Si ya existe un `PROFILE.md`, léelo primero: esto es un refresh, no un reemplazo — conserva lo que siga siendo válido y marca lo que cambió.

## Pasos

### 1. Análisis del website
Con WebFetch, lee el sitio (home, /pricing, /about, casos de estudio, blog reciente). Extrae:
- Qué vende exactamente y a quién (en sus propias palabras, luego en las tuyas).
- Propuesta de valor y diferenciadores que ellos mismos destacan.
- Pruebas sociales: logos, testimonios, números.
- Tono de voz y vocabulario del mercado (esto alimenta a `/gtm-copy`).

### 2. Análisis del negocio
- ICP hipotético: industria, tamaño, rol del decisor, geografía, idioma.
- Modelo de pricing y ticket estimado → esto define cuánto puede costar adquirir un cliente y qué tan agresivo puede ser el outbound.
- Competidores visibles y cómo se posicionan distinto.

### 3. Hipótesis de dolor observable
Lista 5–10 dolores probables de su ICP que sean **observables desde fuera** (ej. equipo comercial de 3–10 personas sin SDRs, corren Google Ads pero sin landing dedicada, sitio sin caso de estudio del vertical). Estas hipótesis son el insumo de `/gtm-pain-segments`.

### 4. Escribir la memoria
Llena `workspaces/<workspace>/PROFILE.md` siguiendo su estructura. Regla: cada afirmación importante lleva su fuente (URL o "hipótesis"). Fecha el análisis.

### 5. Confirmar con el usuario
Presenta un resumen de 10 líneas y pregunta qué corregir. **Las correcciones del usuario valen más que tu análisis** — intégralas al PROFILE.md marcadas como `[confirmado por el cliente]`.

## Al terminar (contrato de memoria)
- Registra en `LEARNINGS.md` de este skill: qué fuentes dieron mejor señal, qué se te escapó y el usuario corrigió, qué preguntas de confirmación resultaron más útiles.
