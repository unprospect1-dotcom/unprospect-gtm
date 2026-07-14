# Unprospect Outbound Playbook v2: templates + líneas AI del crawl + buckets por equipo de ventas + A/B Google Ads

> Reescritura del playbook original (PLAYBOOK-teamsize-googleads.md). Idioma base: es-MX.
> Registro: "tú" (estándar B2B moderno MX). Para despachos contables/legales considerar
> "usted" en la pasada de copy por campaña (/gtm-copy decide por universo).
> Regla de estilo: PROHIBIDOS los guiones largos (em dashes) en el copy. Comas, puntos o dos puntos.

## 0. Arquitectura: template fijo + líneas AI

Cada mensaje es un TEMPLATE fijo. Lo único que cambia por lead son las líneas generadas por
AI a partir del crawl del sitio (`site_crawls.clean_text`). Todo lo demás no se toca.

| Slot AI | Qué es | Regla dura |
|---|---|---|
| `{{linea_observacion}}` | UNA oración que dice qué hace la empresa y para quién, en su vocabulario. Ej: "Vi en su sitio que desarrollan software a la medida para aseguradoras y bancos." | Se AFIRMA, sin hedge. Lo que hacen siempre debería estar claro si checamos su web. La AI elige el sustantivo correcto (empresa, despacho, agencia, taller, estudio). |
| `{{linea_gancho}}` | Versión premium de la observación: un detalle específico verificable (caso de éxito, cliente nombrado, servicio bandera). Ej: "Vi en su sitio el caso que publicaron con una cadena de farmacias." | Solo con confianza alta. Sustituye a `{{linea_observacion}}`, no se suman. |
| `{{icp_corto}}` | Frase corta que nombra el tipo de cliente del prospecto, para el proof magnet. Ej: "manufactureras del Bajío", "filiales extranjeras en México". | Se usa dentro de "cuentas del perfil {{icp_corto}}" (construcción a prueba de género/número). |

**Cadena de fallback (nunca en blanco):**
1. `{{linea_gancho}}` disponible → se usa.
2. Si no → `{{linea_observacion}}`.
3. Si la extracción no es confiable → versión genérica del template (sin línea AI, abre con la pregunta o el contexto de mercado). Registrar el nivel usado por lead.

**Reglas para el prompt de generación de las líneas AI:**
- Una sola oración, máx ~18 palabras, vocabulario del sitio, cero adjetivos de halago.
- Sin guiones largos, sin comillas, sin "parece": las líneas AI afirman.
- Elegir el sustantivo natural del negocio (nunca "firma" por default: un despacho es
  despacho, una fábrica de software es empresa, una agencia es agencia).
- Si la evidencia es ambigua, no inventar: devolver confianza baja y caer al fallback.

## 0.1 Dónde va la humildad (y dónde nunca)

- **La línea de humildad va SOLO en la observación de estructura comercial**: tamaño del
  equipo de ventas, dependencia del fundador, señal de Ads. Eso viene de LinkedIn o de
  inferencia y puede estar mal. Equivocarse ahí con humildad genera replies de corrección,
  y una corrección es una conversación abierta.
- **Nunca en lo que hacen**: eso viene de su web y se afirma. Hedgear lo publicado en su
  sitio te hace ver que no lo leíste.
- Máximo UNA línea de humildad por email. Nunca en el CTA.
- Frases aprobadas (rotar): "puedo estar equivocado", "LinkedIn no siempre refleja la
  realidad", "el tamaño del equipo puede no verse desde fuera", "si me equivoco, dime y no insisto".

## 0.2 Paleta de aperturas (para que la observación no suene igual en todos)

| # | Tipo | Molde | Cuándo |
|---|---|---|---|
| A1 | Gancho del sitio | "Estuve viendo el sitio de {{company}}. {{linea_gancho}}" | Gancho de confianza alta |
| A2 | Observación + inferencia con "parece" | "{{linea_observacion}} Y desde fuera parece que [inferencia del bucket]." | El estándar |
| A3 | Pregunta directa | "¿La venta nueva de {{company}} sigue dependiendo sobre todo de referidos?" | Buckets 0–1 y 2–5 |
| A4 | Hipótesis con humildad | "Puedo estar equivocado, LinkedIn no siempre refleja la realidad, pero {{company}} parece operar con un equipo comercial chico." | Cuando la observación ES el routing |
| A5 | Mercado primero | "En casi todas las empresas que venden proyectos de ticket alto, el pipeline depende de referidos." | Fallback sin línea AI |

