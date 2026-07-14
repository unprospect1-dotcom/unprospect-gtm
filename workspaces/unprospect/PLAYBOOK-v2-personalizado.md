# Unprospect Outbound Playbook v2: templates + líneas AI del crawl + buckets por equipo de ventas + A/B Google Ads

> Reescritura del playbook original (PLAYBOOK-teamsize-googleads.md). Idioma base: es-MX.
> Registro: "tú" (estándar B2B moderno MX). Para despachos contables/legales considerar
> "usted" en la pasada de copy por campaña (/gtm-copy decide por universo).
> Regla de estilo: PROHIBIDOS los guiones largos (em dashes) en el copy. Comas, puntos o dos puntos.

## 0. Arquitectura: template fijo + líneas AI ancladas al dolor

Cada mensaje es un TEMPLATE fijo. Lo único que cambia por lead son los slots generados por
AI a partir del crawl del sitio (`site_crawls.clean_text`).

**La regla central del anclaje:** la observación NUNCA es la primera línea ni una oración
suelta. Siempre va fusionada con el dolor que inferimos de ella, en una sola oración:
*vimos X, y por eso creemos que les pasa Y*. La observación existe para que el prospecto
sienta que hicimos el research mínimo, no para presumirlo. Por eso va subordinada al
argumento, nunca de adorno.

| Slot AI | Qué es | Regla dura |
|---|---|---|
| `{{observacion}}` | Cláusula en minúscula que completa "vi en su sitio que ...". Ej: "se especializan en litigio fiscal y precios de transferencia para grupos con operaciones en EUA". | Se AFIRMA, sin hedge: lo que hacen siempre debería estar claro si checamos su web. La AI usa el sustantivo natural del negocio (despacho, agencia, taller, empresa). |
| `{{gancho}}` | Versión premium: detalle específico verificable que completa "me fijé en ...". Ej: "el caso que publicaron con una cadena de farmacias". | Solo con confianza alta. Sustituye a `{{observacion}}` en el conector, no se suman. |
| `{{icp_corto}}` | Frase corta que nombra el tipo de cliente del prospecto, para el proof magnet. Ej: "manufactureras del Bajío", "filiales extranjeras en México". | Se usa dentro de "cuentas del perfil {{icp_corto}}" (construcción a prueba de género/número). |

**Cadena de fallback (nunca en blanco):**
1. `{{gancho}}` disponible → conector con gancho.
2. Si no → conector con `{{observacion}}`.
3. Extracción no confiable → la oración de anclaje usa el contexto genérico del ángulo
   (sin línea AI). Registrar el nivel usado por lead.

**Reglas para el prompt de generación:**
- Cláusula de máx ~14 palabras, vocabulario del sitio, cero adjetivos de halago.
- Sin guiones largos, sin comillas, sin "parece": las cláusulas AI afirman.
- Debe leerse natural dentro del marco "vi en su sitio que ..." / "me fijé en ...".
- Si la evidencia es ambigua, no inventar: confianza baja y fallback.

## 0.1 Estructura de todo Email 1 (cuatro movimientos)

1. **Apertura** (pregunta, hipótesis o contexto de mercado; rotar, ver 0.3).
2. **Anclaje**: conector + observación + dolor inferido, EN UNA ORACIÓN (ver 0.2).
3. **Value prop ancla** (fija): *"Construimos sistemas de prospección que te dan el poder
   operativo de un equipo entero a una fracción del costo"* + remate del bucket.
4. **CTA** aprobado.

## 0.2 Conectores de anclaje (rotar para que el research no suene a template)

| # | Conector | Molde |
|---|---|---|
| C1 | Lo pregunto porque | "Lo pregunto porque vi en su sitio que {{observacion}}, y [dolor inferido del bucket]." |
| C2 | Lo digo porque | "Lo digo porque me fijé que {{observacion}}. Cuando ese es el negocio, [dolor inferido]." |
| C3 | Vi que | "Vi que {{observacion}}, y en ese modelo [dolor inferido]." (siempre después de la apertura, nunca como línea 1) |
| C-gancho | Me fijé en | "Lo pregunto porque me fijé en {{gancho}}, y ese tipo de trabajo [dolor inferido]." |

## 0.3 Aperturas (línea 1, sin observación)

| # | Tipo | Ejemplo |
|---|---|---|
| O1 | Pregunta directa | "¿La venta nueva de {{company}} todavía pasa por ti?" |
| O2 | Hipótesis con "parece" (+ humildad si aplica) | "Puedo estar equivocado, LinkedIn no siempre refleja la realidad, pero {{company}} parece operar con un equipo comercial chico." |
| O3 | Contexto de mercado | "Las oportunidades de mayor palanca casi nunca están en listas amplias." |

