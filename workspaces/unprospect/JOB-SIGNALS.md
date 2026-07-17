# Señales de contratación — flujo operativo v1

Este documento define el flujo que estamos construyendo juntos. No usa el copy anterior de
Claude y no contiene plantillas de correo. El copy será un módulo nuevo, evaluado por separado.

## Objetivo

Cada semana encontrar empresas basadas en Latinoamérica que publicaron vacantes relacionadas
con prospección, apertura de cuentas, generación de pipeline o desarrollo de mercado. La empresa
puede querer prospectar en su propio país, en LATAM o internacionalmente. Guardar la evidencia,
determinar si Unprospect realmente puede ayudar, encontrar al buyer responsable y preparar la
oportunidad para email o LinkedIn.

## Flujo

1. **Harvest:** en la fase actual, Apify consulta LinkedIn Jobs con los términos de
   `signals-keywords.txt`, ubicación `Mexico` y últimos siete días. El mercado de clientes sigue
   siendo LATAM; México es solamente el foco de búsqueda de esta corrida.
2. **Dedupe:** una vacante se identifica por `source_job_id`. Volver a ejecutar la semana no
   crea duplicados.
3. **Conservación:** descripción completa, payload original, logo, URL, empresa y fecha quedan
   en Supabase.
4. **Prefiltro barato:** reglas simples ordenan la cola en prioridad alta, media, baja o revisión.
   No deciden el fit y nunca borran una vacante.
5. **Análisis:** un humano o LLM separa la fuerza de la señal, el fit de la cuenta, el país base
   de la empresa, el alcance de prospección y la confianza en el empleador. Después devuelve la
   acción de campaña, el problema y citas exactas. Una decisión positiva sin evidencia textual
   es rechazada por el importador.
6. **Buyer:** primero se buscan contactos ya existentes en Supabase. Empresa pequeña apunta a
   founder/CEO; empresa mayor a liderazgo comercial. Se respetan `do_not_contact` y 90 días de
   espera desde el último contacto.
7. **Canal:** email solamente cuando existe email verificado. Si no existe, se prepara para
   LinkedIn. No se inventa un email.
8. **Copy:** queda en `not_started` hasta que creemos y aprobemos juntos el módulo nuevo.
9. **Envío:** desactivado. Más adelante exigirá copy aprobado, proveedor configurado y gate
   humano antes del primer envío.

## Cómo se reduce contexto sin perder información

- Supabase conserva siempre la descripción completa y el JSON original.
- El LLM recibe un paquete de máximo 6,000 caracteres con las frases donde aparecen señales
  relevantes, más hash, tamaño del original y URL.
- Si el paquete no basta, se consulta el original; no se rellena con suposiciones.
- Las citas importadas deben existir literalmente dentro de la descripción guardada.

Así el contexto corto sirve para velocidad y costo, mientras el original sigue disponible para
resolver casos ambiguos.

## Estados principales

| Estado | Significado |
|---|---|
| `ready_for_analysis` | Se conservó y necesita decisión de fit |
| `ready_for_contact` | Fit positivo; necesita buyer |
| `ready_for_copy` | Buyer y canal encontrados; copy todavía vacío |
| `draft_ready` | Los dos mensajes/brief existen, pero no están aprobados |
| `approved` | Revisión humana completada |
| `sent` | El proveedor confirmó el envío |
| `not_fit` | Revisado y descartado, conservando la evidencia |

## Dimensiones de calificación

- `signal_fit`: si la vacante demuestra outbound, apertura de cuentas o construcción de pipeline.
- `account_fit`: si la empresa y su situación encajan con el servicio de Unprospect.
- `company_region_fit`: si la empresa está basada en LATAM. La ubicación de la vacante no basta.
- `prospecting_scope`: nacional, LATAM regional, internacional o mixto.
- `employer_confidence`: si conocemos al empleador real o es una vacante de cliente oculto.
- `campaign_action`: contactar, revisar, mantener en espera o excluir.

Ejemplo: una empresa colombiana que contrata un BDR para vender en Estados Unidos puede tener
`signal_fit=high`, `company_region_fit=latam` y `prospecting_scope=international`.

## Presupuesto y activación

- Actor: `curious_coder/linkedin-jobs-scraper`.
- Precio observado 2026-07-16: USD 1 por 1,000 resultados.
- Límite inicial: 500 resultados por semana; máximo estimado USD 0.50 por corrida.
- Hard stop configurado: USD 1.00 por corrida.
- El workflow no corre hasta que la variable de GitHub `JOB_SIGNALS_ENABLED` sea `true`.
- Enriquecimiento pagado y envío siguen desactivados.

## Comandos

```powershell
# Ver URLs, volumen y costo; no hace llamadas externas
python scripts/job_signals.py plan --max-results 25

# Normalizar una muestra local
python scripts/job_signals.py normalize --input muestra.json --output normalizada.json

# Corrida real y persistencia (gasta Apify; requiere acción explícita)
python scripts/job_signals.py harvest --live --persist --max-results 500

# Paquetes compactos para análisis
python scripts/job_signals.py export-review --output work/job-signals-review.json

# Bandeja humana: una fila por empresa, brief extractivo y fuente auditable
python scripts/job_signals.py export-company-review `
  --run-id <job_signal_runs.id> `
  --output work/company-review.json `
  --csv-output work/company-review.csv

