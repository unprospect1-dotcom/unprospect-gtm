# Prompts afinados de este workspace

Activos producidos por `/gtm-prompt-tuner`: un `.md` por prompt con frontmatter
(goal, segmento, fecha, rondas hasta converger, schema de salida) y el prompt como cuerpo.

El frontier los afina una vez; un modelo barato los ejecuta a escala
(`scripts/run_prompt.py`, config en `config/providers.yaml` sección `models`).
Re-tunear solo cuando cambie el segmento/offer o cuando `/gtm-retro` traiga
evidencia de clasificación errónea.
