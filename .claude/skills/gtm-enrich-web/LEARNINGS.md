# LEARNINGS — gtm-enrich-web

## 2026-07-08 — Piloto SOFOMes (20 empresas, tabla `sofoms`)
Resultado: 13 found / 6 partial / 1 🟣 not_found, en 2 rondas (4 agentes de 5 + 1 verificador con 9 dudas).

- **El curl del sandbox NO sirve como prueba de vida**: el proxy bloquea sitios grandes (banorte.com, ford.mx, consupago.com dieron 000 estando vivos). La liveness la debe juzgar el agente verificador por el índice de búsqueda (snippets frescos, portales activos, menciones recientes), no curl. Un 403/500 sí significa vivo (bot protection).
- **SOFOMes de grupo financiero (E.R.) casi nunca tienen web ni LinkedIn propios**: viven dentro del sitio del grupo (afirme.com, mifel.com.mx, ford.mx/ford-credit) y el LinkedIn correcto suele ser el del grupo o no existir. `partial` es el resultado esperado, no un fallo.
- **LinkedIn auto-generado ≠ página real**: slugs con la razón social completa y ~6 followers suelen ser stubs sin reclamar (caso GM Financial). Preferir la página reclamada con empleados/posts aunque sea la global.
- **Las empresas del padrón pueden estar muertas**: Finanmadrid seguía inscrita en SIPRES pero está en liquidación (CIBanco). Señales: DNS NXDOMAIN, último snapshot de Wayback viejo, cartera transferida. Eso es 🟣 not_found legítimo y es información valiosa (no contactar).
- **Queries que funcionaron**: razón social entre comillas + "SOFOM"; sitio del regulador/estados financieros hospedados en el dominio candidato confirman pertenencia mejor que el homepage; el aviso de privacidad es donde vive la razón social.
- Costo aprox. del piloto: ~290K tokens de subagentes para 20 empresas (≈14.5K/empresa) y ~12 min de reloj con 4 agentes en paralelo.
