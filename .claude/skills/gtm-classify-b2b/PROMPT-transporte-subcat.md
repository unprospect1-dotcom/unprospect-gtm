# Rubro: subcategoría de empresas del universo transporte/logística MX

Clasificas empresas leyendo SOLO el `clean_text` de su sitio. Sin conocimiento de marca,
sin navegar. Una etiqueta por dominio.

## Etiquetas (exactamente una)

- `flota-carga` — transportista terrestre de carga con flota propia como negocio central
  (FTL/LTL, caja seca, plataforma, volteo, líquidos, oversize, HAZMAT, mudanzas). Si además
  ofrece refrigerado como UNO MÁS de sus equipos, sigue siendo flota-carga.
- `refrigerado` — la cadena de frío ES el negocio central: flota refrigerada dominante,
  almacén frío/congelado, farma/perecederos con temperatura controlada. No basta mencionarlo.
- `forwarder-aduanal` — agencia de carga / freight forwarder / agencia aduanal / comercio
  exterior: coordina embarques multimodales (marítimo/aéreo/terrestre) y/o despacho aduanal;
  la flota propia no es el centro (puede tener unidades de apoyo).
- `3pl-almacen` — logística integral tercerizada: almacenaje, fulfillment, distribución,
  inventarios, maquila logística; bodegas como activo central.
- `paqueteria` — mensajería, paquetería, last-mile, envíos exprés multi-cliente.
- `software-transporte` — SaaS, TMS, plataforma o marketplace para el sector transporte/logística.
- `pasajeros` — transporte de personas: personal, turístico, taxis, shuttles, rentas con chofer.
- `proveedor-del-sector` — le VENDE al transporte: carrocerías/remolques, refacciones, llantas,
  GPS/telemetría, seguros de carga, combustible, racks, montacargas, capacitación.
- `no-transporte` — nada que ver con transporte/logística (inmobiliaria, cámara empresarial,
  alimentos, muebles, etc.).
- `sin-sitio` — placeholder (parked/wix/hostinger), en construcción, error, hackeado/spam,
  o clean_text vacío/inútil.

## Reglas de desempate

1. Manda el NEGOCIO CENTRAL descrito, no menciones de pasada ni listas de servicios genéricas.
2. flota-carga vs forwarder-aduanal: ¿describe SUS unidades/flota/rutas (flota-carga) o
   coordina embarques de terceros y trámites (forwarder-aduanal)? Si hace ambos con peso real,
   gana el que abra el sitio / domine la descripción.
3. refrigerado exige frío como identidad (nombre, hero, mayoría de servicios); si es un equipo
   más en la lista → flota-carga (anota el frío en evidence).
4. 3pl-almacen vs forwarder: bodegas/inventario/fulfillment → 3pl; embarques/aduanas → forwarder.
5. Empresa de transporte con sitio pobre pero identificable → clasifícala con confidence low;
   texto inútil de verdad → sin-sitio.
6. El objeto social/aviso de privacidad NO cuenta como descripción del negocio.
7. confidence: high (evidencia explícita), med (inferible), low (débil/ambiguo).

## Formato de salida (una línea JSON por dominio)

{"domain": "...", "subcat": "<etiqueta>", "confidence": "high|med|low",
 "evidence": "<cita textual corta del clean_text>", "reason": "<una frase>"}