Regla: dentro de un mismo bucket, cada ángulo usa una apertura DISTINTA.
En el A/B de Ads la apertura y el nivel de personalización se mantienen constantes.

## 1. Posicionamiento y lógica de secuencia

**Value prop ancla (línea fija de todos los Email 1):**

> Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una fracción del costo.

Se permite adaptar el remate por bucket ("sin contratarlo", "alrededor de tu equipo actual",
"antes de comprometer nómina"), pero el ancla no cambia.

Email 1 prueba interés estratégico. Email 2 es el proof magnet: una muestra corta de cuentas
objetivo enmarcada en el ICP del prospecto (`{{icp_corto}}`), no en "su industria".

CTAs aprobados (rotar, mantener por campaña):
- ¿Crees que un sistema así le daría a {{company}} una ventaja competitiva?
- ¿Crees que algo así ayudaría a {{company}} a llegar a sus metas comerciales este año?
- ¿Crees que algo así le generaría a {{company}} más conversaciones calificadas con cuentas de mejor fit?

## 2. Buckets por equipo de ventas visible (routing oculto, NUNCA se menciona el conteo)

| Ventas visibles | Realidad probable | Dolor primario | Framing Unprospect |
|---|---|---|---|
| 0–1 | Vende el fundador | El pipeline depende de una persona y de referidos | Crear pipeline calificado antes de contratar prospección |
| 2–5 | Equipo comercial chico | Saben vender; prospectar no es un sistema | Función completa de prospección alrededor del equipo |
| 6–15 | Organización creciendo | Outbound inconsistente, fragmentado | Estandarizar research, datos, mensajes, secuencias, follow-up |
| 16–50 | Organización estructurada | Segmentos nuevos, capacidad por rep, QA | Experimentos GTM enfocados + capa de prospección |
| 50+ | Organización madura | Puntos ciegos, localización, jugadas estratégicas | Sistemas de prospección dirigidos a oportunidades sub-trabajadas |

---

## 3. Bucket 0–1: venta del fundador

### Ángulo: cuello de botella del fundador (apertura A2)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{linea_observacion}} Y desde fuera parece que la venta nueva todavía pasa por el fundador.

Cuando es así, el problema casi nunca es saber vender: es que el negocio nuevo depende de
una sola persona abriendo puertas, dando seguimiento y empujando oportunidades.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, sin contratarlo.

¿Crees que algo así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo mi nota anterior.

En vez de explicarte el sistema en teoría, te mando una muestra corta de cuentas objetivo
para {{company}}: cuentas del perfil {{icp_corto}}, por qué cada una vale la pena, y el
ángulo que usaría para abrir la conversación.

¿Te serviría?

Saludos,
Camilo

### Ángulo: techo de referidos (apertura A3)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

¿La venta nueva de {{company}} sigue dependiendo sobre todo de referidos y relaciones?

Funciona bien, pero es imposible de pronosticar.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo: research de cuentas, mensajes, secuencias y follow-up alrededor de lo
que ya tienes.

¿Crees que algo así ayudaría a {{company}} a llegar a sus metas comerciales este año?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Le sumo algo a mi nota anterior.

En lugar de mandarte un checklist genérico, te armo una muestra corta de cuentas objetivo
para {{company}}: cuentas del perfil {{icp_corto}} que valdría la pena abrir proactivamente,
por qué hacen fit, y cómo las abordaría.

¿Te serviría?

Saludos,
Camilo

### Ángulo: antes de la primera contratación comercial (apertura A4)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Puedo estar equivocado, LinkedIn no siempre refleja la realidad, pero {{company}} parece
estar en la etapa donde el siguiente paso sería contratar ventas o desarrollo de negocio.

Antes de asumir esa nómina, conviene validar qué tipos de cuenta, compradores y mensajes
generan conversaciones de verdad.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, antes de que te comprometas con la contratación.

¿Crees que algo así sería útil antes de tu siguiente contratación comercial?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo mi nota.

Te puedo armar una muestra corta de cuentas objetivo para {{company}} en vez de solo
describir el sistema: cuentas del perfil {{icp_corto}}, por qué parecen fit, y el ángulo de
apertura que probaría antes de invertir en un prospector de tiempo completo.

¿Te serviría?

Saludos,
Camilo

