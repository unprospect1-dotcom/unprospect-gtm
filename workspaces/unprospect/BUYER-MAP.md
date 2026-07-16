# Buyer Map — Unprospect (MX B2B)

> Personas a contactar por empresa + banco de títulos ES/EN para la receta DM-unión.
> Lo leen `gtm-lists-aiark` y `gtm-getleads`. Regla: **taxonomía ∪ diccionario de títulos**,
> con y sin acento (el match es sensible a acentos). Sacar cada persona SOLO donde exista
> (adaptativo por `sales_bucket` / `marketing_bucket`). Sondear la unión GRATIS antes de gastar.

## Personas

| Persona | Cuándo sacarla | Taxonomía (Capa A) |
|---|---|---|
| **P1 · Dirección/Dueño** | Siempre (comprador económico) | `seniority: [founder, c_suite]` (sin depto) |
| **P2 · Líder comercial** | Donde `sales_bucket ≥ 1-2` | `departmentAndFunction: master_sales` + `seniority: [c_suite, vp, director, manager]` |
| **P3 · Líder de marketing** | Donde `marketing_bucket ≥ 1-2` | `departmentAndFunction: master_marketing` + `seniority: [c_suite, vp, director, manager]` |

Fallback: si no aparece el nivel director+, bajar a coordinador/jefe; si nada, dejar la persona vacía (no forzar).
`max_per_company: 1` por persona → hasta 3 contactos por empresa.

## Banco de títulos — Capa B (diccionario, WORD mode)

### P1 · Dirección/Dueño
**ES:** Director General · Dirección General · Direccion General · Director Ejecutivo · Gerente General ·
Fundador · Cofundador · Co-Fundador · Socio · Socio Director · Socio Fundador · Dueño · Dueno ·
Propietario · Presidente · Consejero Delegado · Administrador Único · Administrador Unico · Apoderado Legal · Director
**EN:** CEO · Founder · Co-Founder · Owner · President · Managing Director · Managing Partner · Chief Executive · Partner
> Jerga MX clave: "Administrador Único" y "Apoderado Legal" = dueño legal de la razón social (muy común en PyME).

### P2 · Líder comercial
**ES:** Director Comercial · Dirección Comercial · Direccion Comercial · Subdirector Comercial · Gerente Comercial ·
Gerente de Ventas · Director de Ventas · Jefe de Ventas · Jefe Comercial · Encargado de Ventas ·
Coordinador Comercial · Coordinador de Ventas · Responsable Comercial · Responsable de Ventas · Líder Comercial · Lider Comercial ·
Gerente de Nuevos Negocios · Desarrollo de Negocios · Gerente de Cuentas · Gerente de Desarrollo Comercial
**EN:** VP Sales · VP of Sales · Head of Sales · Sales Director · Sales Manager · Chief Revenue Officer · CRO ·
Commercial Director · Business Development Manager · Head of Business Development
> Jerga MX clave: "Comercial" ≈ liderazgo de ventas; "Desarrollo de Negocios" = business development.

### P3 · Líder de marketing
**ES:** Director de Marketing · Dirección de Marketing · Gerente de Marketing · Director de Mercadotecnia ·
Dirección de Mercadotecnia · Gerente de Mercadotecnia · Coordinador de Marketing · Coordinador de Mercadotecnia ·
Jefe de Marketing · Responsable de Marketing · Líder de Marketing · Director de Marca · Gerente de Marca
**EN:** CMO · Chief Marketing Officer · Head of Marketing · Marketing Director · Marketing Manager · VP Marketing ·
Head of Growth · Growth Marketing · Demand Generation
> Jerga MX clave: **"Mercadotecnia"** es la palabra formal de marketing en MX — sin ella se pierde medio universo.

## Excludes (falsos positivos a tirar)
Asistente · Assistant · Becario · Intern · Practicante · Auxiliar · Recepcionista · Community Manager (para P2).

## Método de ejecución (por batch)
1. **Sondeo gratis de la unión** por persona: `count(A)`, `count(B)`, `count(A∩B)` → A∪B = A + B − A∩B. Reporta cuánto agrega el diccionario sobre la taxonomía.
2. **Muestra de aprobación** (~25) → correcciones del usuario → cada una vuelve filtro/exclude → re-sondeo gratis.
3. **Dedupe** contra `outreach_log` (nadie ya contactado).
4. **Export con email** (AI Ark, verifica MX en tiempo real; ~1 cr por contacto con email, 0 si no hay). `max_per_company: 1` por persona.
5. Normaliza al `csv_schema`, sube a `list_companies`/artefacto, listo para el sender.
