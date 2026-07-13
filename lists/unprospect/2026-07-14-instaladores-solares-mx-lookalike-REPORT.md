# Instaladores solares MX — lookalike Ocean (2026-07-14)

**Estado: LISTA COMPLETA — 1,120 empresas (el universo lookalike entero de MX), 1,032 nuevas.**

## Cómo se construyó (modo SEEDS cold-start + lookalike, receta completa en gtm-ocean/SKILL.md)
1. Sizing gratis: GetLeads count `company_description: "paneles solares"` + MX → 1,744 contactos ($0).
2. Pool de candidatos: AI Ark `productAndServices SMART ["instalación de paneles solares","solar panel installation"]` + MX + employeeSize 2–700 → 31 empresas (3.1 créditos).
3. Evaluación LLM de descripciones → descartados telecom, US, automatización, remodelaciones.
4. Warmup Ocean (gratis) → 2 backups usados por "crawler failed" (etesla.mx, globalsolare.com).
5. Lookalike `precise` con 10 seeds.

## Seeds (validados con warmup)
galt.mx, ecocentro.mx, naturalproject.mx, energialibre.com.mx, energiasolarinc.com,
marsamsolar.com, sunbank.mx, heliostecnologiasolar.net, pueblosolar.mx, greenvolt.com.mx

## Query reproducible (POST /v3/search/companies)
```json
{"companiesFilters": {
  "lookalikeDomains": ["<los 10 seeds>"],
  "companyMatchingMode": "precise",
  "primaryLocations": {"includeCountries": ["mx"]},
  "employeeCountLinkedin": {"from": 2, "to": 700},
  "excludeDomains": ["<los 10 seeds>"]}}
```

## Resultados
| Métrica | Valor |
|---|---|
| Total lookalikes MX (universo completo) | **1,120** |
| Relevancia A / B / C | 477 / 618 / 25 |
| Tamaños dominantes (autoreportado) | 2–10: 410 · 11–50: 482 · 51–200: 164 |
| Ya en Supabase | 88 |
| **Nuevas** | **1,032** |

Nota: ~11 empresas con bracket autoreportado grande (501+) pasaron el corte porque su conteo
LinkedIn es ≤700 — el corte fue por `employeeCountLinkedin` (alcanzabilidad), como se decidió.

## Créditos (costo real medido)
- **Ocean cobra 0.2 créditos por resultado de lookalike** (no 1.0 como asumía la config): 1,120 resultados + retrabajo de la primera página = **226 créditos**. Saldo Ocean después: **4,442.8**.
- AI Ark (candidatos a seed): 3.2. GetLeads: $0.
- **Costo total de la lista: ~229 créditos ≈ $0.20 de crédito por empresa.**

## Siguiente paso sugerido
Buckets de equipo comercial gratis (GetLeads count por dominio) + crawler para subcategoría
(residencial vs industrial/comercial, EPC vs distribuidor) → después personas + emails
(GetLeads/AI Ark, no Ocean reveal, salvo que se quiera validar su calidad de email).
