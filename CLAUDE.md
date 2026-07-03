# Unprospect GTM OS

Máquina de cold outbound con memoria (Supabase + Markdown) y auto-aprendizaje.
Este archivo es el mapa; las decisiones de diseño y el esquema de datos viven en [ARCHITECTURE.md](ARCHITECTURE.md).

## El pipeline — 5 etapas

Todo el sistema es este flujo. Cada etapa agrupa sus skills:

### 1. Research — entender el negocio y su mercado
- `/gtm-onboard` — analiza website y fuentes → `workspaces/<ws>/PROFILE.md`
- `/gtm-pain-segments` — segmentos por dolor observable → `SEGMENTS.md` + Supabase

### 2. List building — conseguir los leads correctos
- `/gtm-lists` — **el punto de entrada**: elige proveedor, garantiza dedupe y control de calidad
- `/gtm-lists-aiark` — AI Ark: búsqueda + lookalikes nativos + export con email verificado
- `/gtm-prospeo` — Prospeo: buscar (hasta 25K con crawl por estado) o enriquecer un CSV
- `/gtm-ocean` — Ocean.io: lookalikes semánticos desde 3–10 dominios seed (créditos duros)
- `/gtm-check-contact` — dedupe contra Supabase. **SIEMPRE antes de exportar o contactar.**

### 3. Copywriting — qué decir
- `/gtm-offer-ideation` — front-end offers por segmento → `OFFERS.md`
- `/gtm-campaign-ideation` — ángulos (segmento × dolor × offer) → `ANGLES.md` + `BRIEF.md`
- `/gtm-experiments` (modo diseñar) — matriz del A/B de dolor antes de escribir
- `/gtm-copy` — copy por framework, variantes A/B por hipótesis de dolor → `COPY.md`

### 4. Campaign launch — enviar y registrar
- Pendiente `/gtm-launch`. Hoy: CSV + copy a Instantly a mano, y registrar **todo** envío
  en `outreach_log` (`scripts/instantly_sync.py`). Si no está en el log, no pasó.

### 5. Campaign feedback — aprender
- `/gtm-reply-analysis` — clasifica replies, liga reply → ángulo → dolor
- `/gtm-experiments` (modo evaluar) — aplica el criterio pre-registrado, declara ganador o "sin señal"
- `/gtm-retro` — destila el ciclo en los `LEARNINGS.md` (workspace y skills)

## Contrato de memoria (aplica a TODO skill gtm-*)

- **Al empezar:** lee el `LEARNINGS.md` del propio skill y el `PROFILE.md` + `LEARNINGS.md` del workspace activo.
- **Al terminar:** todo hallazgo, decisión o corrección del usuario se registra con fecha.
  Lo específico del cliente → `workspaces/<ws>/LEARNINGS.md`. Lo transferible entre clientes → el `LEARNINGS.md` del skill.
- Workspace default: `unprospect`. Cliente nuevo = copiar `workspaces/_template/` y correr `/gtm-onboard`.

## Contrato de aprobación (todo lo que gasta créditos o manda emails)

Inferir primero, preguntar solo lo que falta → confirmar dirección con números reales →
muestra pequeña → correcciones del usuario (cada una se traduce a filtro/regla) →
dos rondas limpias → recién entonces escalar.

## Reglas duras

- Nada se contacta sin pasar por `/gtm-check-contact`.
- Todo envío se refleja en `outreach_log` — es la fuente de verdad del dedupe.
- Configuración de proveedores en `config/providers.yaml` — nunca hardcodear keys, límites ni tamaños.
- El A/B testea **hipótesis de dolor**, no cosméticos (subject/CTA/largo se mantienen constantes).
- Segmentamos por dolor **observable** (atributos estructurales visibles hoy), no por señales de intención (funding, contrataciones).