# Importar decisiones verificando que las citas existan
python scripts/job_signals.py import-analysis --input decisiones.json --analysis-version <version>

# Buscar buyers existentes sin gastar créditos
python scripts/job_signals.py match-contacts
```

## Bandeja repetible de revisión humana

`export-company-review` es el gate anterior al análisis de dolor y al copy. Toma únicamente
vacantes con prioridad alta que no contienen señales negativas del prefiltro y las consolida por
nombre de empresa. No borra las publicaciones duplicadas: conserva sus IDs, URLs, hashes y
descripciones completas como fuente.

Cada fila devuelve:

- descripción de la empresa publicada por la fuente;
- roles, ubicaciones y mercados mencionados;
- un brief extractivo compuesto solamente por frases presentes en las descripciones;
- evidencia textual sobre el tipo de cliente al que parece dirigirse el rol;
- alertas de revisión para USA, país de fuente no LATAM, reclutadores, empleador oculto,
  falta de dominio y múltiples vacantes;
- columnas manuales separadas para sede LATAM, B2B, empleador real y fit con Unprospect.

Las alertas son preguntas de control, no decisiones automáticas. El país de la fuente no se
convierte en HQ. Una vez que el usuario aprueba empresas en esta bandeja, solamente esas filas
deben pasar al extractor de dolor y después al módulo de copy.

La corrida México del 2026-07-16 produjo 160 vacantes limpias consolidadas en 134 empresas.

## Lo que falta construir juntos

1. Rúbrica y muestra dorada del analizador de fit.
2. Nuevo sistema de copy: email 1, bridge, email 2/lead magnet y brief de LinkedIn.
3. Proveedor de envío con API y configuración de mailbox/firma.
4. Prueba controlada de calidad antes de activar el cron.

## Aprendizajes de la muestra 2026-07-16

Muestra aprobada: 25 vacantes, costo real USD 0.025. Resultado de la primera revisión:
3 `high`, 19 `no_fit`, 3 `excluded`. Las tres positivas permanecen en `qualified` y requieren
aprobación humana; ninguna avanzó a contactos, copy o envío.

Reglas incorporadas y corregidas:

- Colombia u otro país de residencia de la vacante no descalifica una señal. Unprospect sirve a
  empresas de LATAM y puede operar prospección nacional o internacional. Lo que se verifica por
  separado es el país base de la empresa.
- La primera muestra estuvo sesgada: el límite global de 25 se llenó con `SDR`, `BDR`,
  `sales development representative` y `business development representative`. No alcanzó a
  probar la taxonomía completa en español y portugués.
- “Our client is looking...” indica empleador oculto: se conserva, pero baja de prioridad.
- El número de empleados del posting puede representar una subsidiaria. La descripción de
  Arrow Components decía que el grupo tiene 22,000 empleados; el texto pesa más que el `129`
  estructurado para decidir account fit.
- `pipeline` por sí solo genera demasiado ruido. Expansión, renewals, upsell, cross-sell y
  clientes existentes no equivalen a nueva adquisición outbound.
- Construcción de bases, market mapping, cold calling, prospección telefónica y cold email son
  señales directas aunque el título sea genérico como “Sales”.
- Múltiples vacantes de una misma empresa deben consolidarse a nivel dominio antes de buscar
  contacto o preparar una campaña.
- Un fit positivo con `needs_human_review=true` queda en `qualified`; no puede avanzar a
  enriquecimiento ni copy hasta aprobación humana.

Bloqueo antes de activar GitHub Actions: la variable global `SUPABASE_SERVICE_ROLE_KEY`
pertenece al proyecto y su JWT no está vencido, pero Data API responde `401`, señal de que la
llave fue rotada o deshabilitada. `SUPABASE_TOKEN` responde `403`. La muestra se persistió por
la conexión MCP autenticada. Actualizar la llave global y el secret de GitHub antes del cron.

## Corrida México 2026-07-16

- Apify run `JHSkSu6RA9vbggrrK`: 500 resultados, 500 `source_job_id` únicos y costo real
  USD 0.50.
- Todas las búsquedas usaron `location=Mexico` y `f_TPR=r604800`. Las fechas guardadas van del
  10 al 17 de julio de 2026.
- Supabase conserva 497 descripciones, 456 dominios y los 500 logos. Los 500 excerpts respetan
  el máximo de 6,000 caracteres; copy y envío permanecen vacíos/desactivados.
- Prefiltro inicial: 229 `high`, 120 `medium`, 120 `review` y 31 `low`. Es prioridad de revisión,
  no fit final.
- El límite global de 500 se llenó después de 21 de las 92 URLs. El orden intercalado sí produjo
  títulos en español, inglés y portugués, pero para cobertura completa de las 92 taxonomías una
  corrida futura debe repartir cuotas por familias en vez de usar un solo límite global.
- La llave global de `SUPABASE_SERVICE_ROLE_KEY` volvió a responder `401`. No se repitió el gasto:
  se importó el dataset ya pagado mediante la conexión MCP autenticada y después se eliminó la
  extensión HTTP temporal.