Regla: dentro de un mismo bucket, cada ángulo abre distinto.

## 0.4 Dónde va la humildad (y dónde nunca)

- **Solo en la inferencia de estructura comercial**: tamaño del equipo, dependencia del
  fundador, señal de Ads. Eso viene de LinkedIn o de inferencia y puede estar mal.
  Equivocarse ahí con humildad genera replies de corrección, y una corrección es una
  conversación abierta.
- **Nunca en lo que hacen**: eso viene de su web y se afirma.
- Máximo UNA línea de humildad por email. Nunca en el CTA.
- Frases aprobadas (rotar): "puedo estar equivocado", "LinkedIn no siempre refleja la
  realidad", "el tamaño del equipo puede no verse desde fuera", "si me equivoco, dime y no insisto".

## 1. Posicionamiento y lógica de secuencia

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

### Ángulo: cuello de botella del fundador (O1 + C1)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

¿La venta nueva de {{company}} todavía pasa por ti?

Lo pregunto porque vi en su sitio que {{observacion}}, y en ese tipo de negocio abrir
puertas, dar seguimiento y empujar oportunidades suele recaer en una sola persona: el dueño.

Eso funciona, hasta que el crecimiento depende del tiempo de esa persona.

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

### Ángulo: techo de referidos (O2 + C3)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Puedo estar equivocado, pero {{company}} parece crecer sobre todo por referidos y relaciones.

Vi que {{observacion}}, y ese tipo de trabajo se recomienda solo. El problema no es la
calidad de esos clientes: es que no se pueden pronosticar.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo: una capa proactiva de pipeline alrededor de lo que ya te llega.

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

### Ángulo: antes de la primera contratación comercial (O3 + C2)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Hay una etapa donde el siguiente paso lógico parece ser contratar al primer vendedor. Y es
la contratación más cara de equivocarse.

Lo digo porque me fijé que {{observacion}}. Cuando ese es el negocio, conviene validar qué
tipos de cuenta, compradores y mensajes generan conversaciones de verdad antes de asumir la
nómina.

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

### Ángulo: los reps cierran, pero no prospectan consistentemente (O2 + C3)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Desde fuera parece que {{company}} opera con un equipo comercial compacto. Si es así, esto
te va a sonar.

Vi que {{observacion}}, y en ese negocio lo difícil no suele ser cerrar cuando hay interés:
es abrir consistentemente las cuentas correctas.

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

### Ángulo: el impuesto de prospectar a mano (O1 + C1)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

¿Tus reps en {{company}} arman sus propias listas, investigan cuentas y escriben sus
propios follow-ups?

Lo pregunto porque vi en su sitio que {{observacion}}, y en ventas de ese tipo cada hora
que un vendedor pasa en Excel es una hora fuera de una conversación con un cliente potencial.

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

### Ángulo: de reactivo a proactivo (O1 + C-gancho)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

¿{{company}} está sobre todo respondiendo a la demanda que llega, o abriendo proactivamente
las cuentas que quiere?

Lo pregunto porque me fijé en {{gancho}}, y ese tipo de trabajo trae clientes por
reputación. Lo que la reputación no hace es elegir a qué cuentas llega.

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

### Ángulo: diseño de sistema y estandarización (O2 + C3)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

El tamaño del equipo puede no verse desde fuera, así que corrígeme si me equivoco, pero
{{company}} parece tener un equipo comercial en crecimiento.

Vi que {{observacion}}, y cuando un equipo que vende eso crece, el problema deja de ser
esfuerzo y empieza a ser diseño de sistema: selección de cuentas, calidad de datos,
mensajes, ruteo y consistencia del follow-up.

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

### Ángulo: huecos de cobertura de pipeline (O1 + C1)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

¿Sientes que el equipo de {{company}} está cubriendo el mercado completo, o sobre todo
trabajando las cuentas obvias, tibias o conocidas?

Lo pregunto porque vi en su sitio que {{observacion}}, y ese mercado es más ancho de lo que
un equipo alcanza a cubrir investigando y abriendo cuentas a mano.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, para cubrir los segmentos que se quedan intactos.

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

### Ángulo: fuga en el follow-up (O1 + C2)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

¿En {{company}} hay un proceso definido de follow-up post-reply y post-propuesta, o depende
de cada rep?

Lo digo porque me fijé que {{observacion}}. Cuando ese es el negocio, las oportunidades
rara vez mueren por falta de interés: mueren porque el siguiente toque no agrega ninguna
razón nueva para seguir la conversación.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, con lógica de follow-up que mantiene en movimiento las oportunidades
calificadas.

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

