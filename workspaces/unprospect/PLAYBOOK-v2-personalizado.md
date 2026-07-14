# Unprospect Outbound Playbook v2 — personalización del sitio + buckets por equipo de ventas + A/B Google Ads

> Reescritura del playbook original (PLAYBOOK-teamsize-googleads.md) con la capa de
> personalización extraída del crawl ($0, site_crawls.clean_text). Idioma base: es-MX.
> Registro: "tú" (estándar B2B moderno MX). Para despachos contables/legales considerar
> "usted" en la pasada de copy por campaña (/gtm-copy decide por universo).

## 0. Los tres campos de personalización (del crawl, no de la imaginación)

| Campo | Qué es | Regla |
|---|---|---|
| `{{oferta_corta}}` | Qué vende la empresa, 3–6 palabras, EN SU VOCABULARIO (del sitio) | Se afirma sin hedge — está en su sitio |
| `{{a_quien}}` | A quién le vende, según evidencia del sitio (sectores, casos, clientes) | Se afirma suave ("por lo que veo en su sitio") |
| `{{gancho}}` | UNA observación específica verificable (caso de éxito, sector nombrado, servicio bandera) | Solo si confianza alta; máx. 1 por email |

**Cadena de fallback (nunca en blanco):**
1. `{{gancho}}` disponible → apertura con gancho.
2. Sin gancho → apertura con `{{oferta_corta}}` + `{{a_quien}}`.
3. Sin extracción confiable → degradar a la versión genérica por industria (playbook v1). Registrar el nivel usado por lead para poder medir su efecto después.

## 0.1 La regla de congruencia del hedge (dónde va la humildad y dónde NO)

- **El hedge va en las INFERENCIAS** (tamaño del equipo comercial, founder-led, señal de Ads):
  ahí sí puedes estar equivocado, y equivocarse con humildad genera replies de corrección —
  una corrección es una conversación abierta.
- **El hedge NO va en lo verificable del sitio** (`{{oferta_corta}}`, `{{gancho}}`): hedgear lo
  que está publicado en su web te hace ver que no lo leíste.
- **Máximo UN hedge por email.** Nunca en el CTA.
- Frases aprobadas de humildad (rotar): "puedo estar equivocado", "LinkedIn no siempre
  refleja la realidad", "corrígeme si leí mal", "si me equivoco, dime y no insisto",
  "desde fuera es difícil saberlo".

## 0.2 Paleta de aperturas (para que el "I saw that" no se repita)

| # | Tipo | Molde | Cuándo |
|---|---|---|---|
| A1 | Gancho del sitio (afirmativa) | "Estuve viendo el sitio de {{company}} — {{gancho}}." | Gancho de confianza alta |
| A2 | Parece ser (inferencia + hedge) | "{{company}} parece ser una firma que vende {{oferta_corta}} a {{a_quien}} — corrígeme si leí mal." | El estándar preferido |
| A3 | Pregunta directa | "¿La venta nueva de {{company}} sigue dependiendo sobre todo de referidos?" | Buckets 0–1 y 2–5 |
| A4 | Hipótesis con humildad | "Puedo estar equivocado — LinkedIn no siempre refleja la realidad — pero {{company}} parece operar con un equipo comercial chico para lo que vende." | Cuando la observación ES el routing |
| A5 | Mercado primero | "Entre las firmas que venden {{oferta_corta}}, casi ninguna tiene un sistema de prospección — la venta la carga el dueño." | Cuando no quieres personalizar la 1a línea |

Regla: dentro de un mismo bucket, cada ángulo usa una apertura DISTINTA de la paleta.
El A/B de Ads mantiene la apertura constante entre variantes (la apertura no es la variable).

## 1. Posicionamiento y lógica de secuencia

Sistema outbound = el output de un equipo completo de prospección por una fracción del costo.
Email 1 prueba interés estratégico. Email 2 es el proof magnet: una muestra corta de cuentas
objetivo que demuestra la calidad del trabajo pagado — **enmarcada en el ICP del prospecto**
(`{{a_quien}}`), no en "su industria".

CTAs aprobados (rotar, mantener por campaña):
- ¿Crees que un sistema así le daría a {{company}} una ventaja competitiva?
- ¿Crees que algo así ayudaría a {{company}} a llegar a sus metas comerciales este año?
- ¿Crees que algo así le generaría a {{company}} más conversaciones calificadas con cuentas de mejor fit?

## 2. Buckets por equipo de ventas visible (routing oculto — NUNCA se menciona el conteo)

