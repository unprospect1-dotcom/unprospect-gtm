# 8 universos B2B MX (Ocean lookalike) — reporte de cierre

- **Fecha:** 2026-07-15
- **Workspace:** unprospect
- **Estado:** **aprobado y ejecutado.** 8 listas en Supabase `list_companies`; sales counts (A-cut),
  web crawl (A-cut) y flag de Google Ads persistidos. Enrichment de slots + clasificación B2B → Codex.
- **Misión del día:** rescatar el saldo de Ocean antes de que el trial se cortara. **One-time quemado a $0.**

## Resumen ejecutivo

| Universo | Total | Rel. A | Rel. B | Rel. C | Créditos Ocean | Ads (A-cut) |
|---|---|---|---|---|---|---|
| distribuidores-industriales-mx (MRO) | 3,404 | 530 | 2,763 | 111 | 680.8 | 115/530 (22%) |
| empaque-embalaje-mx | 2,569 | 497 | 1,926 | 146 | 513.8 | 121/497 (24%) |
| agencias-audiovisuales-mx | 3,407 | 216 | 2,395 | 796 | 681.4 | 27/216 (13%) |
| fintech-b2b-mx | 2,109 | 254 | 1,574 | 281 | 421.8 | 65/254 (26%) |
| logistics-tech-mx | 1,312 | 280 | 995 | 37 | 262.4 | 67/280 (24%) |
| hr-tech-mx | 1,299 | 94 | 994 | 211 | 259.8 | 26/94 (28%) |
| ciberseguridad-mx | 1,661 | 321 | 847 | 493 | 332.2 | 71/321 (22%) |
| saas-producto-mx | 1,138 | 126 | 836 | 176 | 227.6 | 48/126 (38%) |
| **TOTAL** | **15,899** | **2,318** | **12,330** | **2,251** | **3,379.8** | **540/2,318 (23%)** |

- Saldo Ocean final: **0 one-time + ~110 recurrentes** (empezamos con 3,220 one-time + 300 recurrentes).
- **Web crawl A-cut:** 2,203 dominios, **91% ok** (2,017 crawleados a `site_crawls`, 186 a capa-B agéntica).
- **Google Ads (Apify Transparency Center, 1 ad/dominio):** flag `ads_runs`/`ads_last_shown`/`ads_formats`
  en `list_companies` sobre los 22,008 dominios únicos de los 12 universos. **Resultado final:
  3,550 dominios anuncian (16.1% del total; ~23% del A-cut, que es mayor calidad).** Costo Apify
  total ~$11 (3 cuentas FREE, ~$5/mes c/u, con rotación de tokens).

## Seeds por universo (los que funcionaron)

- **MRO / distribuidores-industriales-mx:** brr.mx, snr.com.mx, idrmx.com, rorisa.com, marol.com.mx,
  lion-supply.com, xpressindustrial.com, jomsmx.com.mx, refatec.mx, eissa.mx (refacciones/rodamientos/MRO).
- **empaque-embalaje-mx:** fastpack.mx, solupack.com.mx, novelsa.com, qsource.com.mx, sealingint.com,
  multiempaquesinternacionales.com, todopallets.com, vessel.mx.
- **agencias-audiovisuales-mx:** btfmedia.com, lavaexplosive.com, eraseunavez.mx, fosforo.video,
  oyefilms.com.mx, monitorstudio.com.mx, republic24.net, hazvideos.com (casas productoras puras).
- **fintech-b2b-mx:** clara.com, mendel.com, konfio.com, conekta.com, belvo.com, higo.io, mundi.com,
  covalto.com, tryjeeves.com, minu.mx (payments/spend-mgmt/SME lending B2B).
- **logistics-tech-mx:** nuvocargo.com, envia.com, mienvio.mx, cargamos.com, 99minutos.com, cubbo.com,
  solvento.com, liftit.co, klog.co (SaaS de envíos/logística).
- **hr-tech-mx:** runahr.com, worky.mx, factorialhr.com, buk.mx, minu.mx, sesamehr.com, talenteca.com,
  nominapp.com (software de RH/nómina/talento).
- **ciberseguridad-mx:** silikn.com, strike.sh, kionetworks.com, smartekh.com, hackmetrix.com, ikusi.com,
  deltaprotect.com, cyberpymes.com, a3sec.com (MSSP/consultores de seguridad).
- **saas-producto-mx:** yalo.com, osmos.io, binderp.com, incode.com, truora.com, leadsales.io,
  auronix.com, mattilda.io, gigstack.io (SaaS producto B2B).

## Filtros Ocean (reproducibles)

```json
{"companiesFilters": {"lookalikeDomains": [<seeds>], "excludeDomains": [<seeds>],
 "companyMatchingMode": "precise", "primaryLocations": {"includeCountries": ["mx"]},
 "employeeCountLinkedin": {"from": 10, "to": 700}}}
```
(audiovisual y saas usaron `from: 5`.) Economía medida: **0.2 cr/resultado** de company search.

## Distribución de sales_bucket (A-cut, señal de equipo comercial)

Ver `list_companies.sales_bucket`. Ejemplos: MRO {0-sin-señal 167, 3-10 173, 1-2 131, 11-50 53, 50+ 6};
saas {0-sin-señal 34, 3-10 47, 11-50 13, 1-2 32}. Routing del PLAYBOOK v2 por bucket de ventas.

## Calidad de los lookalikes (muestra de aprobación)

- **10/10 limpio:** MRO, empaque, audiovisual, ciberseguridad, logistics-tech.
- **~8-9/10 con deriva menor:** saas (algo de ERP-consultoría), hr-tech (adyacencia a reclutamiento),
  fintech (deriva a lending de consumidor: Baubap/Yotepresto). La limpia el corte A + clasificación B2B.
- Audiovisual trae más cola C (796) — el A-cut real son 216 productoras puras.

## Incidentes y su fix (ver LEARNINGS de gtm-ocean)

- Contenedor reclamado en idle mató procesos `nohup` (sales/crawlers) a media corrida → resume idempotente.
- Google Ads: 5 corridas Apify en paralelo saturaron el request-queue → correr secuencial chunks chicos.
- Cuentas Apify FREE topan a ~$5/mes → rotación de 3 tokens (serene_rye agotada; 2 y 3 en uso).
- Crawler: chromium crashea bajo contención y marca 'sin_contenido_util' en masa (falsos-fallidos) →
  concurrencia 3 + re-crawl de los ok:false recuperó del 35% al 91%.

## Siguiente paso (handoff a Codex)

1. Extracción de slots AI (`observacion`/`icp_corto`) sobre `site_crawls.clean_text` de los A-cut.
2. `gtm-classify-b2b` para tirar colados (consumer-lending en fintech, reclutamiento en hr-tech).
3. Routing de campaña por `sales_bucket` + flag `ads_runs` (A/B de Google Ads del PLAYBOOK §8).
4. People search + reveal de emails en Ocean SOLO cuando haya saldo (recurrentes: ~110).
