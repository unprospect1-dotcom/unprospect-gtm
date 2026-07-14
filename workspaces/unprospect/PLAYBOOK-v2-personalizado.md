# Unprospect Outbound Playbook v2: templates + observación del crawl + buckets por equipo de ventas + A/B Google Ads

> Versión es-MX del playbook original (PLAYBOOK-teamsize-googleads.md), fiel a su estructura.
> Registro: "tú" (estándar B2B moderno MX). Para despachos contables/legales considerar
> "usted" en la pasada de copy por campaña (/gtm-copy decide por universo).
> Regla de estilo: PROHIBIDOS los guiones largos (em dashes) en el copy. Comas, puntos o dos puntos.

## 0. La estructura NO cambia respecto al original

Todo Email 1 conserva los cuatro movimientos del playbook original:

1. **Observación de estructura comercial** (el routing del bucket: founder-led, equipo chico,
   equipo creciendo...). Aquí vive el "parece" y, cuando aplica, la línea de humildad.
   NUNCA se afirma el conteo.
2. **Dolor del bucket**: el dolor viene del TAMAÑO DEL EQUIPO, no del tipo de negocio.
   Es el mismo texto de dolor del original. Lo único que cambia: donde el original decía
   "for companies in {{industry}}", ahora va la clase de referencia personalizada:
   **"para una empresa que {{observacion}}"**.
3. **Value prop ancla** (fija): *"Construimos sistemas de prospección que te dan el poder
   operativo de un equipo entero a una fracción del costo"* + remate del bucket.
4. **CTA** aprobado.

La observación del crawl existe solo para que el prospecto sienta que hicimos el research
mínimo. No genera el argumento, no abre el correo: sustituye a "su industria" dentro de la
frase de dolor, y ahí se lee natural.

## 0.1 Slots AI (generados del clean_text de site_crawls)

| Slot | Qué es | Regla dura |
|---|---|---|
| `{{observacion}}` | Cláusula que completa "una empresa que ...". Empieza con verbo: "vende software a la medida a aseguradoras", "lleva contabilidad y auditoría de filiales extranjeras". Máx ~14 palabras, vocabulario del sitio. | Se AFIRMA, sin hedge: lo que hacen siempre debería estar claro si checamos su web. Nivel RICO (confianza alta): puede incluir un detalle específico (caso publicado, cliente nombrado). |
| `{{icp_corto}}` | Frase corta que nombra el tipo de cliente del prospecto, para el proof magnet del Email 2. Ej: "manufactureras del Bajío", "filiales extranjeras en México". | Se usa dentro de "cuentas del perfil {{icp_corto}}" (a prueba de género/número). |