| Ventas visibles | Realidad probable | Dolor primario | Framing Unprospect |
|---|---|---|---|
| 0–1 | Vende el fundador | El pipeline depende de una persona y de referidos | Crear pipeline calificado antes de contratar prospección |
| 2–5 | Equipo comercial chico | Saben vender; prospectar no es un sistema | Función completa de prospección alrededor del equipo |
| 6–15 | Organización creciendo | Outbound inconsistente, fragmentado | Estandarizar research, datos, mensajes, secuencias, follow-up |
| 16–50 | Organización estructurada | Segmentos nuevos, capacidad por rep, QA | Experimentos GTM enfocados + capa de prospección |
| 50+ | Organización madura | Puntos ciegos, localización, jugadas estratégicas | Sistemas outbound dirigidos a oportunidades sub-trabajadas |

---

## 3. Bucket 0–1: venta del fundador

### Ángulo: cuello de botella del fundador (apertura A4 — hipótesis con humildad)

**Email 1 — CTA de interés** · Asunto: sistema de prospección

Hola {{first_name}},

Puedo estar equivocado — LinkedIn no siempre refleja la realidad — pero {{company}} parece
seguir dependiendo del fundador para la venta nueva.

Para una firma que vende {{oferta_corta}} a {{a_quien}}, el problema casi nunca es saber
vender — es que el negocio nuevo depende de una sola persona abriendo puertas, dando
seguimiento y empujando oportunidades.

Construimos sistemas outbound que le dan a empresas así el output de un equipo completo de
prospección, sin contratarlo.

¿Crees que algo así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2 — proof magnet** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo mi nota anterior.

En vez de explicarte el sistema en teoría, te puedo mandar una muestra corta de cuentas
objetivo para {{company}}: algunas {{a_quien}} que se ven como fit fuerte, por qué cada una
valdría la pena, y el ángulo que usaría para abrir la conversación.

¿Te serviría?

Saludos,
Camilo

### Ángulo: techo de referidos (apertura A3 — pregunta directa)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

¿La venta nueva de {{company}} sigue dependiendo sobre todo de referidos y relaciones?

Es lo normal en firmas que venden {{oferta_corta}} — funciona bien, pero es imposible de
pronosticar.

Construimos sistemas outbound que agregan una capa proactiva de pipeline alrededor de eso:
research de cuentas, mensajes, secuencias y follow-up — sin contratar un equipo de prospección.

¿Crees que algo así ayudaría a {{company}} a llegar a sus metas comerciales este año?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Le sumo algo a mi nota anterior.

En lugar de mandarte un checklist genérico, te armo una muestra corta de cuentas objetivo
para {{company}}: el tipo de {{a_quien}} que valdría la pena abrir proactivamente, por qué
hacen fit, y cómo los abordaría.

¿Te serviría?

Saludos,
Camilo

### Ángulo: antes de la primera contratación comercial (apertura A2 — parece ser)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece ser una firma que vende {{oferta_corta}} a {{a_quien}} — corrígeme si
leí mal — y quizá está en la etapa donde el siguiente paso sería contratar ventas o
desarrollo de negocio.

Antes de asumir esa nómina, suele convenir validar qué tipos de cuenta, compradores y
mensajes generan conversaciones de verdad.

Construimos sistemas outbound que producen el output de un equipo de prospección antes de
que te comprometas con la contratación.

¿Crees que algo así sería útil antes de tu siguiente contratación comercial?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo mi nota.

Te puedo armar una muestra corta de cuentas objetivo para {{company}} en vez de solo
describir el sistema: algunas cuentas potenciales del perfil {{a_quien}}, por qué parecen
fit, y el ángulo de apertura que probaría antes de invertir en un prospector de tiempo completo.

¿Te serviría?

Saludos,
Camilo

---

## 4. Bucket 2–5: equipo comercial chico

### Ángulo: los reps cierran, pero no prospectan consistentemente (apertura A2)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Por lo que veo en su sitio, {{company}} vende {{oferta_corta}} a {{a_quien}} — y parece
operar con un equipo comercial compacto.

En ese modelo, lo difícil no suele ser cerrar cuando hay interés — es abrir
consistentemente las cuentas correctas.

Construimos sistemas outbound que le dan a equipos chicos el output de una función completa
de prospección: research, datos, mensajes, secuencias y follow-up.

¿Crees que algo así ayudaría a {{company}} a llegar a sus metas comerciales este año?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Una idea más sobre mi nota anterior.

En vez de solo hablar del sistema, te mando una muestra corta de cuentas objetivo para
{{company}}: algunas {{a_quien}} que hacen fit, por qué, y el ángulo con el que el equipo
podría abrir la conversación.

¿Te serviría?