---

## 4. Bucket 2–5: equipo comercial chico

### Ángulo: los reps cierran, pero no prospectan consistentemente (apertura A2)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{linea_observacion}} Y parece que el equipo comercial es compacto.

En ese modelo, lo difícil no suele ser cerrar cuando hay interés: es abrir consistentemente
las cuentas correctas.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, alrededor de los vendedores que ya tienes.

¿Crees que algo así ayudaría a {{company}} a llegar a sus metas comerciales este año?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Una idea más sobre mi nota anterior.

En vez de solo hablar del sistema, te mando una muestra corta de cuentas objetivo para
{{company}}: cuentas del perfil {{icp_corto}}, por qué hacen fit, y el ángulo con el que el
equipo podría abrir la conversación.

¿Te serviría?

Saludos,
Camilo

### Ángulo: el impuesto de prospectar a mano (apertura A3)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Pregunta rápida: ¿tus reps en {{company}} arman sus propias listas, investigan cuentas y
escriben sus propios follow-ups?

Cada hora de un vendedor en Excel es una hora que no está en una conversación con un
cliente potencial.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, para que los reps pasen más tiempo en conversaciones calificadas.

¿Crees que algo así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo lo de la carga de prospección.

Te mando una muestra corta de cuentas objetivo para {{company}} para aterrizar la idea:
cuentas del perfil {{icp_corto}} con fit fuerte, por qué cada una es relevante, y el ángulo
de apertura que le daría al equipo.

¿Te serviría?

Saludos,
Camilo

### Ángulo: de reactivo a proactivo (apertura A1)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Estuve viendo el sitio de {{company}}. {{linea_gancho}}

Me dio curiosidad: ¿hoy están sobre todo respondiendo a la demanda que llega, o tienen un
sistema para abrir proactivamente exactamente las cuentas que quieren?

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo: listas de cuentas, ángulos de compra, mensajes, secuencias y follow-up.

¿Crees que un sistema así haría a {{company}} más proactiva comercialmente?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Le sumo a mi última nota.

Te mando una muestra corta de cuentas objetivo para {{company}} en vez de explicar el
sistema en abstracto: cuentas del perfil {{icp_corto}} que valdría la pena abrir, por qué
hacen fit, y el mensaje con el que generaría la primera conversación.

¿Te serviría?

Saludos,
Camilo

---

## 5. Bucket 6–15: organización de ventas creciendo

### Ángulo: diseño de sistema y estandarización (apertura A4)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

El tamaño del equipo puede no verse desde fuera, así que corrígeme si me equivoco, pero
{{company}} parece tener un equipo comercial en crecimiento.

Cuando un equipo crece, el problema deja de ser esfuerzo y empieza a ser diseño de sistema:
selección de cuentas, calidad de datos, mensajes, ruteo y consistencia del follow-up.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, sin sumar headcount.

¿Crees que algo así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo por aquí.

En vez de solo describir un sistema estandarizado, te mando una muestra corta de cuentas
objetivo para {{company}}: cuentas del perfil {{icp_corto}}, la lógica de fit detrás de
cada una, y el ángulo de apertura que se podría estandarizar para todo el equipo.

¿Te serviría?

Saludos,
Camilo

### Ángulo: huecos de cobertura de pipeline (apertura A2)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{linea_observacion}} Y con un mercado así de amplio, la pregunta es si el equipo lo está
cubriendo completo o sobre todo trabajando las cuentas obvias, tibias o conocidas.

Segmentos valiosos se quedan intactos simplemente porque los reps van por donde el camino
es más fácil.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, para cubrir más mercado sin pedirle a cada rep que investigue y abra
cada cuenta a mano.

¿Crees que algo así ayudaría a {{company}} a llegar a sus metas comerciales este año?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Contexto sobre mi última nota.

Te mando una muestra corta de cuentas objetivo para {{company}} enfocada en cuentas o
subsegmentos del perfil {{icp_corto}} que el equipo quizá no está cubriendo hoy, con el
porqué de cada una y la tesis con la que abriría la conversación.

¿Te serviría?

Saludos,
Camilo

### Ángulo: fuga en el follow-up (apertura A5)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

En la mayoría de los equipos de ventas, las oportunidades no se pierden por falta de
interés: se pierden porque el siguiente toque no agrega ninguna razón nueva para seguir la
conversación.

