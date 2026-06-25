-- Fase B (segmentación) — vertical canónica "broad".
--
-- Consolida las ~2,332 etiquetas crudas de parallel_cat.vertical (texto libre)
-- en una taxonomía cerrada de ~18 verticales, y clasifica también las empresas
-- sin dominio a partir de su industria de LinkedIn. Ver db/enrich/classify_verticals.py.
alter table companies add column if not exists vertical_broad text;

comment on column companies.vertical_broad is
  'Vertical canónica (taxonomía cerrada). Consolidada de parallel_cat.vertical (clasificada por subagentes) y, para empresas sin dominio, de la industria de LinkedIn. Ver db/enrich/classify_verticals.py.';