Saludos,
Camilo

### Ángulo: el impuesto de prospectar a mano (apertura A3)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Pregunta rápida — ¿tus reps en {{company}} arman sus propias listas, investigan cuentas y
escriben sus propios follow-ups?

Vendiendo {{oferta_corta}}, cada hora de un rep en Excel es una hora que no está en una
conversación con {{a_quien}}.

Construimos sistemas outbound que se encargan del trabajo de prospección alrededor del
equipo, para que los reps pasen más tiempo en conversaciones calificadas.

¿Crees que algo así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo lo de la carga de prospección.

Te mando una muestra corta de cuentas objetivo para {{company}} para aterrizar la idea:
algunas {{a_quien}} con fit fuerte, por qué cada una es relevante, y el ángulo de apertura
que le daría al equipo.

¿Te serviría?

Saludos,
Camilo

### Ángulo: de reactivo a proactivo (apertura A1 — gancho del sitio)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Estuve viendo el sitio de {{company}} — {{gancho}}.

Me dio curiosidad: ¿hoy están sobre todo respondiendo a la demanda que llega, o tienen un
sistema para abrir proactivamente exactamente las cuentas que quieren?

La diferencia no suele ser más actividad — es tener una forma repetible de identificar y
abrir cuentas de mejor fit.

Construimos sistemas outbound que convierten mercados objetivo en listas de cuentas,
ángulos de compra, mensajes, secuencias y follow-up.

¿Crees que un sistema así haría a {{company}} más proactiva comercialmente?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Le sumo a mi última nota.

Te mando una muestra corta de cuentas objetivo para {{company}} en vez de explicar el
sistema en abstracto: algunas {{a_quien}} que valdría la pena abrir, por qué hacen fit, y
el mensaje con el que generaría la primera conversación.

¿Te serviría?

Saludos,
Camilo

---

## 5. Bucket 6–15: organización de ventas creciendo

### Ángulo: diseño de sistema y estandarización (apertura A4)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Desde fuera es difícil saberlo — así que corrígeme si me equivoco — pero {{company}} parece
tener un equipo comercial en crecimiento.

Cuando un equipo que vende {{oferta_corta}} crece, el problema deja de ser esfuerzo y
empieza a ser diseño de sistema: selección de cuentas, calidad de datos, mensajes, ruteo y
consistencia del follow-up.

Construimos sistemas outbound que le dan a equipos en crecimiento el output de una función
dedicada de prospección, sin sumar headcount.

¿Crees que algo así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo por aquí.

En vez de solo describir un sistema estandarizado, te mando una muestra corta de cuentas
objetivo para {{company}}: cuentas del perfil {{a_quien}}, la lógica de fit detrás de cada
una, y el ángulo de apertura que se podría estandarizar para todo el equipo.

¿Te serviría?

Saludos,
Camilo

### Ángulo: huecos de cobertura de pipeline (apertura A3)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Pregunta directa — ¿sientes que el equipo de {{company}} está cubriendo el mercado completo
de {{a_quien}}, o sobre todo trabajando las cuentas obvias, tibias o conocidas?

Segmentos valiosos se quedan intactos simplemente porque los reps van por donde el camino
es más fácil.

Construimos sistemas outbound que ayudan a los equipos a cubrir más mercado sin pedirle a
cada rep que investigue y abra cada cuenta a mano.

¿Crees que algo así ayudaría a {{company}} a llegar a sus metas comerciales este año?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Contexto sobre mi última nota.

Te mando una muestra corta de cuentas objetivo para {{company}} enfocada en cuentas o
subsegmentos de {{a_quien}} que el equipo quizá no está cubriendo hoy — con el porqué de
cada una y la tesis con la que abriría la conversación.

¿Te serviría?

Saludos,
Camilo

### Ángulo: fuga en el follow-up (apertura A5 — mercado primero)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

En casi todas las firmas que venden {{oferta_corta}}, las oportunidades no se pierden por
falta de interés — se pierden porque el siguiente toque no agrega ninguna razón nueva para
seguir la conversación.

¿En {{company}} hay un proceso definido de follow-up post-reply y post-propuesta, o depende
de cada rep?

Construimos sistemas outbound que incluyen lógica de follow-up diseñada para mantener en
movimiento las oportunidades calificadas.

¿Crees que algo así ayudaría a {{company}} a convertir más del pipeline que ya generan?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo lo del follow-up.

Te mando una muestra corta de cuentas objetivo para {{company}} — {{a_quien}} con fit — y
le incluyo el ángulo de apertura más uno o dos ángulos de follow-up por cuenta. Ahí se ve
la diferencia entre una lista y un sistema outbound.