¿En {{company}} hay un proceso definido de follow-up post-reply y post-propuesta, o depende
de cada rep?

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, con lógica de follow-up diseñada para mantener en movimiento las
oportunidades calificadas.

¿Crees que algo así ayudaría a {{company}} a convertir más del pipeline que ya generan?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo lo del follow-up.

Te mando una muestra corta de cuentas objetivo para {{company}}, cuentas del perfil
{{icp_corto}}, y le incluyo el ángulo de apertura más uno o dos ángulos de follow-up por
cuenta. Ahí se ve la diferencia entre una lista y un sistema de prospección.

¿Te serviría?

Saludos,
Camilo

---

## 6. Bucket 16–50: organización de ventas estructurada

### Ángulo: probar segmentos nuevos (apertura A2)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{linea_observacion}} Y a ese nivel de estructura, la pregunta ya no es si el equipo sabe
vender.

Es si hay segmentos nuevos que valdría la pena probar y que los reps internos no tienen
bandwidth para validar de punta a punta.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, para probar segmentos nuevos antes de asignarles capacidad interna.

¿Crees que algo así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo lo de probar segmentos.

Te mando una muestra corta de cuentas objetivo para {{company}} alrededor de un segmento
potencial adyacente a su perfil {{icp_corto}}: las cuentas, por qué el segmento puede valer
la pena, y el ángulo con el que abriría las primeras conversaciones.

¿Te serviría?

Saludos,
Camilo

### Ángulo: productividad por rep y abasto de pipeline (apertura A3)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Pregunta rápida: ¿el pipeline en {{company}} está parejo entre reps, o algunos
consistentemente tienen mejor cobertura de cuentas que otros?

A este tamaño el problema rara vez es headcount. Es si cada rep tiene suficientes
conversaciones calificadas para justificar su capacidad.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, generando más conversaciones calificadas alrededor del equipo que ya
existe.

¿Crees que algo así ayudaría a {{company}} a llegar a sus metas comerciales este año?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Contexto a mi última nota.

Te mando una muestra corta de cuentas objetivo para {{company}} diseñada como si estuviera
alimentando a uno de tus reps: la lógica de selección, por qué cada cuenta del perfil
{{icp_corto}} hace fit, y el ángulo que el rep usaría para abrir.

¿Te serviría?

Saludos,
Camilo

### Ángulo: control de calidad del outbound (apertura A5)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Cuando varios reps ejecutan outbound por su cuenta, la calidad se fragmenta rápido: listas,
mensajes, personalización y follow-up distintos por rep, y el mercado recibe una tesis
comercial borrosa.

¿En {{company}} el mensaje outbound está centralizado, o cada rep escribe su versión?

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, estandarizando la capa de prospección detrás del equipo.

¿Crees que algo así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo lo de la consistencia.

Te mando una muestra corta de cuentas objetivo para {{company}} construida alrededor de UNA
tesis consistente de selección y mensaje: cuentas del perfil {{icp_corto}}, por qué hacen
fit, y el ángulo exacto que estandarizaría para la prueba.

¿Te serviría?

Saludos,
Camilo

---

## 7. Bucket 50+: organización de ventas madura

### Ángulo: descubrir puntos ciegos (apertura A2)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{linea_observacion}} Y con una organización comercial de ese tamaño, esto no va de "más
outbound".

A esta escala la oportunidad suele estar en segmentos, triggers y patrones de cuenta que el
motion actual no está priorizando.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, dedicado a experimentos GTM enfocados: segmentos sub-trabajados, señales
de compra y patrones de cuenta.

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

Pregunta rápida: ¿{{company}} adapta el outbound por mercado o región, o el mensaje sigue
siendo bastante global?

Los equipos grandes pueden tener cobertura amplia sin resonancia local: cómo el comprador
de cada mercado describe el problema, evalúa la prueba y decide, cambia por país.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, localizando selección de cuentas, mensajes y follow-up para mercados
como México y LATAM.

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

Las oportunidades de mayor palanca casi nunca están en listas amplias: están en cuentas con
dolor de proveedor actual, señales de timing o triggers de expansión.

¿Las jugadas de desplazamiento de competidor son parte del motion outbound de {{company}},
o el equipo prospecta sobre todo por ICP y título?

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, alrededor de esas jugadas: research de cuentas, lógica de triggers,
mensajes, secuencias y follow-up.

¿Crees que algo así le generaría a {{company}} conversaciones de mayor intención?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo lo del desplazamiento competitivo.

