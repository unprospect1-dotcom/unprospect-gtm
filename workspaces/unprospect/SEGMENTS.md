# Segmentos por dolor observable — Unprospect

> Lo mantiene `/gtm-pain-segments`. Un segmento = atributo observable → dolor probable → cómo verificarlo a escala.
> Estados: `propuesto` → `verificando` → `activo` → `descartado`.

| Segmento (slug) | Atributo observable | Dolor probable | Verificación a escala | Tamaño est. | Estado | Notas |
|---|---|---|---|---|---|---|
| ti-consultoria-software-mx | Consultora TI / fábrica de software MX, 10-700 empleados LinkedIn | (pendiente /gtm-pain-segments) | Lookalike Ocean precise, muestra 10/10 limpia | 3,068 | verificando | Seeds y filtros en lists/unprospect/2026-07-14-servicios-profesionales-mx-seeds-REPORT.md |
| despachos-contables-mx | Despacho contable/fiscal/auditoría MX, 10-700 empleados LinkedIn | (pendiente) | Lookalike Ocean precise, muestra 7-8/10 | 1,503 | verificando | Drift a legal reciclable como segmento despachos-legales-mx |
| bpo-nomina-mx | Maquila de nómina / administración de personal MX, 10-700 empleados LinkedIn | (pendiente) | Lookalike Ocean precise v2 (solo seeds nómina), muestra 6-7/10 | 3,503 | descartado | [confirmado por el cliente 2026-07-14] Fuera: en MX nómina/staffing comparten espacio y staffing no paga los fees. Seeds y filtros quedan en el REPORT por si se retoma |
| distribuidores-industriales-mx | Distribuidor de refacciones/rodamientos/suministro industrial (MRO) MX | (pendiente) | Lookalike Ocean precise, muestra 10/10 | 3,404 (A=530) | verificando | 2026-07-15-8-listas-b2b-REPORT.md · 22% del A-cut corre Google Ads |
| empaque-embalaje-mx | Distribuidor/fabricante de material de empaque y embalaje MX | (pendiente) | Lookalike Ocean precise, muestra 9/10 | 2,569 (A=497) | verificando | Ídem · 24% ads |
| agencias-audiovisuales-mx | Casa productora de video/contenido audiovisual corporativo MX | (pendiente) | Lookalike Ocean precise, muestra 10/10 | 3,407 (A=216) | verificando | Cola C alta; A-cut = productoras puras · 13% ads |
| fintech-b2b-mx | Fintech B2B MX (payments/spend-mgmt/SME lending, no consumidor) | (pendiente) | Lookalike Ocean precise, muestra ~8/10 (deriva a consumer lending) | 2,109 (A=254) | verificando | Limpiar B2C con clasificación · 26% ads |
| logistics-tech-mx | SaaS/plataforma de logística y envíos MX (no transportistas) | (pendiente) | Lookalike Ocean precise, muestra 10/10 | 1,312 (A=280) | verificando | 24% ads |
| hr-tech-mx | Software de RH/nómina-tech/talento B2B MX (no staffing) | (pendiente) | Lookalike Ocean precise, muestra ~8/10 (adyacencia reclutamiento) | 1,299 (A=94) | verificando | 28% ads |
| ciberseguridad-mx | MSSP/consultores de ciberseguridad MX | (pendiente) | Lookalike Ocean precise, muestra 10/10 | 1,661 (A=321) | verificando | 22% ads |
| saas-producto-mx | SaaS producto B2B MX (no consultoría TI) | (pendiente) | Lookalike Ocean precise, muestra ~9/10 (deriva a ERP-consultoría) | 1,138 (A=126) | verificando | 38% ads (el más alto) |
| senales-contratacion-mx | Empresa MX contratando rol comercial/prospección (señal fresca semanal) | Necesitan abrir cuentas/pipeline pero prospectar no es un sistema | Apify LinkedIn Jobs (f_TPR=r604800) + calificador 2-capas + copywriter | flujo semanal | propuesto | Diseño en SIGNALS-hiring-flow.md; muestra en SIGNALS-sample-copy.md; keywords en signals-keywords.txt |
