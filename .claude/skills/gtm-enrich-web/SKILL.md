---
name: gtm-enrich-web
description: Enriquece empresas SIN dominio ni LinkedIn URL. Capa 1 masiva y barata con Parallel Task API (processor lite, ~$5/1000 empresas) + capa 2 de subagentes de investigación web que verifican y corrigen lo dudoso, en loop hasta que cada resultado esté confirmado. Acepta un CSV o una tabla de Supabase. Lo que de verdad no existe se marca 🟣 NOT_FOUND — nunca se inventa.
argument-hint: <archivo.csv | tabla_supabase> [--limit N] [--workspace ws]
---

# GTM Enrich Web — dominio + LinkedIn con Parallel + subagentes verificados

## Antes de empezar (contrato de memoria)
1. Lee `LEARNINGS.md` en este directorio.
2. Requiere `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` si el destino es Supabase, y `PARALLEL_API_KEY` para la capa 1 (si falta, saltar directo al modo solo-subagentes del piloto original).
3. Regla de oro: **un dato inventado es peor que un null**. El sentinel 🟣 `NOT_FOUND` es un resultado válido y honesto.

## Entrada
- Un CSV con al menos una columna de nombre de empresa (idealmente razón social Y nombre comercial, más estado/país como desambiguador), o
- Una tabla de Supabase con filas donde `domain is null` / `linkedin_url is null` (ej. `sofoms`).
- Si la tabla destino no tiene las columnas, agregarlas: `domain text, linkedin_url text, enrichment_status text, enrichment_evidence text, enriched_at timestamptz`.

## Pasos

### 1. Capa 1 — Parallel Task API (masiva, ~$5 USD por 1,000 empresas)
- SDK `parallel-web` (`pip install parallel-web`), processor **`lite`** (validado: `base` cuesta 2x y NO mejora — 17/20 vs 16/20 dominios en el piloto).
- Un task run por empresa, hasta 10 en paralelo con threads. Input: razón social + nombre comercial + estado + instrucción anti-invención ("a wrong answer is worse than null", "similar names are NOT a match").
- Output schema JSON: `{domain, linkedin_url, company_alive (bool), evidence}`. `company_alive=false` = empresa muerta/en liquidación → candidata directa a 🟣 con nota.
- Solo cobran runs exitosos.

### 2. Triage automático de la capa 1
Aceptar directo el resultado de Parallel solo si TODO se cumple:
- El dominio o el slug de LinkedIn guarda relación clara con el nombre comercial (match normalizado).
- No es empresa filial de grupo financiero/corporativo (si el nombre contiene "Grupo Financiero", marca de banco/OEM, etc. → SIEMPRE a capa 3, porque Parallel sistemáticamente devuelve el dominio/LinkedIn del GRUPO en vez del de la entidad).
- `company_alive=true` y ambos campos presentes.
Todo lo demás (nulls, filiales, mismatch nombre-dominio, muertas) va a la capa 3. En el piloto SOFOM E.R. (peor caso: puras filiales) Parallel solo coincidió 9/20 en LinkedIn; en empresas independientes se espera mucho más.

### 3. Capa 3 — Subagentes de investigación (solo los dudosos, en paralelo, en background)
Lotes de **5 empresas por subagente** en JSON en el scratchpad (`batch_N.json`) con: id, nombre legal, nombre comercial, ubicación, y el candidato de Parallel con la duda concreta. El prompt de cada agente DEBE incluir:
- Buscar **dominio oficial** (solo host, sin `https://` ni `www.`) y **LinkedIn company page** (`linkedin.com/company/<slug>`, nunca perfiles personales).
- **Verificación obligatoria del sitio**: WebFetch al candidato y confirmar que pertenece a ESA entidad legal (razón social en footer/aviso de privacidad, o match de marca inconfundible). Nombres parecidos NO son match.
- LinkedIn no se deja fetchear → verificar por snippets de resultados de búsqueda (nombre + país + industria).
- Filiales de grupos (Banorte, Inbursa, GM…): preferir la presencia web más específica de la entidad/producto.
- Regla estricta anti-invención: si no se confirma, devolver `null`.
- Output: `result_N.json` con `[{id, domain|null, linkedin_url|null, status: found|partial|not_found, evidence, confidence}]`.

### 4. Loop de verificación (el orquestador, no confía ciegamente)
Repetir hasta convergencia (máx. 3 rondas):
1. **Checks automáticos** sobre cada resultado:
   - El dominio resuelve (HTTP 200/301 vía curl) y no es un parked domain / dominio de terceros (agregadores tipo dun&bradstreet, directorios, marketplaces = rechazo).
   - El LinkedIn URL tiene formato `linkedin.com/company/...` válido.
   - El slug/dominio guarda relación plausible con el nombre (si no, sospechoso).
   - `confidence: low` o evidencia vaga = sospechoso.
2. **Los sospechosos vuelven a un subagente verificador** con contexto de por qué se dudó ("confirma o corrige: ¿este dominio es de X razón social?").
3. Lo que el verificador confirma pasa; lo que corrige se re-checa; lo que no se pudo confirmar tras las rondas → 🟣 `NOT_FOUND`.

### 5. Persistir
- Supabase: PATCH por id — `domain`, `linkedin_url`, `enrichment_status` (`found` | `partial` | `not_found`), `enrichment_evidence`, `enriched_at = now()`.
- CSV: escribir `<archivo>_enriched.csv` con las columnas nuevas.
- Antes de persistir dominios, correr dedupe contra `companies` por dominio (un dominio ya existente en la base = ligar, no duplicar).

### 6. Reporte (aquí mismo, en el chat)
Tabla con: empresa | dominio | LinkedIn | status. Usar 🟣 para los `NOT_FOUND`.
Resumen: N found / N partial / 🟣 N not_found, rondas de verificación usadas, y qué corrigió el loop (para que se vea qué atrapó).

## Al terminar (contrato de memoria)
- Registrar en `LEARNINGS.md`: patrones de fuentes que engañan (directorios, agregadores), tipos de empresa difíciles (filiales de grupos, razones sociales genéricas), y queries que funcionaron.
- Si el piloto (20) sale limpio, se puede escalar subiendo `--limit`; mantener 5 empresas/agente y máximo ~6 agentes simultáneos por ronda.
