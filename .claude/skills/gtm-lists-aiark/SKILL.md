---
name: gtm-lists-aiark
description: Construye listas de leads en AI Ark (B2B database, 500M+ perfiles / 68M empresas). Búsqueda de empresas (incluye lookalikes nativos), búsqueda de personas, export con email verificado, y listas de exclusión para dedupe. Sigue el contrato universal - infiere filtros, confirma contigo, muestra de prueba, y solo entonces exporta en grande.
argument-hint: <workspace> [segmento | "lookalikes de X, Y" | descripción de la lista]
---

# GTM Lists — AI Ark

## Antes de empezar (contrato de memoria)
1. Lee `LEARNINGS.md` en este directorio y `config/providers.yaml` (sección `aiark` + `defaults` + `csv_schema`). **Toda la configuración sale de ahí — nunca hardcodees valores.**
2. Lee del workspace: `BUYER-MAP.md` si existe (títulos/seniority por persona), `SEGMENTS.md` (filtros del segmento), `PROFILE.md` (geografía/idioma del ICP).
3. Verifica que la env var indicada en `aiark.env_key` exista. Si no, detente y dilo — no simules.

## Referencia técnica de la API
- Auth: header `X-TOKEN`. Base: `aiark.base_url`. Rate limit: 5 rps / 300 rpm (respeta `rate_limit_rps`), 429 al excederse.
- `POST /companies` — búsqueda de empresas. **`lookalikeDomains` (máx 5 dominios) encuentra similares nativamente** — el camino directo cuando el usuario trae empresas de referencia. Filtros `account.*`: industries, location, employeeSize (RANGE), revenue, technologies (SMART/WORD/STRICT), naics, keyword, funding; y `employee.title/seniority/departmentAndFunction` para exigir que tengan cierto rol.
- `POST /people` — búsqueda de personas. `account.*` (filtros de SU empresa) + `contact.*`: experience (títulos con modos SMART/WORD/STRICT), seniority (founder/c_suite/vp/director/manager/senior...), location, departmentAndFunction, keyword. Paginación `page`/`size` (máx 100), responde `totalElements` y `trackId`.
- `POST /people/export` — export batch CON email (verificación real-time por BounceBan, SMTP y CATCH_ALL). Async: `size` hasta 10,000, responde `trackId`; resultados por polling a los endpoints de statistics/results por trackId. Refund automático de fallos en ~10h.
- `POST /lists` — listas de exclusión (`people_id`/`company_id`, máx 10,000 items, **expiran a las 24h** — se recrean por corrida). Se referencian en búsquedas vía `lists.*.exclude`.
- `GET` fetch-credit — saldo de créditos. Consúltalo ANTES de un export grande y repórtalo.
- Sintaxis de filtros: `{any: {include: [...], exclude: [...]}}` = OR; `all` = AND; modos SMART/WORD/STRICT en campos de texto.
- Ejecuta llamadas con `scripts/aiark.py` (subcomandos: `credit`, `companies`, `people`, `export`, `results`, `exclude-list`).

## Flujo (contrato universal: inferir → confirmar → muestra → escalar)

### 1. Inferir los filtros — preguntar solo lo que falta
Del buyer map / segmento / lo que el usuario pidió, arma el JSON de filtros. Pregunta ÚNICAMENTE lo que no puedas inferir (típico: geografía, rango de headcount, ¿empresas o personas primero?). Si el usuario trae dominios de referencia → usa `lookalikeDomains` directo.

### 2. Confirmar dirección con números reales
Corre UNA búsqueda (page 0) y presenta: los filtros en tabla legible + `totalElements` + tu lectura ("~4,200 personas; ¿apretamos con seniority o así?"). **Espera aprobación.** Ajusta y repite hasta que el tamaño y el perfil cuadren.

### 3. Muestra de aprobación
Trae `defaults.sample_size` resultados y muéstralos en tabla (nombre, título, empresa, tamaño, ubicación). El usuario marca lo que no encaja → traduce cada corrección a filtro (ej. "estos son consultores, no operadores" → exclude en industries/keyword) y re-muestra. **Dos rondas sin correcciones = filtros bloqueados.**

### 4. Dedupe ANTES de exportar
Si `defaults.dedupe.against_outreach_log`: consulta Supabase (`outreach_log` + `v_last_contact` del workspace), y sube dominios/IDs ya contactados como lista de exclusión (`exclude-list`). Reporta cuántos se excluyeron.

### 5. Export con email
Reporta créditos disponibles + tamaño del job y **confirma una última vez**. Lanza el export (respetando `export.max_size`; si la lista es mayor, jobs por tandas), haz polling cada `poll_seconds`, y baja resultados. Si `export.verified_only`: filtra a `SMTP`; deja CATCH_ALL en un CSV aparte marcado.

### 6. Artefacto
Normaliza al `csv_schema` de la config (source=`aiark`) y escribe `lists/<workspace>/<YYYY-MM-DD>-<slug>.csv` + `-REPORT.md` con: filtros finales (JSON reproducible), totales, % verificados, excluidos por dedupe, créditos gastados, y estado **aprobado**. Este CSV es lo que consumen `gtm-check-contact`/`gtm-personalize`/launch.

## Al terminar (contrato de memoria)
- Registra en `LEARNINGS.md`: qué filtros/modos dieron señal limpia, correcciones del usuario textuales (ej. "en logística MX el título real es 'Gerente de Tráfico', no 'Operations Manager'"), y sorpresas de la API.
