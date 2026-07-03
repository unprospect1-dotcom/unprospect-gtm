# Prompts afinados de este workspace

Activos producidos por `/gtm-prompt-tuner`: un `.md` por prompt con frontmatter
(goal, segmento, fecha, rondas hasta converger, schema de salida) y el prompt como cuerpo.

El frontier los afina una vez; los ejecutan a escala sub-agents con modelo barato
(Claude Code o Codex, sin API externa — config en `config/providers.yaml`, sección `execution`).
Re-tunear solo cuando cambie el segmento/offer o cuando `/gtm-retro` traiga
evidencia de clasificación errónea.
