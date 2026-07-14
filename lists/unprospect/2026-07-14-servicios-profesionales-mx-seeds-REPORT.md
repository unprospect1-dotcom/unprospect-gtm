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

### Seeds TI (6 fábricas de software + 4 consultoras/integradoras TI)

teknik.mx, gtec.com.mx, dotnet.com.mx, thincode.com, rd-its.com, cynthus.com.mx,
matersys.mx, hlsgroup.com.mx, itbs-grp.com, solsersistem.net
(novutek.com falló el crawler de Ocean → sustituido por itbs-grp.com; backup extra: interax.com.mx)

### Seeds contable (fiscal internacional + despachos integrales + mid-market local)

skatt.com.mx, loftonsc.com, pkf.com.mx, bhrmx.com, delapazcostemalle.com.mx,
bargallocardosoyasociados.com, nexiamexico.mx, hlbpuebla.com, grservicios.com.mx, ramirezsoto.com.mx

### Seeds BPO/nómina (6 nómina/administración de personal + 3 back-office/shelter, SIN call centers ni reclutadoras)

pronomina.com.mx, eog.mx, pagopro.com.mx, grupoono.lat, grupoestrategia.mx,
intermex.mx, labormx.com, coltomex.com, alliax.com

## Filtros Ocean (reproducibles)

`companyMatchingMode: precise`, `primaryLocations: ["mx"]`,
`employeeCountLinkedin: {from: 10, to: 700}`, `excludeDomains` = los seeds.
Archivos: oc_ti.json / oc_conta.json / oc_bpo.json (scratchpad de la sesión).

## Muestras y totales

_(pendiente — se llena al correr las muestras de 10)_

## Créditos

- AI Ark: ~9.3 cr (3 sondeos size 1 + 3 pools de 30)
- Ocean: warmup gratis; muestras 3 × 10 × 0.2 = ~6 cr (por confirmar con creditsUsed)

## Dedupe

- `outreach_log` no existe aún en Supabase (nada contactado) — nada que excluir.
- `list_companies` (9,530 filas: solar/autotransporte) se cruza antes del pull completo.
