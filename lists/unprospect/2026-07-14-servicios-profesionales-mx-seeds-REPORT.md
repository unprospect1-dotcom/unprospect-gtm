# Servicios profesionales MX — 3 universos lookalike (Ocean) — fase seeds + muestra

- **Fecha:** 2026-07-14
- **Workspace:** unprospect
- **Estado:** **aprobado y ejecutado** — TI y contable jalados completos y en Supabase; BPO descartado;
  web enrichment (crawl A) en curso.
- **Decisiones del usuario:** foco en servicios profesionales; staffing EXCLUIDO (fees bajos en MX);
  tamaño mínimo 10 empleados alcanzables (LinkedIn); "software que mencione IA" aparcado como universo futuro;
  **BPO/nómina descartado del todo** (2026-07-14); TI + contable aprobados para pull completo + web enrichment.

## Contexto de saldo

- Saldo Ocean al arrancar: 4,142.8 one-time + 300 recurrentes (dailyLimitRateLeft 1001).
- Presupuesto por corrida (providers.yaml): max 800 cr, reserva 500.

## Sizing gratis (GetLeads, contactos en MX con employees_min 10)

| Nicho | Industrias GetLeads | Contactos |
|---|---|---|
| Consultoría TI / software factories | IT Services and IT Consulting + Software Development + afines | 107,103 |
| Despachos contables/fiscales | Accounting | 11,287 |
| BPO / maquila de nómina | Outsourcing and Offshoring Consulting + Outsourcing/Offshoring | 5,784 |

## Modo SEEDS (cold start, AI Ark SMART + evaluación LLM)

Pools AI Ark (`productAndServices` SMART es+en, location Mexico, employeeSize 10–300):
TI 143 total / contable 134 / BPO 252. Se jalaron 30 candidatos por nicho (~9 cr AI Ark)
y se evaluó negocio central por descripción; falsos positivos tirados: staffing TI,
ciberseguridad pura, software de producto vertical, call centers, reclutadoras puras,
un fabricante industrial y un transportista.

### Seeds TI FINALES (6 fábricas de software + 4 consultoras/integradoras TI)

teknik.mx, gtec.com.mx, dotnet.com.mx, thincode.com, rd-its.com, cynthus.com.mx,
matersys.mx, softnet.com.mx, itbs-grp.com, interax.com.mx
(Sustituciones: novutek.com "crawler failed" → itbs-grp.com; solsersistem.net crawl >7 min → interax.com.mx;
hlsgroup.com.mx warmup OK pero "missing context vector" en search → softnet.com.mx)

### Seeds contable FINALES (fiscal internacional + despachos integrales + mid-market local)

skatt.com.mx, loftonsc.com, pkf.com.mx, bhrmx.com, delapazcostemalle.com.mx,
bargallocardosoyasociados.com, nexiamexico.mx, hlbpuebla.com, ramirezsoto.com.mx, villegasyvillegas.com.mx
(grservicios.com.mx crawl >7 min → villegasyvillegas.com.mx)

### Seeds BPO/nómina v2 FINALES (solo nómina/administración de personal)

pronomina.com.mx, eog.mx, grupoono.lat, grupoestrategia.mx, intermex.mx, labormx.com

**Learning clave:** la v1 incluía coltomex.com y alliax.com (back-office/shared services tech) y la muestra
se fue COMPLETA a consultoría TI/procesos — 2 seeds tech entre 8 arrastraron el centro semántico.
La v2 sin ellos regresó el universo a capital humano/nómina. pagopro.com.mx quedó fuera (crawl no terminó).

## Filtros Ocean (reproducibles, sintaxis verificada)

```json
{"companiesFilters": {"lookalikeDomains": [...], "excludeDomains": [...seeds],
 "companyMatchingMode": "precise",
 "primaryLocations": {"includeCountries": ["mx"]},
 "employeeCountLinkedin": {"from": 10, "to": 700}}}
```
(⚠️ `primaryLocations` es objeto; `companyMatchingMode` va DENTRO de companiesFilters.)

