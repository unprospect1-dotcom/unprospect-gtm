# Compatibilidad Claude Code ↔ Codex

## Decisión de arquitectura

`.claude/skills/` permanece como fuente canónica de workflows, scripts, referencias y memoria.
Codex descubre un adaptador por skill en `.agents/skills/`. El adaptador carga el skill canónico y
aplica únicamente equivalencias de harness. No se duplica la lógica de GTM ni los `LEARNINGS.md`.

Esta decisión preserva Claude Code y evita que dos copias completas de cada skill diverjan.

## Equivalencias

| En el skill canónico | En Codex |
|---|---|
| `/gtm-nombre` | `$gtm-nombre` o selección desde `/skills` |
| `WebFetch` | Herramienta web, navegador o conector disponible que mejor cubra la fuente |
| `Task` / subagente de Claude | Subagente de Codex cuando esté disponible y el skill permita delegación |
| `haiku` | Modelo/subagente más rápido y económico disponible; registra el modelo real |
| `sonnet` / verificador fuerte | Modelo o pasada independiente más capaz disponible; registra el modelo real |
| “en este directorio” | El directorio canónico `.claude/skills/<skill>/` |
| `.claude/skills/...` | Ruta compartida intencional; no cambiarla a `.agents/skills/...` |

Si una capacidad del harness no existe, conserva el contrato del workflow y ejecútalo secuencialmente;
no inventes resultados ni llames una API externa como sustituto sin autorización.

## Descubrimiento de instrucciones

Codex carga `AGENTS.md` como guía durable del repositorio y descubre skills de proyecto en
`.agents/skills`. Los adaptadores tienen `name` y `description` para descubrimiento progresivo y
referencian el `SKILL.md` canónico completo.

Fuentes oficiales:

- [Guía de AGENTS.md](https://developers.openai.com/codex/concepts/customization#agents-guidance)
- [Skills de Codex](https://developers.openai.com/codex/concepts/customization#skills)

## Agregar o cambiar un skill

1. Crea o actualiza `.claude/skills/<skill>/SKILL.md` y sus assets.
2. Crea o actualiza `.agents/skills/<skill>/SKILL.md` como adaptador, sin copiar el workflow.
3. Conserva el mismo `name` que el directorio.
4. Ejecuta `python scripts/check_agent_compat.py`.
5. Ejecuta las pruebas y revisa que el diff de `.claude/` sea intencional.

## Límites conocidos

- `gtm-web-crawler/setup.sh` es POSIX/Linux. Codex en Windows necesita WSL o contenedor.
- Los nombres de modelos son sugerencias de costo/capacidad, no IDs portables entre harnesses.
- Los skills de `reference/coldoutboundskills/` siguen siendo referencia y no se exponen como skills
  activos de Codex.
