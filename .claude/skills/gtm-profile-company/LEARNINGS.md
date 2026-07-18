# LEARNINGS — gtm-profile-company

## El run "carísimo y lento" en Claude Code — 2026-07-18

No fue el diseño del skill: fue el despacho. En Claude Code un subagente sin `model`
explícito **hereda el modelo de la sesión principal** (Opus/Fable ≈ 5-10x el costo de
Haiku por token), y el repo no tenía ningún agente definido en `.claude/agents/` — así que
"capa 1 con Haiku" en la práctica corría en el modelo grande, con TODAS las tools (schemas
MCP incluidos) y despacho secuencial. Fix permanente:

- Agente **`gtm-profiler`** (`model: haiku`, tools Read/Write) para la capa 1 y
  **`gtm-verifier`** (`model: sonnet`) para la revisión ciega — espejo de las lanes
  `.codex/agents/` que Codex ya tenía. Nunca despachar workers masivos sin agente nombrado.
- Oleadas paralelas: varios `Agent` en un mismo mensaje (corren en background), no uno por
  uno.
- El orquestador tampoco necesita el modelo grande: sesión `/model haiku`/`sonnet` para
  corridas masivas (equivalente al modo `gpt-5.4-mini` de Codex).

Señal de alarma para el futuro: si una capa 1 de cientos de dominios cuesta decenas de
dólares (o quema los límites de la sesión), un worker está heredando el modelo grande.
El orden correcto es centavos por lote de 10 en Haiku.

## Loop inicial con crawls reales — 2026-07-16

Muestra: 24 `clean_text` del crawler activo, balanceados por presencia/ausencia de señal B2B
y por texto corto, medio y largo. Dos pasadas ciegas con `gpt-5.4-mini`, esfuerzo `low`, en
lotes de 8. Todas las citas pasaron validación literal UTF-8.

Con la primera versión general del criterio:

| campo | acuerdo |
|---|---:|
| modelo de negocio | 21/24 (87.5%) |
| línea B2B presente | 23/24 (95.8%) |
| economía comercial | 19/24 (79.2%) |
| fit outbound | 22/24 (91.7%) |
| alcance outbound | 22/24 (91.7%) |

Los desacuerdos mostraron cuatro reglas necesarias:

1. Candidatos y participantes no son automáticamente clientes; identificar quién paga.
2. Reclutar agentes/comisionistas individuales no es B2B aunque se llamen empresarios.
3. Una mención genérica a “personas y empresas” no prueba una línea B2B.
4. Gobierno/educación requieren `noncommercial`, y medios sin pagador visible requieren
   `business_model=unclear` aunque su audiencia sea de consumo.

La segunda prueba cargó 12 casos difíciles y controles. Después de aplicar las primeras
cuatro reglas, las dos pasadas coincidieron 12/12 en `entity_type`, línea B2B, economía,
fit y alcance; coincidieron 11/12 en modelo de negocio. El único borde restante fue un sitio
de contenido sin pagador visible. La regla final separa audiencia de cliente y fija
`outbound_fit=low`/`scope=none` cuando no existe línea B2B demostrada.
Dos pasadas frescas posteriores coincidieron en los seis campos categóricos del caso.

## Calibración de contexto y revisión selectiva — 2026-07-17

Se comparó una pasada con contexto durable de hasta 8K contra una pasada ciega con contexto
de hasta 4K, preservando inicio y líneas de oferta, cliente, industria, casos y contacto.
Muestra: 24 dominios reales.

| campo | acuerdo 4K vs 8K |
|---|---:|
| tipo de entidad | 24/24 (100%) |
| modelo de negocio | 23/24 (95.8%) |
| línea B2B presente | 23/24 (95.8%) |
| economía comercial exacta | 19/24 (79.2%) |
| fit outbound exacto | 21/24 (87.5%) |
| alcance outbound | 23/24 (95.8%) |

El único error en la decisión B2B fue conservador: `b2b/high` terminó `unclear/medium`, no
como un falso B2C. Por eso cae automáticamente en revisión con 8K. Los otros desacuerdos de
fit fueron `medium` contra `high`; ambos siguen siendo aptos para outbound. Las diferencias de
economía fueron principalmente `plausible` contra `strong`, por lo que esa etiqueta no debe
usarse sola como exclusión.

Decisión operativa confirmada: no hacer dos pasadas completas. Usar 4K + lotes de 10 para
la primera pasada; revisar `mixed`, `unclear`, confianza no alta, economics/fit unclear,
inconsistencias y 5% determinístico de claros. Arbitrar solo desacuerdos. El hash evita volver
a pagar por dominios sin cambios.