## Muestras y totales (size 10 c/u, relevancia A en todos los devueltos)

| Universo | Total | Calidad de muestra | Nota |
|---|---|---|---|
| ti-consultoria-software-mx | **3,068** | 10/10 en nicho | consultoras/dev shops puras |
| despachos-contables-mx | **1,503** | ~7-8/10 | drift menor a legal (2) + 1 SaaS facturación — recortable con relevancia A + clasificación |
| bpo-nomina-mx (v2) | **3,503** | ~6-7/10 nómina/PEO core | 2-3 reclutadoras puras coladas — en MX nómina y staffing son un mismo espacio; separar exige crawl+clasificación |

## Créditos gastados en esta fase

- AI Ark: ~9.3 cr (3 sondeos size 1 + 3 pools de 30) — saldo 13,869.4 → ~13,860
- Ocean: 8.2 cr (1 sondeo size 1 + 4 muestras de 10 × 2.0 cr) — saldo 4,142.8 → 4,134.6 one-time (+300 recurrentes)

## Pull completo EJECUTADO (2026-07-14, costos reales)

| Universo | Empresas | Relevancia A/B/C | Créditos | Artefactos |
|---|---|---|---|---|
| ti-consultoria-software-mx | 3,068 | **1,067** / 1,952 / 49 | 613.6 | CSV local (gitignored) + Supabase `list_companies` |
| despachos-contables-mx | 1,503 | **574** / 896 / 33 | 300.6 | CSV local (gitignored) + Supabase `list_companies` |
| bpo-nomina-mx | — | — | 0 | **DESCARTADO por el usuario** (staffing no paga fees en MX) |

- Gasto total del pull: 914.2 cr. Saldo final Ocean: **3,220.4 one-time + 300 recurrentes**.
- Gasto acumulado de la corrida completa (sondeos + muestras + pull): ~922.4 cr Ocean + ~9.3 cr AI Ark.
- Traslape con universos previos (solar/autotransporte): 171 dominios de TI — coexisten por (niche, domain).
- Incidente: un reset de conexión tumbó el pull entre universos; el driver con resume por página
  no perdió créditos y el retry de errores de red quedó endurecido (backoff exponencial).

## Web enrichment (gtm-web-crawler, $0) — COMPLETADO 2026-07-14

Corte de relevancia A (regla confirmada del skill): **1,641 dominios** (1,067 TI + 574 contable),
concurrencia 5, persistencia directa a Supabase `site_crawls` (upsert por dominio, resume idempotente).

| Universo | Crawleados | OK | Fallidos (capa B agéntica) | Tasa |
|---|---|---|---|---|
| TI (relevancia A) | 1,067 | 859 | 144 (+64 previos al restart sin desglose en log) | ~81-86% |
| Contable (relevancia A) | 574 | 516 | 58 | 90% |

- Un reinicio del contenedor a media corrida NO costó nada: resume por archivo + upsert por dominio.
- El `clean_text` de site_crawls es el insumo para gtm-classify-b2b y gtm-pain-segments (paso siguiente).
- Los `ok:false` (challenge/Cloudflare/sitio muerto) están marcados en site_crawls para la capa B agéntica.

## Siguiente paso sugerido

1. `gtm-classify-b2b` sobre el clean_text de los dos universos (verificar negocio central, tirar colados).
2. `gtm-pain-segments` con sales_count/departmentSizes ya capturados en list_companies.
3. People search + reveal de emails en Ocean SOLO sobre las empresas verificadas.

## Dedupe

- `outreach_log` no existe aún en Supabase (nada contactado) — nada que excluir.
- `list_companies` (9,530 filas: solar/autotransporte) se cruza antes del pull completo.

## Universo aparcado (decisión del usuario)

- **Software MX que mencione IA** — para después. Rutas: keywords filter en Ocean sobre lookalike de
  software factories, o post-filtro del crawl del universo TI (la señal "IA" abunda: ya se ve en keywords
  de la muestra TI: ensitech, adbansys, virtus, bcareconsulting).
