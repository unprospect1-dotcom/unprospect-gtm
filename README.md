# unprospect-gtm

Go-to-market OS para Unprospect — una máquina de cold outbound con memoria y auto-aprendizaje.

- **[CLAUDE.md](CLAUDE.md)** — el mapa: pipeline de 5 etapas (research → list building → copywriting → launch → feedback), skills y contratos.
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — decisiones de diseño, esquema de Supabase y roadmap.

## Clasificación local de empresas

Clasifica empresas de Supabase en subsegmentos de logística (requiere `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`):

```bash
python segment_companies.py      # → segment_results.json / .csv
python subagent_workflow.py     # → subagent_results.json
python -m unittest discover -s tests -p "test_*.py"
```