**Cadena de fallback (nunca en blanco):** rica → estándar → genérica ("una empresa como la
tuya"). Registrar el nivel usado por lead para poder medir su efecto.

**Reglas para el prompt de generación:** sin guiones largos, sin comillas, sin "parece"
(las cláusulas afirman), cero adjetivos de halago, no inventar: evidencia ambigua = confianza
baja = fallback.

## 0.2 La observación de estructura comercial (línea 1) y la humildad

- Formas aprobadas (rotar entre ángulos): "parece ser / parece tener", pregunta directa
  ("¿tus reps arman sus propias listas?"), "no sé si esto es relevante, pero...".
- **La línea de humildad va SOLO aquí**, en la inferencia de estructura comercial (equipo,
  founder-led, señal Ads): eso viene de LinkedIn y puede estar mal. Equivocarse ahí con
  humildad genera replies de corrección, y una corrección es una conversación abierta.
- Frases aprobadas (rotar): "puedo estar equivocado", "LinkedIn no siempre refleja la
  realidad", "el tamaño del equipo puede no verse desde fuera", "si me equivoco, dime y no insisto".
- Máximo UNA línea de humildad por email. Nunca en el CTA. Nunca sobre lo que hacen.

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

### Ángulo: cuello de botella del fundador

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece seguir siendo bastante founder-led en lo comercial. Puedo estar
equivocado, LinkedIn no siempre refleja la realidad.

Para una empresa que {{observacion}}, el problema no suele ser saber vender: es que el
negocio nuevo depende demasiado de una persona abriendo puertas, dando seguimiento y
manteniendo vivas las oportunidades.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, sin contratarlo.

¿Crees que algo así le daría a {{company}} una ventaja competitiva?

Saludos,
Camilo

**Email 2** · Asunto: muestra de cuentas objetivo

Hola {{first_name}},

Retomo mi nota anterior.

En vez de explicarte el sistema en teoría, te mando una muestra corta de cuentas objetivo
para {{company}}: cuentas del perfil {{icp_corto}}, por qué cada una podría valer la pena,
y el ángulo que usaría para abrir la conversación.

¿Te serviría?

Saludos,
Camilo

### Ángulo: techo de referidos

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Un pensamiento rápido: si {{company}} es como la mayoría de las empresas founder-led, buena
parte del crecimiento viene de referidos, relaciones y la red existente.

Eso funciona bien, pero es difícil de pronosticar. Y para una empresa que {{observacion}},
ese techo se siente justo cuando hay metas que cumplir.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo: una capa proactiva de pipeline alrededor de lo que ya te llega, con
research de cuentas, mensajes, secuencias y follow-up.

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

### Ángulo: antes de la primera contratación comercial

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

No sé si esto es relevante, pero {{company}} parece estar en la etapa donde el siguiente
paso de crecimiento podría ser contratar ventas o desarrollo de negocio.

Para una empresa que {{observacion}}, suele ayudar validar qué tipos de cuenta, compradores
y mensajes generan conversaciones de verdad antes de hacer esa contratación.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, antes de que te comprometas con la nómina.

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

### Ángulo: los reps cierran, pero no prospectan consistentemente

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece tener un equipo comercial compacto.

Para una empresa que {{observacion}}, lo difícil no suele ser vender cuando hay interés: es
abrir consistentemente las cuentas correctas.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo: research, datos, mensajes, secuencias y follow-up alrededor de los
vendedores que ya tienes.

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

### Ángulo: el impuesto de prospectar a mano

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Pregunta rápida: ¿tus reps en {{company}} arman sus propias listas, investigan cuentas y
escriben sus propios follow-ups?

En una empresa que {{observacion}}, eso le quita una cantidad seria de tiempo a la venta
real.

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

### Ángulo: de reactivo a proactivo

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Me da curiosidad: ¿{{company}} está sobre todo respondiendo a la demanda que llega, o
tienen un sistema para abrir proactivamente exactamente las cuentas que quieren?

Para una empresa que {{observacion}}, la diferencia no suele ser más actividad: es tener
una forma repetible de identificar y abrir cuentas de mejor fit.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo: convierten mercados objetivo en listas de cuentas, ángulos de compra,
mensajes, secuencias y follow-up.

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

### Ángulo: diseño de sistema y estandarización

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece tener un equipo de ventas en crecimiento. El tamaño puede no verse desde
fuera, así que corrígeme si me equivoco.

Cuando crece el equipo de una empresa que {{observacion}}, el problema deja de ser esfuerzo
y empieza a ser diseño de sistema: selección de cuentas, calidad de datos, mensajes, ruteo
y consistencia del follow-up.

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

### Ángulo: huecos de cobertura de pipeline

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Pregunta rápida: ¿sientes que el equipo de {{company}} está cubriendo el mercado completo,
o sobre todo trabajando las cuentas que ya son obvias, tibias o conocidas?

En el mercado de una empresa que {{observacion}}, hay segmentos valiosos que se quedan
intactos simplemente porque los reps van por donde el camino es más fácil.

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

### Ángulo: fuga en el follow-up

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Me da curiosidad: ¿en {{company}} hay un proceso definido de follow-up post-reply y
post-propuesta, o eso depende de cada rep?

Para una empresa que {{observacion}}, las oportunidades rara vez desaparecen por falta de
interés: desaparecen porque el siguiente toque no agrega ninguna razón nueva para seguir la
conversación.

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

### Ángulo: probar segmentos nuevos

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece tener un equipo comercial ya estructurado.

Para una empresa que {{observacion}}, la pregunta en esta etapa no suele ser si el equipo
sabe vender: es si hay segmentos nuevos que valdría la pena probar y que los reps internos
no tienen bandwidth para validar de punta a punta.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, para probar segmentos nuevos con research, mensajes, secuencias y
follow-up antes de asignarles capacidad interna.

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

### Ángulo: productividad por rep y abasto de pipeline

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Pregunta rápida: ¿el pipeline en {{company}} está parejo entre reps, o algunos
consistentemente tienen mejor cobertura de cuentas que otros?

En una empresa que {{observacion}}, el tema a este tamaño rara vez es headcount: es si cada
rep tiene suficientes conversaciones calificadas para justificar su capacidad.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, generando más conversaciones calificadas alrededor del equipo que ya
existe, en vez de resolver todo con más contrataciones.

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

### Ángulo: control de calidad del outbound

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Me da curiosidad: ¿el mensaje outbound está centralizado en {{company}}, o cada rep escribe
su propia versión?

En una empresa que {{observacion}}, la calidad del outbound se fragmenta rápido cuando
listas, mensajes, personalización y follow-up varían por rep, y el mercado recibe una tesis
comercial borrosa.

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

### Ángulo: descubrir puntos ciegos

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece tener una organización comercial madura.

Para una empresa que {{observacion}}, la oportunidad a esta escala no suele ser simplemente
más outbound: es encontrar segmentos, triggers y patrones de cuenta que el motion actual no
está priorizando.

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

### Ángulo: penetración localizada

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Pregunta rápida: ¿{{company}} adapta el outbound por mercado o región, o el mensaje sigue
siendo bastante global?

Para una empresa que {{observacion}}, un equipo grande puede tener cobertura amplia sin
resonancia local: cómo el comprador describe el problema, evalúa la prueba y decide cambia
por mercado.

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

### Ángulo: desplazamiento competitivo

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

Me da curiosidad: ¿las jugadas de desplazamiento de competidor son parte del motion
outbound de {{company}}, o el equipo prospecta sobre todo por ICP y título?

Para una empresa que {{observacion}}, las oportunidades de mayor palanca suelen estar en
cuentas con dolor de proveedor actual, señales de timing o triggers de expansión, no en
listas amplias.

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
de personalización (la observación NO es la variable del test).

### Variante A: observación de Google Ads

**Email 1** · Asunto: sistema de prospección

Hola {{first_name}},

{{company}} parece invertir en Google Ads. Puedo estar equivocado, es lo que se ve desde
fuera.

Para una empresa que {{observacion}}, el search de paga trae demanda, pero no siempre el
tipo exacto de cuentas que ventas quiere cerrar.

Ahí es donde un sistema de prospección funciona distinto: en vez de esperar a que la
empresa correcta busque, eliges primero las cuentas y construyes el research, los mensajes,
las secuencias y el follow-up alrededor de ellas. El poder operativo de un equipo entero a
una fracción del costo.

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
  personalización (no mezclar nivel rico con genérico entre variantes).
- Registrar por lead el nivel de fallback usado (rica / estándar / genérica): es un
  experimento gratis dentro del experimento.
- Medir: positive replies, solicitudes del sample, replies que confirman dolor, y juntas.
  No solo reply rate.
- NUNCA afirmar el conteo del equipo en el email (routing oculto). La línea de humildad
  existe justo para cuando la inferencia se asoma.
- No atacar Google Ads: la prospección es complementaria. Paid search captura demanda; el
  sistema elige y abre cuentas objetivo.

## 10. Resumen de routing

| Condición | Ángulo primario Email 1 | Proof magnet |
|---|---|---|
| 0–1 ventas | Cuello de botella / referidos / pre-contratación | Sample que prueba el mercado antes de contratar |
| 2–5 ventas | Función de prospección alrededor del equipo | Cuentas {{icp_corto}} + fit + ángulo |
| 6–15 ventas | Estandarización / cobertura / follow-up | Sample que muestra proceso repetible |
| 16–50 ventas | Segmentos / abasto por rep / QA | Sample por segmento alimentando al equipo |
| 50+ ventas | Puntos ciegos / localización / desplazamiento | Experimento por señal o segmento |
| Ads + equipo elegible | Demanda de paga sin control de ICP | Cuentas de mejor fit que el lead de paga promedio |

## 11. Pipeline de datos que llena los slots AI

1. `site_crawls.clean_text` (ya existe para 1,375 dominios A de TI + contable).
2. Extracción LLM 2 capas (patrón gtm-classify-b2b): capa 1 masiva barata genera
   `observacion` (cláusula que completa "una empresa que ...", empieza con verbo) e
   `icp_corto` + confianza; capa 2 verifica ciego contra el clean_text. Baja confianza =
   fallback genérico, nunca inventar.
3. `list_companies.sales_count` (departmentSizes de Ocean, ya cargado) → bucket.
4. Señal Ads: GetLeads `where_sql MONTHLY_GOOGLE_ADSPEND_ORG > 0` → flag por dominio.
5. Todo se upserta a Supabase junto a la empresa; Instantly recibe las columnas como custom
   fields (observacion, icp_corto, bucket, ads_flag, nivel_fallback).