¿Te serviría?

Saludos,
Camilo

---

## 6. Bucket 16–50: organización de ventas estructurada

### Ángulo: probar segmentos nuevos (apertura A2)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece ser de las firmas más estructuradas vendiendo {{oferta_corta}} — y a ese
tamaño la pregunta ya no es si el equipo sabe vender.

Es si hay segmentos nuevos que valdría la pena probar y que los reps internos no tienen
bandwidth para validar de punta a punta.

Construimos sistemas outbound que prueban segmentos nuevos con research, mensajes,
secuencias y follow-up — antes de asignarles capacidad interna de ventas.

¿Crees que algo así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo lo de probar segmentos.

Te mando una muestra corta de cuentas objetivo para {{company}} alrededor de un segmento
potencial adyacente a {{a_quien}}: las cuentas, por qué el segmento puede valer la pena, y
el ángulo con el que abriría las primeras conversaciones.

¿Te serviría?

Saludos,
Camilo

### Ángulo: productividad por rep y abasto de pipeline (apertura A3)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Pregunta rápida — ¿el pipeline en {{company}} está parejo entre reps, o algunos
consistentemente tienen mejor cobertura de cuentas que otros?

A este tamaño el problema rara vez es headcount. Es si cada rep tiene suficientes
conversaciones calificadas con {{a_quien}} para justificar su capacidad.

Construimos sistemas outbound que generan más conversaciones calificadas alrededor del
equipo existente, en vez de resolver todo con más contrataciones.

¿Crees que algo así ayudaría a {{company}} a llegar a sus metas comerciales este año?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Contexto a mi última nota.

Te mando una muestra corta de cuentas objetivo para {{company}} diseñada como si estuviera
alimentando a uno de tus reps: la lógica de selección, por qué cada {{a_quien}} hace fit, y
el ángulo que el rep usaría para abrir.

¿Te serviría?

Saludos,
Camilo

### Ángulo: control de calidad del outbound (apertura A5)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Cuando varios reps ejecutan outbound por su cuenta, la calidad se fragmenta rápido: listas,
mensajes, personalización y follow-up distintos por rep — y el mercado recibe una tesis
comercial borrosa.

¿En {{company}} el mensaje outbound está centralizado, o cada rep escribe su versión?

Construimos sistemas outbound que estandarizan la capa de prospección detrás del equipo,
para que {{a_quien}} reciba una tesis comercial más filosa y consistente.

¿Crees que algo así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo lo de la consistencia.

Te mando una muestra corta de cuentas objetivo para {{company}} construida alrededor de UNA
tesis consistente de selección y mensaje: las cuentas, por qué hacen fit, y el ángulo
exacto que estandarizaría para la prueba.

¿Te serviría?

Saludos,
Camilo

---

## 7. Bucket 50+: organización de ventas madura

### Ángulo: descubrir puntos ciegos (apertura A2)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece tener una organización comercial madura — así que esto no va de "más
outbound".

A esta escala la oportunidad suele estar en segmentos, triggers y patrones de cuenta que el
motion actual no está priorizando dentro del mercado de {{a_quien}}.

Construimos sistemas outbound para experimentos GTM enfocados: segmentos sub-trabajados,
señales de compra y patrones de cuenta.

¿Crees que algo así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo por aquí.

Te mando una muestra corta de cuentas objetivo para {{company}} construida alrededor de un
posible punto ciego: las cuentas, la señal o patrón detrás de ellas, y la tesis de apertura
que probaría.

¿Te serviría?

Saludos,
Camilo

### Ángulo: penetración localizada (apertura A3)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Pregunta rápida — ¿{{company}} adapta el outbound por mercado o región, o el mensaje sigue
siendo bastante global?

Los equipos grandes pueden tener cobertura amplia sin resonancia local: cómo {{a_quien}} de
cada mercado describe el problema, evalúa la prueba y decide, cambia por país.

Construimos sistemas outbound que localizan selección de cuentas, mensajes y follow-up para
mercados específicos como México y LATAM.

¿Crees que algo así ayudaría a {{company}} a generar más tracción local?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Sumo a mi última nota.

Te mando una muestra corta y localizada de cuentas objetivo para {{company}}: empresas del
mercado elegido, por qué hacen fit, y cómo adaptaría el ángulo de apertura al contexto de
compra local.

¿Te serviría?

Saludos,
Camilo

### Ángulo: desplazamiento competitivo (apertura A5)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Las oportunidades de mayor palanca casi nunca están en listas amplias — están en cuentas
con dolor de proveedor actual, señales de timing o triggers de expansión.

