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
**ES masc:** Director General · Dirección General · Direccion General · Director Ejecutivo · Gerente General ·
Fundador · Cofundador · Co-Fundador · Socio · Socio Director · Socio Fundador · Dueño · Dueno ·
Propietario · Presidente · Consejero Delegado · Administrador Único · Administrador Unico · Apoderado Legal · Director
**ES fem (¡obligatorio!):** Directora General · Directora Ejecutiva · Gerente General *(neutro)* · Gerenta General ·
Fundadora · Cofundadora · Socia · Socia Directora · Dueña · Propietaria · Presidenta · Directora · Administradora Única
**EN:** CEO · Founder · Co-Founder · Owner · President · Managing Director · Managing Partner · Chief Executive · Partner
> Jerga MX clave: "Administrador Único" y "Apoderado Legal" = dueño legal de la razón social (muy común en PyME).
> **Género (2026-07-16, catch del usuario en movon):** el título en español lleva género y el match los separa —
> incluir SIEMPRE la forma femenina (Directora, Dueña, Socia, Fundadora, Presidenta, Jefa, Coordinadora).

### P2 · Líder comercial
**ES:** Director Comercial · Dirección Comercial · Direccion Comercial · Subdirector Comercial · Gerente Comercial ·
Gerente de Ventas · Director de Ventas · Jefe de Ventas · Jefe Comercial · Encargado de Ventas ·
Coordinador Comercial · Coordinador de Ventas · Responsable Comercial · Responsable de Ventas · Líder Comercial · Lider Comercial ·
Gerente de Nuevos Negocios · Desarrollo de Negocios · Gerente de Cuentas · Gerente de Desarrollo Comercial
**ES fem:** Directora Comercial · Gerenta Comercial · Jefa de Ventas · Jefa Comercial · Encargada de Ventas ·
Coordinadora Comercial · Responsable Comercial · Líder Comercial
**EN:** VP Sales · VP of Sales · Head of Sales · Sales Director · Sales Manager · Chief Revenue Officer · CRO ·
Commercial Director · Business Development Manager · Head of Business Development
> Jerga MX clave: "Comercial" ≈ liderazgo de ventas; "Desarrollo de Negocios" = business development. Incluir formas femeninas.

### P3 · Líder de marketing
**ES:** Director de Marketing · Dirección de Marketing · Gerente de Marketing · Director de Mercadotecnia ·
Dirección de Mercadotecnia · Gerente de Mercadotecnia · Coordinador de Marketing · Coordinador de Mercadotecnia ·
Jefe de Marketing · Responsable de Marketing · Líder de Marketing · Director de Marca · Gerente de Marca
**ES fem:** Directora de Marketing · Gerenta de Marketing · Directora de Mercadotecnia · Coordinadora de Marketing ·
Jefa de Marketing · Responsable de Marketing · Directora de Marca
**EN:** CMO · Chief Marketing Officer · Head of Marketing · Marketing Director · Marketing Manager · VP Marketing ·
Head of Growth · Growth Marketing · Demand Generation
> Jerga MX clave: **"Mercadotecnia"** es la palabra formal de marketing en MX — sin ella se pierde medio universo.

## El hueco estructural de las bases (2026-07-16, del usuario)
Las bases B2B (AI Ark, GetLeads, Apollo…) son un SUBCONJUNTO de LinkedIn. Mucho dueño/directora de PyME MX
está **en LinkedIn pero no en ninguna base** (confirmado: la directora general de movon no está en AI Ark ni GetLeads).
Pasa en TODAS las bases, no en una. Qué hacer con eso:
- **Para el canal EMAIL:** si la persona no está en las bases, casi nunca hay email verificado aunque scrapees su nombre
  → **no es emaileable**. Anclar el email en la persona que las bases SÍ tienen con email (típico: P2 comercial).
- **Para los dueños ausentes de las bases:** son target de **LinkedIn** (Apify saca empleados por LinkedIn URL de la
  empresa → connection + DM), canal aparte. No bloquear el ship de email por ellos.
- Solo vale un pase Apify+enrich (LinkedIn→email) en cuentas de alto valor, midiendo hit rate de email antes de escalar.

## Excludes (falsos positivos a tirar)
Asistente · Assistant · Becario · Intern · Practicante · Auxiliar · Recepcionista · Community Manager (para P2).

## Método de ejecución (por batch)
1. **Sondeo gratis de la unión** por persona: `count(A)`, `count(B)`, `count(A∩B)` → A∪B = A + B − A∩B. Reporta cuánto agrega el diccionario sobre la taxonomía.
2. **Muestra de aprobación** (~25) → correcciones del usuario → cada una vuelve filtro/exclude → re-sondeo gratis.
3. **Dedupe** contra `outreach_log` (nadie ya contactado).
4. **Export con email** (AI Ark, verifica MX en tiempo real; ~1 cr por contacto con email, 0 si no hay). `max_per_company: 1` por persona.
5. Normaliza al `csv_schema`, sube a `list_companies`/artefacto, listo para el sender.
