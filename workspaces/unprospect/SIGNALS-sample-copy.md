# Muestra de copy — capa de señales de contratación (para iterar)

> 2026-07-15. Postings reales (LinkedIn Jobs MX, última semana, vía Apify).
> Principio: la observación NO es "estás contratando un X" (eso está hueco). La observación
> es el **empuje comercial** que la vacante revela; el **dolor** va ligado a lo que Unprospect
> hace. La vacante es la EVIDENCIA fresca, no el titular. Copy **templated** (esqueleto fijo,
> variable = el dolor/actividad extraído), para medir A/B como en el PLAYBOOK.

## El calificador (lo que extrae de cada posting)

| Posting | Empresa | emp | fit | bucket | actividad_extraida (el slot variable) |
|---|---|---|---|---|---|
| Head de Desarrollo Comercial | Coketo Coco | 2 | ALTO | 0-1 | construir el área comercial desde cero para abrir convenios HORECA y replicar plaza por plaza |
| Gerente de Desarrollo de Negocio | T-ASSIS-T | 9 | ALTO | 0-1/2-5 | abrir cuentas corporativas B2B de banca, seguros y alianzas |
| Market Development Manager | Bioelements | 51 | ALTO | 6-15 | abrir mercado MX de packaging sostenible en retail/consumo masivo, ciclo consultivo largo |
| Gerente Comercial Bajío | Cargo Group | 116 | ALTO | 6-15/16-50 | acelerar cuentas corporativas de transporte internacional con equipo inside+field |
| BDM | ATFX Latam | 56 | MEDIO | 6-15 | desarrollar cartera de traders e Introducing Brokers (canal financiero) |
| BD Manager | Blue Box Talent | 32 | EXCLUIR | — | reclutadora: la empresa real está oculta (target equivocado) |
| New Business Manager | Kantar | 24,991 | NO | — | enterprise: no compra outbound boutique |

**Reglas del calificador que salen de esta muestra:**
- Excluir **reclutadoras/bolsas** (Blue Box, Latino Legends, Lato Jobs, Delta Top Talent): la
  empresa que contrata NO es la que compraría; el dominio es de la agencia.
- Downweight **enterprise** (BBVA, PepsiCo, Mastercard, ABB, Orange, Linde, WTW): equipo interno,
  no compran DFY outbound. Corte por `companyEmployeesCount` alto + marca global.
- fit ALTO = el puesto vive de **abrir cuentas nuevas / prospectar / desarrollar mercado** en B2B.

## El template (esqueleto fijo, 4 movimientos del PLAYBOOK)

```
Hola {{first_name}},

[1 OBSERVACIÓN = empuje comercial, del posting, SIN decir "vi que contratan"]
{{company}} está {{actividad_extraida}}.

[2 DOLOR ligado al bucket + a lo que hacemos]
{{dolor_del_bucket_ligado_a_la_actividad}}

[3 VALUE PROP ANCLA — fija]
Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo: {{remate_del_bucket}}.

[4 CTA aprobado]
¿Crees que algo así {{resultado}}?

Saludos,
Camilo
```
La única variable de contenido es {{actividad_extraida}} + {{dolor}} (del posting). Todo lo
demás es constante → se puede correr A/B limpio (variable = hipótesis de dolor, no cosméticos).

---

## Ejemplos completos (mismo template, 3 buckets)

### A · Coketo Coco — bucket 0-1 (construir área desde cero)

Hola {{first_name}},

Coketo está en el momento de construir el área comercial desde cero para abrir convenios con
hoteles, restaurantes y bares, y replicar el modelo plaza por plaza.

En esa etapa el reto no suele ser cerrar: es que llegar de forma consistente a los grupos
HORECA correctos, dar con el decisor y sostener el seguimiento se vuelve un sistema completo
que hoy recae en una sola persona.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo: research de cuentas, listas, mensajes, secuencias y follow-up alrededor de
tu área comercial.

¿Crees que algo así ayudaría a Coketo a abrir convenios más rápido en cada plaza nueva?

Saludos,
Camilo

### B · Bioelements — bucket 6-15 (venta consultiva de ciclo largo)

Hola {{first_name}},

Bioelements está abriendo mercado en México para packaging sostenible con cuentas de retail,
consumo masivo y e-commerce, en ciclos de venta consultiva largos.

En ese tipo de venta el pipeline se sostiene con research y follow-up constantes, y ahí es
donde una persona abriendo mercado se satura en la parte de prospectar antes de llegar a las
conversaciones que de verdad avanzan.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo: cuentas, mensajes, secuencias y follow-up que alimentan al comercial en
vez de restarle tiempo.

¿Crees que algo así ayudaría a Bioelements a sostener un pipeline más robusto en México?

Saludos,
Camilo

### C · Cargo Group — bucket 6-15/16-50 (equipo ya operando)

Hola {{first_name}},

Cargo Group está acelerando la adquisición de cuentas corporativas de transporte internacional
en el Bajío, con un equipo de inside y field sales detrás.

Cuando ya hay equipo, el problema deja de ser esfuerzo y pasa a ser sistema: qué cuentas
priorizar, con qué datos, con qué mensaje y con qué follow-up consistente entre cada rep.

Construimos sistemas de prospección que te dan el poder operativo de un equipo entero a una
fracción del costo, sin sumar headcount.

¿Crees que algo así le daría a Cargo Group una ventaja para abrir más cuentas en rutas
estratégicas?

Saludos,
Camilo

---

## Preguntas para iterar el copy (esto es lo que "trabajamos juntos")
1. ¿La observación (línea 1) debe quedar 100% implícita (como aquí) o SÍ nombrar la contratación
   pero reencuadrada al dolor ("estás sumando capacidad comercial para X, y en esa etapa...")?
2. Registro: "tú" (como aquí) o "usted" para ciertos sectores (banca/corporativo)?
3. ¿El value prop ancla queda fijo palabra por palabra, o lo dejamos rotar por bucket?
4. ¿CTA de una sola pregunta (como aquí) o cerramos con la oferta de la muestra de cuentas (Email 2 del playbook)?
5. DM target por caso: Coketo/T-ASSIS-T → Dirección General/founder; Bioelements/Cargo → Director Comercial/VP Ventas. ¿Confirmas?
