# Rubric GTM company profile v1

Clasificar usando solo `clean_text`. No navegar, no usar conocimiento externo y no asumir
ticket. La pregunta de B2B y la de fit outbound son independientes.

## Salida

Devolver un array JSON y nada más. Un objeto por dominio:

```json
{
  "domain": "example.com",
  "entity_type": "company|government|education|nonprofit|media_or_directory|unclear",
  "business_model": "b2b|b2c|mixed|noncommercial|unclear",
  "confidence": "high|medium|low",
  "b2b_line_present": true,
  "sells": "máximo 18 palabras o null",
  "primary_customer": "máximo 20 palabras o null",
  "probable_icp": {
    "company_type": "string o null",
    "industries": ["solo industrias explícitas"],
    "buyer": "rol explícito o inferencia funcional prudente, o null",
    "geography": ["solo geografías explícitas"]
  },
  "sales_economics": "strong|plausible|weak|not_applicable|unclear",
  "outbound_fit": "high|medium|low|unclear",
  "outbound_scope": "companywide|b2b_line_only|none|unclear",
  "outbound_reason": "máximo 25 palabras",
  "evidence": ["máximo dos citas literales exactas"]
}
```

Usar `null` cuando no hay valor y `[]` cuando no hay elementos demostrables.

## Modelo de negocio

- `b2b`: la oferta principal se vende a organizaciones para operar, producir o crecer.
- `b2c`: la oferta principal se dirige a individuos para uso personal.
- `mixed`: existen ofertas comerciales sustanciales para organizaciones e individuos.
- `noncommercial`: organismo público o institución sin oferta comercial demostrable.
- `unclear`: texto insuficiente, placeholder, sitio roto o propuesta indescifrable.

Reglas de frontera:

1. Identificar quién **paga o contrata**, no solo quién usa, participa o aparece en el sitio.
2. Candidatos en un sitio de reclutamiento no vuelven B2C al negocio. Solo usar `mixed` si
   hay una oferta explícita para la persona, no una bolsa de trabajo gratuita.
3. Reclutar agentes, distribuidores, comisionistas, franquiciados o emprendedores
   individuales no es B2B por llamarlos “empresarios”. Sin una oferta comprada por una
   organización, clasificar la captación como individual.
4. Una frase genérica como “personas y empresas” no demuestra línea B2B. Exigir producto,
   caso de uso o sección empresarial concreta.
5. Una línea B2B menor no vuelve `mixed` a un sitio dominado por consumo. Registrar
   `b2b_line_present=true` y `outbound_scope=b2b_line_only` solo si la línea es concreta.
6. Gobierno, educación y nonprofits no son B2B por servir organizaciones. Si no venden una
   oferta comercial, usar `noncommercial`.
7. En medios, directorios y sitios de contenido, la audiencia no es necesariamente el
   cliente. Si el texto no demuestra quién paga —suscriptor, anunciante, afiliado o empresa
   listada— usar `business_model=unclear`, aunque el contenido hable a consumidores.

## Economía comercial

Esto es un proxy prudente del posible valor de venta; nunca producir montos.

- `strong`: el texto demuestra al menos una economía de compra compleja: implementación o
  integración; ingeniería/equipo industrial; financiamiento; outsourcing, nómina o BPO;
  plataforma recurrente; cumplimiento regulado; operación multi-sitio; contrato o proyecto
  claramente sustancial.
- `plausible`: B2B especializado o consultivo con ICP útil, pero sin evidencia suficiente
  de escala, recurrencia o complejidad económica.
- `weak`: consumo, commodity, autoservicio, captación de individuos, oportunidad por
  comisión o servicio pequeño sin señal empresarial concreta.
- `not_applicable`: entidad no comercial.
- `unclear`: no hay información para juzgar.

No subir a `strong` solo por decir “personalizado”, por años de experiencia, testimonios o
número de clientes.

## Fit outbound

- `high`: línea B2B clara, cuenta objetivo identificable, necesidad operativa y economía
  `strong` o `plausible` que soporta una conversación consultiva.
- `medium`: existe línea B2B real, pero el ICP es genérico, la economía es incierta o esa
  línea es secundaria.
- `low`: B2C, no comercial, captación de individuos o medio/directorio sin una línea B2B
  demostrada. Puede ser `low` aunque el pagador del medio sea `unclear`: basta saber que no
  hay oferta empresarial prospectable.
- `unclear`: el texto es tan insuficiente que ni siquiera permite saber si existe una línea
  B2B.

`outbound_scope`:

- `companywide`: la oferta principal es prospectable B2B.
- `b2b_line_only`: solo una unidad o línea concreta es prospectable.
- `none`: no hay línea B2B prospectable; usarlo también para medios/directorios con audiencia
  conocida pero monetización desconocida.
- `unclear`: no se puede decidir si existe una línea B2B.

## Evidencia y confianza

- Máximo dos citas exactas del `clean_text`; preferir una de oferta y otra de audiencia o
  complejidad.
- `high`: oferta y cliente explícitos.
- `medium`: conclusión razonable con una frontera real.
- `low`: texto delgado o inferencia débil.
