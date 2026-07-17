---
name: gtm-profile-company
description: Perfila empresas desde site_crawls.clean_text para saber si son B2B, qué venden, a quién venden, su ICP probable y si su economía comercial parece apta para outbound. Usar después de gtm-web-crawler al segmentar, priorizar o preparar listas; también para validar una muestra antes de clasificar en masa.
---

# GTM company profile

Producir un perfil breve y demostrable desde `clean_text`. Separar siempre **modelo de
negocio** de **fit outbound**; no inventar ticket.

## Flujo

1. Leer `LEARNINGS.md` y `references/rubric.md` completos. El rubric es la única fuente
   del criterio y del esquema; LEARNINGS conserva resultados y fronteras ya observadas.
2. Preparar JSON con `domain`, `clean_text` y hash de fuente. La cola durable es
   `company_gtm_profiles`; procesar solo `pending`, `stale` o `failed`.
3. Primera pasada: compactar a 4K caracteres con `scripts/compact_batches.py` o
   `scripts/rebatch_compact.py` y usar lotes de 10. Nunca superar 10 empresas por worker.
4. Ejecutar capa 1 con los subagentes más baratos del harness:
   - Claude Code: Haiku.
   - Codex: `gpt-5.4-mini`, esfuerzo `low`, mediante las lanes de `.codex/agents/`.
5. No repetir toda la base. Enviar a segunda pasada ciega, usando el contexto de hasta 8K,
   solo si se cumple al menos una condición:
   - `business_model` es `mixed` o `unclear`;
   - `confidence` no es `high`;
   - `sales_economics` u `outbound_fit` es `unclear`;
   - falla una regla de consistencia del validador;
   - pertenece a la muestra de control determinística del 5% de casos claros.
6. Rotar el worker de revisión y no mostrarle la respuesta inicial. Validar cada salida con
   `scripts/validate_profiles.py`; toda cita debe existir literalmente en el contexto UTF-8.
7. Aceptar directamente la primera pasada clara que valide. En casos revisados, aceptar si
   coinciden los campos categóricos; enviar solo desacuerdos a árbitro ciego o revisión humana.
8. Persistir el perfil aceptado y ambas corridas auditables solo después de validar y confirmar
   que `profiled_source_hash = current_source_hash`.

## Contrato de contexto

- Usar únicamente `clean_text`; no navegar ni completar desde conocimiento de marca.
- Leer archivos como UTF-8 explícito. En PowerShell usar `Get-Content -Encoding UTF8`.
- Primera pasada: máximo 4K, conservando inicio y líneas de oferta, audiencia, prueba y
  contacto. Revisión: volver al contexto durable de hasta 8K.
- En volumen: `sells` ≤10 palabras, `primary_customer` ≤12, `outbound_reason` ≤12, ICP en
  etiquetas mínimas y una cita literal. La información fuente completa nunca se elimina.
- Usar `null`, `[]` o `unclear` cuando la evidencia no alcance.

## Comandos

```bash
python .claude/skills/gtm-profile-company/scripts/make_batches.py \
  --input companies_with_clean_text.json --outdir work/profile_batches --size 8

python .claude/skills/gtm-profile-company/scripts/rebatch_compact.py \
  --input-dir work/profile_batches --output-dir work/profile_batches_compact \
  --start 1 --end 100 --size 10 --context-limit 4000

python .claude/skills/gtm-profile-company/scripts/validate_profiles.py \
  --source companies_with_clean_text.json --results profiles_pass1.json

python .claude/skills/gtm-profile-company/scripts/compare_runs.py \
  --source companies_with_clean_text.json \
  --run-a profiles_pass1.json --run-b profiles_pass2.json
```

Los scripts de batching, compacción, validación y comparación solo procesan archivos locales;
no llaman proveedores ni escriben en bases de datos.

## Modo barato en una sesión nueva

Usar `gpt-5.4-mini` con esfuerzo `low`. La sesión barata puede ser el orquestador completo;
debe reportar solo por checkpoint, no por empresa. Prompt operativo:

> Usa `$gtm-profile-company`. Reanuda `company_gtm_profiles`; procesa solo pending/stale,
> valida citas, persiste válidos y deja ambiguous/low-confidence en needs_review. No navegues
> ni recrawlees.
