# Servicios profesionales MX — 3 universos lookalike (Ocean) — fase seeds + muestra

- **Fecha:** 2026-07-14
- **Workspace:** unprospect
- **Estado:** muestras en curso — pendiente aprobación del usuario para el pull completo
- **Decisiones del usuario:** foco en servicios profesionales; staffing EXCLUIDO (fees bajos en MX);
  tamaño mínimo 10 empleados alcanzables (LinkedIn); "software que mencione IA" aparcado como universo futuro.

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

## Estimación del pull completo (0.2 cr/resultado, search only)

| Universo | Total | Costo search | Nota |
|---|---|---|---|
| TI | 3,068 | ~614 cr | |
| Contable | 1,503 | ~301 cr | |
| BPO/nómina | 3,503 | ~701 cr | pendiente decisión del usuario por mezcla con staffing |

Los tres juntos ≈ 1,616 cr > tope de 800 cr/corrida → correr en tandas.
La relevancia A suele ser ~40-45% del universo (caso solar) — el corte A se hace local post-pull.
Emails (reveal) = 1 cr/verificado, se estima después de elegir personas.

## Dedupe

- `outreach_log` no existe aún en Supabase (nada contactado) — nada que excluir.
- `list_companies` (9,530 filas: solar/autotransporte) se cruza antes del pull completo.

## Universo aparcado (decisión del usuario)

- **Software MX que mencione IA** — para después. Rutas: keywords filter en Ocean sobre lookalike de
  software factories, o post-filtro del crawl del universo TI (la señal "IA" abunda: ya se ve en keywords
  de la muestra TI: ensitech, adbansys, virtus, bcareconsulting).