Te mando una muestra corta de cuentas objetivo para {{company}} basada en empresas con una
señal plausible de cambio o timing, con el porqué de cada una y el ángulo que usaría sin
inventar afirmaciones que no puedo sostener.

¿Te serviría?

Saludos,
Camilo

---

## 8. A/B de Google Ads

Solo cuando la misma empresa tiene equipo de ventas visible Y señal confiable de Google Ads.
Mantener constante: audiencia, asunto, estilo de CTA, remitente, cadencia, oferta y la capa
de personalización (las líneas AI NO son la variable del test).

### Variante A: observación de Google Ads

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece invertir en Google Ads. Puedo estar equivocado, es lo que se ve desde
fuera.

El search de paga trae demanda, pero no siempre el tipo exacto de cuentas que ventas quiere
cerrar.

Un sistema de prospección funciona distinto: en vez de esperar a que la empresa correcta
busque, eliges primero las cuentas y construyes el research, los mensajes, las secuencias y
el follow-up alrededor de ellas. Te da el poder operativo de un equipo entero a una
fracción del costo.

¿Crees que un sistema así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo lo de paid search versus prospección.

En vez de explicar el sistema en teoría, te mando una muestra corta de cuentas objetivo
para {{company}}: cuentas del perfil {{icp_corto}} con mejor fit que el lead inbound o de
paga promedio, por qué cada una, y el ángulo que usaría.

¿Te serviría?

Saludos,
Camilo

### Variante B: observación por tamaño de equipo

Usar tal cual el ángulo "los reps cierran, pero no prospectan consistentemente" (sección 4),
misma personalización.

## 9. Setup y medición del test

- Solo empresas con AMBAS señales conocidas (Ads + tamaño de equipo).
- Split 50/50 aleatorio del mismo ICP.
- Constantes: asunto, remitente, cadencia, dominios, oferta del sample y nivel de
  personalización (no mezclar nivel gancho con nivel genérico entre variantes).
- Registrar por lead el nivel de fallback usado (gancho / observación / genérico): es un
  experimento gratis dentro del experimento.
- Medir: positive replies, solicitudes del sample, replies que confirman dolor, y juntas.
  No solo reply rate.
- NUNCA afirmar el conteo del equipo en el email (routing oculto). La línea de humildad
  existe justo para cuando la inferencia se asoma.
- No atacar Google Ads: la prospección es complementaria. Paid search captura demanda; el
  sistema elige y abre cuentas objetivo.

## 10. Resumen de routing

| Condición | Ángulo primario Email 1 | Apertura | Proof magnet |
|---|---|---|---|
| 0–1 ventas | Cuello de botella / referidos / pre-contratación | A2 / A3 / A4 | Sample que prueba el mercado antes de contratar |
| 2–5 ventas | Función de prospección alrededor del equipo | A2 / A3 / A1 | Cuentas {{icp_corto}} + fit + ángulo |
| 6–15 ventas | Estandarización / cobertura / follow-up | A4 / A2 / A5 | Sample que muestra proceso repetible |
| 16–50 ventas | Segmentos / abasto por rep / QA | A2 / A3 / A5 | Sample por segmento alimentando al equipo |
| 50+ ventas | Puntos ciegos / localización / desplazamiento | A2 / A3 / A5 | Experimento por señal o segmento |
| Ads + equipo elegible | Demanda de paga sin control de ICP | hedge en la señal | Cuentas de mejor fit que el lead de paga promedio |

## 11. Pipeline de datos que llena los slots AI

1. `site_crawls.clean_text` (ya existe para 1,375 dominios A de TI + contable).
2. Extracción LLM 2 capas (patrón gtm-classify-b2b): capa 1 masiva barata genera
   `linea_observacion`, `linea_gancho` (opcional), `icp_corto` + confianza; capa 2 verifica
   ciego contra el clean_text. Baja confianza = fallback genérico, nunca inventar.
3. `list_companies.sales_count` (departmentSizes de Ocean, ya cargado) → bucket.
4. Señal Ads: GetLeads `where_sql MONTHLY_GOOGLE_ADSPEND_ORG > 0` → flag por dominio.
5. Todo se upserta a Supabase junto a la empresa; Instantly recibe las columnas como custom
   fields (linea_observacion, linea_gancho, icp_corto, bucket, ads_flag, nivel_fallback).
