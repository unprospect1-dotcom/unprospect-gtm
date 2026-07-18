# Unprospect GTM OS — instrucciones para Codex

## Objetivo y mapa rápido

- Este repositorio es un sistema operativo de cold outbound con memoria por cliente.
- `.claude/skills/` es la fuente canónica compartida de los workflows y sus `LEARNINGS.md`.
- `.agents/skills/` contiene adaptadores pequeños para que Codex descubra esos mismos workflows.
- `workspaces/<workspace>/` guarda el conocimiento específico de cada cliente.
- `supabase/migrations/` define la memoria estructurada y `scripts/` contiene los ejecutores.
- `reference/coldoutboundskills/` es material de referencia: no son skills activos del producto.

Lee `ARCHITECTURE.md` antes de cambios amplios. Para compatibilidad entre agentes, lee
`docs/CODEX-COMPATIBILITY.md`.

## Convenciones de trabajo

- Opera siempre sobre un workspace explícito. Si el usuario no lo da, usa `unprospect` y dilo.
- Antes de producir una campaña o lista, lee los artefactos de entrada que indique el skill.
- Para trabajo de Unprospect, lee `workspaces/unprospect/PROFILE.md` como contexto central del producto.
- No avances al siguiente paso si el artefacto requerido no existe o no está aprobado.
- Mantén la regla de memoria: consulta antes de contactar y registra evidencia/aprendizajes al terminar.
- Un dato no confirmado vale `null`/`NOT_FOUND`; nunca inventes dominios, perfiles, métricas ni fuentes.
- Conserva `.claude/skills/` como implementación canónica. No copies lógica dentro de los adaptadores
  de `.agents/skills/`.

## Claude Code ↔ Codex

- En Codex, `$gtm-*` equivale a la invocación `/gtm-*` descrita por los skills canónicos.
- `WebFetch`, `Task` y nombres de modelos de Claude se traducen según
  `docs/CODEX-COMPATIBILITY.md`; no se reescribe el workflow de negocio.
- Las rutas `.claude/skills/...` son intencionales: contienen scripts, referencias y memoria compartida.
- Cuando se agregue o elimine un skill canónico, agrega o elimina su adaptador Codex en el mismo cambio.

## Seguridad, gasto y datos

- Nunca imprimas, registres ni comitees API keys, service-role keys o tokens.
- Las consultas gratuitas y de solo lectura pueden ejecutarse si están dentro del pedido.
- Antes de cualquier llamada pagada, export masivo, reveal, envío de campaña o escritura externa,
  presenta el costo/impacto y respeta el gate de aprobación del skill.
- No hagas llamadas reales a proveedores durante tests.
- No comitees nuevos CSV/JSON de leads o replies. Guarda salidas operativas bajo `lists/` siguiendo
  `.gitignore`, y persiste la fuente durable en Supabase cuando el skill lo exija.

## Subagentes

Cuando un skill canónico pida subagentes paralelos y el trabajo pueda dividirse en lotes independientes,
delégalo con los **lanes definidos en el repo** — nunca con un subagente genérico sin modelo explícito:

- **Codex:** lanes en `.codex/agents/*.toml` (`gtm_classifier`, `gtm_verifier`, `gtm_profile_a/b/c`),
  `gpt-5.4-mini` esfuerzo `low`, sandbox read-only (el worker devuelve la salida; el orquestador la guarda).
- **Claude Code:** agentes en `.claude/agents/*.md` (`gtm-classifier`, `gtm-verifier`, `gtm-profiler`)
  con `model` barato fijado en el frontmatter. Un subagente sin `model` HEREDA el modelo de la sesión
  (Opus/Fable ≈ 5-10x Haiku): esa herencia fue la causa del run carísimo de julio 2026.

El orquestador materializa el contexto en disco ANTES de despachar (los workers no hacen red) y lanza
oleadas paralelas. Cada worker escribe/devuelve archivos únicos; ningún worker modifica `LEARNINGS.md`,
Supabase ni un mismo archivo compartido. El agente principal valida, fusiona y persiste los resultados.
Si la superficie actual no ofrece subagentes, ejecuta el mismo contrato secuencialmente.
Guía completa: `docs/SUBAGENTS.md`.

## Compatibilidad de plataforma

- Python soportado: 3.10 o superior. Usa `python` en Windows y `python3` en POSIX cuando corresponda.
- Los scripts generales son stdlib salvo los que declaran `requests` y el crawler.
- `gtm-web-crawler/setup.sh` requiere Bash/Linux y privilegios para instalar `libnss3-tools`. En Windows,
  usa WSL/contenedor; no simules que el bootstrap POSIX funcionó nativamente.

## Verificación

Ejecuta desde la raíz:

```text
python scripts/check_agent_compat.py
python -m unittest discover -s tests -p "test_*.py"
python -m compileall -q .
```

En una máquina donde `python` no esté en PATH, usa el ejecutable Python disponible en el entorno.
No ejecutes pruebas de integración con APIs salvo que el usuario lo pida y autorice el costo.

## Definición de terminado

- El cambio conserva el descubrimiento y los paths de Claude Code.
- La capa Codex pasa `check_agent_compat.py`.
- Las pruebas y la compilación Python pasan, o se documenta con precisión un bloqueo de entorno.
- La documentación refleja la estructura y los comandos reales.
- El diff no contiene secretos ni nuevos datos personales/operativos.