### Ángulo: probar segmentos nuevos (O2 + C3)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece tener una operación comercial ya estructurada. A ese nivel la pregunta
deja de ser si el equipo sabe vender.

Vi que {{observacion}}, y alrededor de ese negocio suele haber segmentos adyacentes que
valdría la pena probar, pero que los reps internos no tienen bandwidth para validar de
punta a punta.

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

### Ángulo: productividad por rep y abasto de pipeline (O1 + C1)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

¿El pipeline en {{company}} está parejo entre reps, o algunos consistentemente tienen mejor
cobertura de cuentas que otros?

Lo pregunto porque vi en su sitio que {{observacion}}, y en esa venta el problema rara vez
es headcount: es si cada rep tiene suficientes conversaciones calificadas para justificar
su capacidad.

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

### Ángulo: control de calidad del outbound (O3 + C2)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Cuando varios reps ejecutan outbound por su cuenta, la calidad se fragmenta rápido: listas,
mensajes y follow-up distintos por rep, y el mercado recibe una tesis comercial borrosa.

Lo digo porque me fijé que {{observacion}}. Cuando ese es el negocio, la diferencia entre
una tesis filosa y veinte versiones sueltas se nota en el pipeline.

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

### Ángulo: descubrir puntos ciegos (O2 + C3)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece tener una organización comercial madura, así que esto no va de "más
outbound".

Vi que {{observacion}}, y a esa escala la oportunidad suele estar en segmentos, triggers y
patrones de cuenta que el motion actual no está priorizando.

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

### Ángulo: penetración localizada (O1 + C1)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

¿{{company}} adapta el outbound por mercado o región, o el mensaje sigue siendo bastante
global?

Lo pregunto porque vi en su sitio que {{observacion}}, y cómo el comprador de cada mercado
describe ese problema, evalúa la prueba y decide, cambia por país.

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

### Ángulo: desplazamiento competitivo (O3 + C2)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Las oportunidades de mayor palanca casi nunca están en listas amplias: están en cuentas con
dolor de proveedor actual, señales de timing o triggers de expansión.

Lo digo porque me fijé que {{observacion}}. Cuando ese es el negocio, prospectar solo por
ICP y título deja fuera justo las cuentas con mayor intención.

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

### Variante A: observación de Google Ads (O2 sobre la señal + C3)

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece invertir en Google Ads. Puedo estar equivocado, es lo que se ve desde
fuera.

Si es así, seguro llega demanda. Vi que {{observacion}}, y ese perfil de cliente rara vez
llega buscando en Google: se elige y se abre.

Un sistema de prospección hace exactamente eso: eliges primero las cuentas y construyes el
research, los mensajes, las secuencias y el follow-up alrededor de ellas. Te da el poder
operativo de un equipo entero a una fracción del costo.

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

| Condición | Ángulos Email 1 (apertura + conector) | Proof magnet |
|---|---|---|
| 0–1 ventas | O1+C1 / O2+C3 / O3+C2 | Sample que prueba el mercado antes de contratar |
| 2–5 ventas | O2+C3 / O1+C1 / O1+C-gancho | Cuentas {{icp_corto}} + fit + ángulo |
| 6–15 ventas | O2+C3 / O1+C1 / O1+C2 | Sample que muestra proceso repetible |
| 16–50 ventas | O2+C3 / O1+C1 / O3+C2 | Sample por segmento alimentando al equipo |
| 50+ ventas | O2+C3 / O1+C1 / O3+C2 | Experimento por señal o segmento |
| Ads + equipo elegible | O2(señal)+C3 | Cuentas de mejor fit que el lead de paga promedio |

## 11. Pipeline de datos que llena los slots AI

1. `site_crawls.clean_text` (ya existe para 1,375 dominios A de TI + contable).
2. Extracción LLM 2 capas (patrón gtm-classify-b2b): capa 1 masiva barata genera
   `observacion` (cláusula que completa "vi en su sitio que ..."), `gancho` (opcional,
   completa "me fijé en ..."), `icp_corto` + confianza; capa 2 verifica ciego contra el
   clean_text. Baja confianza = fallback genérico, nunca inventar.
3. `list_companies.sales_count` (departmentSizes de Ocean, ya cargado) → bucket.
4. Señal Ads: GetLeads `where_sql MONTHLY_GOOGLE_ADSPEND_ORG > 0` → flag por dominio.
5. Todo se upserta a Supabase junto a la empresa; Instantly recibe las columnas como custom
   fields (observacion, gancho, icp_corto, bucket, ads_flag, nivel_fallback).
