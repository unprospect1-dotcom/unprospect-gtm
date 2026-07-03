---
name: gtm-prompt-tuner
description: El loop tuner/worker - el modelo frontier redacta y afina un prompt sobre muestras de 10 filas con auto-crítica + correcciones del usuario hasta dos rondas limpias; el prompt bloqueado se guarda como activo en workspaces/<ws>/prompts/ y lo ejecutan a escala sub-agents con modelo barato (Claude Code o Codex, sin API externa). Usos - ICP-fit scoring de listas, relevancia/normalización de títulos (decisor vs influencer), y snippets de personalización cuando el playbook los pide. El prompt es el activo, no la corrida.
argument-hint: <workspace> <icp-fit | title-buyer | snippet <campo>> [archivo.csv de muestra]
---

# GTM Prompt Tuner — el frontier afina, el barato ejecuta

Escribir prompts a mano es lento; correr un modelo frontier sobre miles de filas es caro.
Este skill hace las dos cosas baratas: **Claude Code es el prompt engineer, el modelo barato es el worker.**

## Los 3 usos (mismo loop, distinto goal)

| Uso | Input por fila | Output JSON (máx 3 campos) | Cuándo |
|---|---|---|---|
| `icp-fit` | domain, name, industry, headcount, description | `{qualified, confidence, reason}` | Después del export del proveedor, antes del gate de calidad de `/gtm-lists` |
| `title-buyer` | job_title, seniority, headcount | `{rol_normalizado, bucket: decisor\|influencer\|descartar, confidence}` | Títulos dispersos: decidir a QUIÉN de la empresa contactar |
| `snippet <campo>` | La fila completa del lead | `{<campo>: "..."}` (ej. industria específica, caso de éxito del vertical) | **Solo cuando el BRIEF/playbook lo pide** — relevancia > personalización |

## El loop (se detiene solo)

1. **Contexto y meta.** Infiere del workspace (`PROFILE.md`, `SEGMENTS.md`, `BUYER-MAP.md`, `BRIEF.md` según el uso): qué es un buen resultado, qué descalifica, qué campos hay disponibles. Define el output schema (≤3 campos, siempre con `confidence`).
2. **Draft del prompt.** Claude lo redacta — el usuario NO escribe prompts. Estructura: rol, criterios de calificación, descalificadores duros, **ejemplos negativos** ("empresas como X NO encajan porque Y" vale más que criterios genéricos), formato de salida JSON.
3. **Corre sobre 10 filas** (mezcla de casos probables buenos y malos) vía Task sub-agent.
4. **Auto-crítica ANTES de mostrar:** Claude califica su propio output contra la meta y corrige el prompt donde falló. Luego presenta la tabla de 10 resultados + el prompt actual.
5. **Correcciones del usuario.** Cada corrección se traduce a regla/ejemplo en el prompt. **Una corrección resetea la racha a cero.** Nunca auto-aprobar.
6. **Dos rondas limpias consecutivas = prompt bloqueado.** Guárdalo (ver abajo). Si no converge en 5 rondas, el problema es la data de entrada, no el prompt — enriquece campos (description, headcount) antes de seguir.

Reglas del loop: lotes de 10 (50 de golpe esconde errores); mostrar el prompt completo tras cada ajuste; el tuning SIEMPRE ocurre dentro de Claude Code (sub-agents, sin API externa).

## El activo

Escribe `workspaces/<ws>/prompts/<uso>-<slug>.md`:

```markdown
---
goal: icp-fit | title-buyer | snippet:<campo>
segment: <segmento del workspace>
tuned_at: YYYY-MM-DD
rounds_to_convergence: N
input_fields: [domain, name, ...]
output_schema: {qualified: bool, confidence: float, reason: str}
execution: ver config/providers.yaml (sección execution)
---
<el prompt completo>
```

Re-tunear solo cuando cambie el segmento/offer o cuando `/gtm-retro` traiga evidencia de que el prompt clasifica mal.

## Ejecución a escala (fan-out de sub-agents — sin API externa)

El worker son **sub-agents del propio harness** (Claude Code o Codex) con el modelo barato del plan
(`execution.subagent_model`, ej. haiku): el prompt afinado va como instrucción, cada sub-agent
procesa su lote de filas y devuelve JSON. Config en `config/providers.yaml`, sección `execution`.

- Lotes de `rows_per_subagent` (10–20) por sub-agent — lotes más grandes degradan la calidad.
- Hasta `parallel_subagents` en paralelo; listas grandes en rondas de `rows_per_round` filas para no saturar el contexto de la sesión padre.
- **Merge por identificador estable de la fila** (email / domain / source_id) — nunca por posición.
- Muestreo de control al final: 10 filas al azar contra el criterio del prompt — si el worker degrada la calidad vs el frontier, sube `subagent_model` en la config; no toques el prompt.
- El activo es portable: el mismo prompt corre igual en Claude Code, Codex o cualquier API si algún día conviene.

## Al terminar
- A `LEARNINGS.md` de este skill: cuántas rondas tomó converger por tipo de uso, qué clase de ejemplos negativos aceleran la convergencia, y qué modelos worker mantienen la calidad del frontier.
