# LEARNINGS — gtm-enrich-web

## 2026-07-09 — Corrida completa dominio-only (2,177 SOFOMes, tabla `sofoms`)
Pipeline de 3 capas ejecutado en escala real. Resultado final: **1,302 found / 843 🟣 not_found / 26 defunct / 6 partial (piloto)**, con 28 ligadas por dominio a `companies`. Costo Parallel ≈ $11 USD.

- **Distribución de trabajo entre capas (validó el diseño)**: Parallel `lite` barrió las 2,157 en ~3h (11/min, 12 threads, ~$5/1k). El triage automático aceptó directo **1,247** y mandó solo **55** (2.5%) a subagentes. De esos 55, los subagentes confirmaron el candidato de Parallel en ~60%, lo **corrigieron en ~25%** y lo tiraron a 🟣 en ~15%.
- **El error #1 de Parallel a escala NO es inventar, es dar el dominio de OTRA empresa del mismo giro/nombre**: hipoprestamo.com (era de Auropresto), multilateralmexico.com (FIMM), superpromise.mx (directorio), coinn.com.mx (COIN asesoría), gruposim.com.mx (Grupo SIM RH), fpc.com.mx (válvulas), centum.mx (fintech de pagos), capitalfundinglab.com (crowdfunding IFC), capitalx.com.mx (otra SAPI), easyprestamo.top (app genérica). **Todos** los cazó la capa de verificación cruzando razón social contra el contenido del sitio. Sin ese cruce, habríamos metido ~12 dominios equivocados a la base.
- **El content_check (curl + match de tokens/razón social) es un buen COLADOR, no un juez**: generó ~30% de falsos negativos (`no_match`/`unreachable`) por sitios SPA/Angular (paya.com.mx), sub-páginas legales (walmartmexico.com/tesoreria), proxy 503, o marca ≠ razón social (DAE Hipotecaria = Desarrolladora de Alternativas Estratégicas). Sirve para PRIORIZAR qué mandar a subagentes, nunca para descartar un dominio solo.
- **Blacklist de directorios: anclar el dominio, no usar regex de substring**. La v1 con `re.search` marcó falsos positivos absurdos (invex, pretmex, unicredix… porque contenían "mex"/"dex"). Correcto: comparar el root exacto o sufijo `.dominio` contra un set (condusef.gob.mx, mbia.com, sites.google.com, nadbank.org como no-propios, etc.).
- **Casos legítimos de dominio compartido**: sí hay varias SOFOMes distintas que viven en el mismo sitio de grupo y es correcto (inventafinancial.mx aloja 2 razones sociales del grupo Inventa; grupobafar.com aloja Vextor y Sofivext). Un dominio repetido >2 veces es señal de revisar, no de rechazar automáticamente.
- **Límite operativo del plan**: 11 subagentes simultáneos + ~3h de corrida agotó el límite de sesión a media verificación (tumbó 9 lotes). Lección: **olas de máx 6 agentes**, y como los fixresult_N.json se escriben a disco antes de aplicar, un `send_later` reanuda sin perder trabajo. Idempotencia por archivo = barato reanudar.
- **PostgREST**: un bulk upsert con filas de llaves heterogéneas da 400; separar en grupos con el MISMO set de columnas (ej. con/sin matched_company_id). Y usar retry con backoff — hubo ConnectionReset esporádicos.

## 2026-07-08 — Benchmark Parallel Task API vs subagentes (mismas 20 SOFOMes)
- **`lite` vs `base`**: base cuesta 2x ($10 vs $5 /1k) y NO mejora de forma material (dominios 17/20 vs 16/20; LinkedIn 11/20 vs 9/20 de acuerdo con el baseline verificado). **Usar `lite` siempre** para domain+LinkedIn.
- **Sesgo sistemático de Parallel con filiales**: devuelve el dominio/LinkedIn del GRUPO (banregio.com, bb.com.mx, inbursa.com, afirme-financial-group, ford-motor-credit-company) en vez del sitio/página propios de la entidad (startbanregio.com, financierabajio.com.mx, sofom.inbursa.com…). Las 4 discrepancias de dominio del benchmark se resolvieron TODAS a favor de los subagentes. → filiales de grupo: directo a capa de subagentes.
- **Parallel también da aliases no canónicos** (gmfinancial.mx que redirige a gmfinancial.com.mx). El triage debe seguir redirects para canonicalizar.
- **En lo que sí coincide, coincide bien**: 16/20 dominios con lite en el PEOR segmento posible (E.R. corporativas). En E.N.R. independientes se espera tasa de aceptación directa mucho mayor.
- **Parallel detectó igual que nosotros que Finanmadrid está muerta** (null/null) — el campo `company_alive` del schema funciona como señal.
- Costo real del benchmark: 40 runs (20 lite + 20 base) ≈ $0.30 USD, ~2 min por ronda con 10 threads.

## 2026-07-08 — Piloto SOFOMes (20 empresas, tabla `sofoms`)
Resultado: 13 found / 6 partial / 1 🟣 not_found, en 2 rondas (4 agentes de 5 + 1 verificador con 9 dudas).

- **El curl del sandbox NO sirve como prueba de vida**: el proxy bloquea sitios grandes (banorte.com, ford.mx, consupago.com dieron 000 estando vivos). La liveness la debe juzgar el agente verificador por el índice de búsqueda (snippets frescos, portales activos, menciones recientes), no curl. Un 403/500 sí significa vivo (bot protection).
- **SOFOMes de grupo financiero (E.R.) casi nunca tienen web ni LinkedIn propios**: viven dentro del sitio del grupo (afirme.com, mifel.com.mx, ford.mx/ford-credit) y el LinkedIn correcto suele ser el del grupo o no existir. `partial` es el resultado esperado, no un fallo.
- **LinkedIn auto-generado ≠ página real**: slugs con la razón social completa y ~6 followers suelen ser stubs sin reclamar (caso GM Financial). Preferir la página reclamada con empleados/posts aunque sea la global.
- **Las empresas del padrón pueden estar muertas**: Finanmadrid seguía inscrita en SIPRES pero está en liquidación (CIBanco). Señales: DNS NXDOMAIN, último snapshot de Wayback viejo, cartera transferida. Eso es 🟣 not_found legítimo y es información valiosa (no contactar).
- **Queries que funcionaron**: razón social entre comillas + "SOFOM"; sitio del regulador/estados financieros hospedados en el dominio candidato confirman pertenencia mejor que el homepage; el aviso de privacidad es donde vive la razón social.
- Costo aprox. del piloto: ~290K tokens de subagentes para 20 empresas (≈14.5K/empresa) y ~12 min de reloj con 4 agentes en paralelo.
