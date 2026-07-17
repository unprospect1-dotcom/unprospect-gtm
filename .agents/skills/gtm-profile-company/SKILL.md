---
name: gtm-profile-company
description: Perfila empresas desde clean_text para clasificar B2B, oferta, cliente, ICP probable y fit outbound con dos pasadas ciegas.
---

# Adaptador Codex

1. Lee completo `.claude/skills/gtm-profile-company/SKILL.md`.
2. Lee `docs/CODEX-COMPATIBILITY.md` y aplica sus equivalencias de harness.
3. Resuelve recursos y scripts contra `.claude/skills/gtm-profile-company/`.
4. Usa las lanes Mini de `.codex/agents/gtm_profile_*.toml` para lotes paralelos baratos.
5. No dupliques lógica canónica en este adaptador.