¿Las jugadas de desplazamiento de competidor son parte del motion outbound de {{company}},
o el equipo prospecta sobre todo por ICP y título?

Construimos sistemas outbound alrededor de esas jugadas: research de cuentas, lógica de
triggers, mensajes, secuencias y follow-up.

¿Crees que algo así le generaría a {{company}} conversaciones de mayor intención?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo lo del desplazamiento competitivo.

Te mando una muestra corta de cuentas objetivo para {{company}} basada en empresas con una
señal plausible de cambio o timing — con el porqué de cada una y el ángulo que usaría sin
inventar afirmaciones que no puedo sostener.

¿Te serviría?

Saludos,
Camilo

---

## 8. A/B de Google Ads

Solo cuando la misma empresa tiene equipo de ventas visible Y señal confiable de Google Ads.
Mantener constante: audiencia, asunto, estilo de CTA, remitente, cadencia, oferta **y la capa
de personalización** (los campos del crawl NO son la variable del test).

### Variante A — observación de Google Ads (apertura A2 aplicada a la señal)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece invertir en Google Ads — puedo estar equivocado, es lo que se ve desde fuera.

El search de paga trae demanda, pero no siempre el tipo exacto de {{a_quien}} que ventas
quiere cerrar.

Ahí es donde un sistema outbound funciona distinto: en vez de esperar a que la empresa
correcta busque, eliges primero las cuentas y construyes el research, los mensajes, las
secuencias y el follow-up alrededor de ellas.

¿Crees que un sistema así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo lo de paid search versus outbound.

En vez de explicar el sistema en teoría, te mando una muestra corta de cuentas objetivo
para {{company}}: algunas {{a_quien}} con mejor fit que el lead inbound o de paga promedio,
por qué cada una, y el ángulo que usaría.

¿Te serviría?

Saludos,
Camilo

### Variante B — observación por tamaño de equipo (idéntica al ángulo 1 del bucket 2–5)

Usar tal cual el ángulo "los reps cierran, pero no prospectan consistentemente" (sección 4),
misma personalización.

## 9. Setup y medición del test

- Solo empresas con AMBAS señales conocidas (Ads + tamaño de equipo).
- Split 50/50 aleatorio del mismo ICP.
- Constantes: asunto, remitente, cadencia, dominios, oferta del sample **y nivel de
  personalización** (no mezclar nivel 1-gancho con nivel 3-genérico entre variantes).
- Registrar por lead el **nivel de fallback usado** (gancho / oferta+a_quien / genérico) —
  es un experimento gratis dentro del experimento.
- Medir: positive replies, solicitudes del sample, replies que confirman dolor, y juntas —
  no solo reply rate.
- NUNCA afirmar el conteo del equipo en el email (routing oculto). El hedge existe justo
  para cuando la inferencia se asoma.
- No atacar Google Ads: outbound es complementario — paid search captura demanda; outbound
  elige y abre cuentas objetivo.

## 10. Resumen de routing

| Condición | Ángulo primario Email 1 | Apertura | Proof magnet |
|---|---|---|---|
| 0–1 ventas | Cuello de botella / referidos / pre-contratación | A4 / A3 / A2 | Sample que prueba el mercado antes de contratar |
| 2–5 ventas | Función de prospección alrededor del equipo | A2 / A3 / A1 | Cuentas {{a_quien}} + fit + ángulo |
| 6–15 ventas | Estandarización / cobertura / follow-up | A4 / A3 / A5 | Sample que muestra proceso repetible |
| 16–50 ventas | Segmentos / abasto por rep / QA | A2 / A3 / A5 | Sample por segmento alimentando al equipo |
| 50+ ventas | Puntos ciegos / localización / desplazamiento | A2 / A3 / A5 | Experimento por señal o segmento |
| Ads + equipo elegible | Demanda de paga sin control de ICP | A2 | Cuentas de mejor fit que el lead de paga promedio |

## 11. Pipeline de datos que llena los campos

1. `site_crawls.clean_text` (ya existe para 1,375 dominios A de TI + contable).
2. Extracción LLM 2 capas (patrón gtm-classify-b2b): capa 1 masiva barata → capa 2
   verificación ciega → `{{oferta_corta}}`, `{{a_quien}}`, `{{gancho}}` + nivel de confianza.
3. `list_companies.sales_count` (departmentSizes de Ocean, ya cargado) → bucket.
4. Señal Ads: GetLeads `where_sql MONTHLY_GOOGLE_ADSPEND_ORG > 0` → flag por dominio.
5. Todo se upserta a Supabase junto a la empresa; Instantly recibe las columnas como
   custom fields.
