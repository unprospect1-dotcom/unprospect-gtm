# GetLeads.io — Referencia de API (extraída del bundle de getleads.io, 2026-07-11)

> No hay docs públicas navegables; esto viene embebido en su SPA. Verificado en vivo: auth, /contacts/health, /contacts/search/count.
> Rate limit: 100 req/min global. Créditos: 1 por registro devuelto/ítem exitoso; counts y filter-values GRATIS.

REST endpoints for enrichment and contacts lookup, plus MCP tools for Cursor and Claude. All routes except `GET /api/health` require your `glb_live_…` API key. Credits: one per item where `success` is `true`. Install the terminal client: `npm install -g @getleads/cli`.

---

## Getting started

### Authentication

Send your key in either form (pick one per request):

```http
Authorization: Bearer glb_live_<keyId>_<secret>
X-API-Key: glb_live_<keyId>_<secret>
```

Revoked keys receive `401`.

### Rate limits

Accounts default to **100 requests per minute** across all endpoints; requests beyond that return `429` — back off and retry after a moment. Integrating at higher volume? Message us and we'll raise your account's limit (we routinely set 5 req/s and can go higher). Note the request rate is separate from processing throughput: batch endpoints accept up to 100 items per request, so e.g. enrichment sustains ~10,000 records/min well within the default limit.

### Field naming

JSON requests use `snake_case` for person and URL fields (`first_name`, `linkedin_url`). JSON responses add `camelCase` convenience keys (`linkedinUrl`, `profileUrl`) plus a `data` object whose keys mirror the enrichment provider (often `snake_case`, e.g. `email_address`, `person_linkedin_url`).

### Common mistakes

- Work emails → `POST /api/v1/enrich/from-email` with `{ "email" }`, not `/from-linkedin`.
- LinkedIn URLs → `POST /api/v1/enrich/from-linkedin` with `{ "linkedin_url" }`, not `/from-email`.

### HTTP errors

Error body (JSON, typical):

```json
{
  "ok": false,
  "message": "Provide at least one item with linkedin_url.",
  "creditsRemaining": 1234
}
```

`creditsRemaining` is included on some `402` responses; omitted otherwise.

| Status | Meaning |
| --- | --- |
| `401` | Missing, malformed, or revoked API key. |
| `402` | Not enough credits (worst-case for the request). |
| `400` | Invalid body, CSV shape, or batch over limit. |
| `429` | Rate limit exceeded (default 100 requests/min per account — see Rate limits). Back off and retry. |
| `502` | Enrichment provider error or timeout. |
| `503` | Contact database unavailable (contacts) or funding store empty / not configured. |

---

## Health

### `GET /api/health`

No API key. Returns JSON such as `{ "ok": true, "enrichBundleId": "…" }` with `Cache-Control: no-store`.

```bash
curl -sS "https://app.getleads.io/api/health"
```

### `GET /api/v1/contacts/health`

Requires API key. Pings the contact database and returns connection status plus approximate `releases` row count when healthy.

```bash
curl -sS "https://app.getleads.io/api/v1/contacts/health" 
  -H "Authorization: Bearer $GETLEADS_API_KEY"
```

---

## Person enrichment — 3 ways

Choose the workflow that matches what you already know about each person. Each path has a JSON batch endpoint for programmatic use and a CSV upload on the same route with a different `mode`. Successful lookups return full provider fields in `data` (JSON) or `enriched_*` columns (CSV).

| # | You have | JSON endpoint | CSV mode |
| --- | --- | --- | --- |
| 1 | Work email | `POST /api/v1/enrich/from-email` | `work_email` (alias `email`) |
| 2 | LinkedIn profile URL | `POST /api/v1/enrich/from-linkedin` | `linkedin` (default; alias `profile`) |
| 3 | First + last name + company or domain | `POST /api/v1/enrich/from-person` | `person` |

CSV uploads for all three modes use `POST /api/v1/enrich/csv` with `mode` set as above.

---

### 1. From work email

Start with a known work email. Returns LinkedIn URL and all scalar fields the provider sends (title, company, name, etc.).

#### JSON batch — `POST /api/v1/enrich/from-email`

JSON array of work emails. One credit per item where `success` is `true`. `creditsRemaining` may be `null` on unlimited plans.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `items` | array | Yes | Each element must include `email` (string). |

Request body (JSON):

```json
{
  "items": [
    { "email": "jane@acme.com" },
    { "email": "bob@example.com" }
  ]
}
```

Response body (200, JSON):

```json
{
  "ok": true,
  "results": [
    {
      "email": "jane@acme.com",
      "success": true,
      "profileUrl": "https://www.linkedin.com/in/janedoe",
      "data": {
        "email_address": "jane@acme.com",
        "person_linkedin_url": "https://www.linkedin.com/in/janedoe",
        "first_name": "Jane",
        "last_name": "Doe"
      }
    },
    {
      "email": "bob@example.com",
      "success": false,
      "profileUrl": null,
      "data": null
    }
  ],
  "creditsRemaining": 4999
}
```

Example request:

```bash
curl -sS -X POST "https://app.getleads.io/api/v1/enrich/from-email" 
  -H "Authorization: Bearer $GETLEADS_API_KEY" 
  -H "Content-Type: application/json" 
  -d '{"items":[{"email":"jane@acme.com"}]}'
```

#### CSV bulk — `POST /api/v1/enrich/csv`

`Content-Type: multipart/form-data` with field `file`, or raw POST with `Content-Type: text/csv` and `mode` / `mapping` on the query string.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `mode` | string | Yes | Set to `work_email` (`email`). |
| `file` | file | Yes | CSV file (multipart) or raw body (`text/csv`). |
| `mapping` | JSON string | Yes | Maps semantic keys to your column headers (see below). |
| `maxRows` | number | No | Optional cap on rows processed (multipart field or `?maxRows=`). |
| `fileName` | string | No | Optional label stored in run history. |

**Column mapping** — map `email` to your work-email column (required). Omit `profileUrl` in mapping to write found LinkedIn URLs to `ProfileURL`.

Example input CSV:

```csv
Work_Email
jane@acme.com
```

Example request (multipart):

```bash
curl -sS -D headers.txt -o enriched.csv -X POST "https://app.getleads.io/api/v1/enrich/csv" 
  -H "Authorization: Bearer $GETLEADS_API_KEY" 
  -F "file=@./contacts.csv" 
  -F "mode=work_email" 
  -F 'mapping={"email":"Work_Email"}'
```

Example response CSV (200, body only):

```csv
Work_Email,ProfileURL,enriched_first_name,enriched_last_name,enriched_email_address
jane@acme.com,https://www.linkedin.com/in/janedoe,Jane,Doe,jane@acme.com
```

**Output columns** — on success, every scalar provider field in `data` becomes an `enriched_*` column (e.g. `enriched_first_name`, `enriched_job_title`). Convenience columns `email` and `ProfileURL` are written when mapped (or use defaults above). Nested objects from the provider are omitted (same as JSON batch `data`).

Successful CSV responses return `200` with body = enriched CSV (not JSON). Headers: `X-Enrich-Total`, `X-Enrich-Succeeded`, `X-Enrich-Skipped`, `X-Enrich-Partial`, `X-Credits-Remaining` (empty when unlimited). Use `curl -D headers.txt` to inspect.

---

### 2. From LinkedIn profile URL

Start with a public LinkedIn profile URL. Returns work email and all provider fields for that person.

#### JSON batch — `POST /api/v1/enrich/from-linkedin`

JSON array of LinkedIn URLs. Optional `limit_per_item` (default 1, max 10). One credit per item where `success` is `true`. `creditsRemaining` may be `null` on unlimited plans.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `items` | array | Yes | Each element must include `linkedin_url` (string). |
| `limit_per_item` | number | No | Matches per URL (default 1, max 10). |

Request body (JSON):

```json
{
  "items": [
    { "linkedin_url": "https://www.linkedin.com/in/example" },
    { "linkedin_url": "https://www.linkedin.com/in/other" }
  ],
  "limit_per_item": 1
}
```

Response body (200, JSON):

```json
{
  "ok": true,
  "results": [
    {
      "linkedinUrl": "https://www.linkedin.com/in/example",
      "success": true,
      "email": "found@company.com",
      "data": {
        "email_address": "found@company.com",
        "person_linkedin_url": "https://www.linkedin.com/in/example",
        "first_name": "Alex",
        "last_name": "Example"
      }
    },
    {
      "linkedinUrl": "https://www.linkedin.com/in/other",
      "success": false,
      "email": null,
      "data": null
    }
  ],
  "creditsRemaining": 4999
}
```

Example request:

```bash
curl -sS -X POST "https://app.getleads.io/api/v1/enrich/from-linkedin" 
  -H "Authorization: Bearer $GETLEADS_API_KEY" 
  -H "Content-Type: application/json" 
  -d '{"items":[{"linkedin_url":"https://www.linkedin.com/in/example"}],"limit_per_item":1}'
```

Batches are capped at 100 items per request; a larger batch returns `400`.

#### CSV bulk — `POST /api/v1/enrich/csv`

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `mode` | string | Yes | Set to `linkedin` (`profile`; omit `mode` for same behavior). |
| `file` | file | Yes | CSV file (multipart) or raw body (`text/csv`). |
| `mapping` | JSON string | No | Maps semantic keys to your column headers. Optional when the CSV header is exactly `profileURL`. |
| `maxRows` | number | No | Optional cap on rows processed (multipart field or `?maxRows=`). |
| `fileName` | string | No | Optional label stored in run history. |

**Column mapping** — map `profileUrl` to the column with LinkedIn URLs (required). Omit `email` in mapping to write found emails to `email`. You can omit `mapping` when headers are exactly `profileURL`.

Example input CSV:

```csv
profileURL,notes
https://www.linkedin.com/in/example,
```

Example request (multipart):

```bash
curl -sS -D headers.txt -o enriched.csv -X POST "https://app.getleads.io/api/v1/enrich/csv" 
  -H "Authorization: Bearer $GETLEADS_API_KEY" 
  -F "file=@./contacts.csv" 
  -F "mode=linkedin" 
  -F 'mapping={"profileUrl":"profileURL"}'
```

Example response CSV (200, body only):

```csv
profileURL,email,enriched_first_name,enriched_last_name
https://www.linkedin.com/in/example,found@company.com,Alex,Example
```

Output columns and response headers match the [from-email CSV route](#csv-bulk--post-apiv1enrichcsv).

---

### 3. From name + company

Start with first name, last name, and either company name or email domain. Returns work email, LinkedIn URL, and full provider data when found.

#### JSON batch — `POST /api/v1/enrich/from-person`

JSON array of person records. Each item needs `first_name`, `last_name`, and at least one of `company_name` or `email_domain`. Same batch size cap as other batch routes (100 items per request). `creditsRemaining` may be `null` on unlimited plans.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `items` | array | Yes | Each element: `first_name`, `last_name`, and `company_name` and/or `email_domain` (non-empty strings). |

Request body (JSON):

```json
{
  "items": [
    {
      "first_name": "Jane",
      "last_name": "Doe",
      "company_name": "Acme Inc"
    },
    {
      "first_name": "Bob",
      "last_name": "Smith",
      "email_domain": "example.com"
    }
  ]
}
```

Response body (200, JSON):

```json
{
  "ok": true,
  "results": [
    {
      "first_name": "Jane",
      "last_name": "Doe",
      "company_name": "Acme Inc",
      "success": true,
      "email": "jane.doe@acme.com",
      "profileUrl": "https://www.linkedin.com/in/janedoe",
      "data": {
        "email_address": "jane.doe@acme.com",
        "person_linkedin_url": "https://www.linkedin.com/in/janedoe",
        "company_name": "Acme Inc"
      }
    },
    {
      "first_name": "Bob",
      "last_name": "Smith",
      "email_domain": "example.com",
      "success": false,
      "email": null,
      "profileUrl": null,
      "data": null
    }
  ],
  "creditsRemaining": 4999
}
```

Example request:

```bash
curl -sS -X POST "https://app.getleads.io/api/v1/enrich/from-person" 
  -H "Authorization: Bearer $GETLEADS_API_KEY" 
  -H "Content-Type: application/json" 
  -d '{"items":[{"first_name":"Jane","last_name":"Doe","company_name":"Acme Inc"}]}'
```

#### CSV bulk — `POST /api/v1/enrich/csv`

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `mode` | string | Yes | Set to `person`. |
| `file` | file | Yes | CSV file (multipart) or raw body (`text/csv`). |
| `mapping` | JSON string | Yes | Maps semantic keys to your column headers (see below). |
| `maxRows` | number | No | Optional cap on rows processed (multipart field or `?maxRows=`). |
| `fileName` | string | No | Optional label stored in run history. |

**Column mapping** — map `firstName`, `lastName`, and `companyName` or `emailDomain` to your columns (company or domain required per row). Default output columns: `email` and `ProfileURL` when not specified in mapping.

Example input CSV:

```csv
First,Last,Company
Jane,Doe,Acme Inc
```

Example request (multipart):

```bash
curl -sS -D headers.txt -o enriched.csv -X POST "https://app.getleads.io/api/v1/enrich/csv" 
  -H "Authorization: Bearer $GETLEADS_API_KEY" 
  -F "file=@./contacts.csv" 
  -F "mode=person" 
  -F 'mapping={"firstName":"First","lastName":"Last","companyName":"Company"}'
```

Example response CSV (200, body only):

```csv
First,Last,Company,email,ProfileURL,enriched_first_name,enriched_last_name,enriched_job_title
Jane,Doe,Acme Inc,jane.doe@acme.com,https://www.linkedin.com/in/janedoe,Jane,Doe,VP Sales
```

Output columns and response headers match the [from-email CSV route](#csv-bulk--post-apiv1enrichcsv).

#### `POST /api/v1/enrich/csv` — single CSV route

Set `mode` to match your input columns:

- `work_email` or `email` — see [From work email](#1-from-work-email)
- `linkedin` or `profile` — see [From LinkedIn profile URL](#2-from-linkedin-profile-url)
- `person` — see [From name + company](#3-from-name--company)

---

## Contacts lookup

Phone uses the contact database; colleagues uses the same contact search as Database search. Credits: 1 per phone match found; for colleagues, 1 per record returned; 0 if none.

### `GET /api/v1/contacts/lookup/phone`

Query param `phone` or `cellphone`. Returns the full `releases` row in `data` when found; `success: false` with no charge when not found.

Example response (found):

```json
{
  "ok": true,
  "success": true,
  "data": {
    "first_name": "Steve",
    "last_name": "Neu",
    "email_address": "steve@payheremarketing.com",
    "cellphone": "+1 803-520-0590",
    "domain_org": "payheremarketing.com"
  },
  "creditsRemaining": 4999
}
```

Example request:

```bash
curl -sS "https://app.getleads.io/api/v1/contacts/lookup/phone?phone=%2B1+803-520-0590" 
  -H "Authorization: Bearer $GETLEADS_API_KEY"
```

### `POST /api/v1/contacts/from-phone`

JSON batch lookup (same pattern as `POST /api/v1/enrich/from-email`). Each item accepts `phone` or `cellphone`. US phones are stored as `+1 XXX-XXX-XXXX` (space after country code). Optional `limit_per_item` (default 1, max 10).

Request body:

```json
{
  "items": [
    { "phone": "+1 803-520-0590" },
    { "cellphone": "5551234567" }
  ],
  "limit_per_item": 1
}
```

Example response:

```json
{
  "ok": true,
  "results": [
    {
      "phone": "+1 803-520-0590",
      "success": true,
      "data": { "first_name": "Steve", "cellphone": "+1 803-520-0590" }
    },
    {
      "phone": "5551234567",
      "success": false,
      "data": null
    }
  ],
  "creditsRemaining": 4998
}
```

Example request:

```bash
curl -sS -X POST "https://app.getleads.io/api/v1/contacts/from-phone" 
  -H "Authorization: Bearer $GETLEADS_API_KEY" 
  -H "Content-Type: application/json" 
  -d '{"items":[{"phone":"+1 803-520-0590"},{"phone":"5550000000"}],"limit_per_item":1}'
```

### `POST /api/v1/contacts/lookup/colleagues`

Find people at a company using a company email domain (e.g. `acme.com`). Queries the GetLeads contact database — same data as search. Defaults to verified emails only. Returns contacts with pagination (`has_more`, `next_offset`). One credit per record returned; 0 if none. Default `limit_per_item` 100 (max 5000). For very large lists, use search export with the same domain filter.

Request body:

```json
{
  "email_domain": "tabby.ai",
  "limit_per_item": 100,
  "offset": 0
}
```

Example response:

```json
{
  "ok": true,
  "contacts": [ "…" ],
  "total_available": 842,
  "query_credits_used": 100,
  "creditsRemaining": 4900,
  "offset": 0,
  "limit": 100,
  "returned": 100,
  "has_more": true,
  "next_offset": 100,
  "normalized_inputs": { "email_domain": "tabby.ai" }
}
```

Example request:

```bash
curl -sS -X POST "https://app.getleads.io/api/v1/contacts/lookup/colleagues" 
  -H "Authorization: Bearer $GETLEADS_API_KEY" 
  -H "Content-Type: application/json" 
  -d '{"email_domain":"tabby.ai","limit_per_item":100}'
```

### `POST /api/v1/contacts/lookup/decision-makers`

Find decision makers at a company using GetLeads database search. Matches contacts with seniority `C-Team`, `VP`, or `Director`, or any job title containing `Head` (e.g. Head of Growth, Department Head). Provide `domain` or `company_name`, not both. Defaults to verified emails only. Up to 5000 records per request (default 5000); use `offset` for the next page. 1 credit per record returned; 0 if none.

Request body:

```json
{
  "domain": "acme.com",
  "limit": 5000,
  "offset": 0,
  "require_email": true
}
```

Example request:

```bash
curl -sS -X POST "https://app.getleads.io/api/v1/contacts/lookup/decision-makers" 
  -H "Authorization: Bearer $GETLEADS_API_KEY" 
  -H "Content-Type: application/json" 
  -d '{"domain":"acme.com","limit":10}'
```

---

## Database search

Queries the GetLeads contact index (~370M+ rows). Phone lookup uses the contacts database only. Search costs 1 credit per record returned; 0 if none; counts and filter values are free.

### `POST /api/v1/contacts/search`

Filtered search over the contact index. Up to 50,000 records per request (default 1000). Paginate with `offset` until `has_more` is `false`, or use `POST /api/v1/contacts/search/export` for a full CSV on S3. Pass filters in a nested `filters` object or as top-level keys — both work. All filter fields are combined with AND logic. Optional `limit` (default 1000, max 50,000), `offset` (default 0), and `max_per_company` (1–50) sit at the top level. Responses include `has_more` and `next_offset` for pagination. `total_available` in the response is a pagination hint bounded by the per-request window (it carries `total_available_is_minimum: true` when more rows match) — for the true match count use `POST /api/v1/contacts/search/count`.

Minimal request body:

```json
{
  "filters": {
    "domains": ["acme.com"],
    "seniority": ["C-Team"],
    "countries": ["United States"]
  },
  "max_per_company": 3
}
```

Richer example (multiple filter groups):

```json
{
  "filters": {
    "domains": ["acme.com", "globex.com"],
    "seniority": ["C-Team", "VP"],
    "job_titles": ["Sales"],
    "countries": ["United States"],
    "email_status": ["VALID"],
    "exclude_domains": ["competitor.com"],
    "require_phone": true
  },
  "max_per_company": 3
}
```

Seniority aliases: `C-Suite`, `C-Level`, and `Executive` map to `C-Team`; `Vice President`, `SVP`, and `EVP` map to `VP`. See `GET /filter-values` for allowed enum values.

#### Company targeting

| Field | Type | Description |
| --- | --- | --- |
| `domains` | string[] | Company website domains (e.g. `acme.com`, `globex.com`). |
| `company_name` | string | Company name substring match on `org_company_name`. |
| `email_domain` | string | Email domain filter (e.g. `gmail.com`). Comma-separated values OK. |
| `domain_list_id` | string | Saved domain list id (`fv_…` or `@fvid:…`). |

#### Role

| Field | Type | Description |
| --- | --- | --- |
| `job_titles` | string[] | Job title keywords — substring match (e.g. `["CEO", "Engineer"]`). |
| `seniority` | string[] | Job level: `C-Team`, `VP`, `Director`, `Manager`, `Staff`, `Other`. Aliases normalized (`C-Suite` → `C-Team`). |
| `job_functions` | string[] | Department: `Sales & Business Development`, `Engineering`, `Information Technology`, etc. |
| `personas` | string[] | Buyer personas (e.g. `CEO / Founder`, `CTO`, `DevOps`). |

#### Company firmographics

| Field | Type | Description |
| --- | --- | --- |
| `industries` | string[] | LinkedIn industries (515 categories). |
| `company_size_min` | number | Minimum employees — server maps to employee count ranges. |
| `company_size_max` | number | Maximum employees — server maps to employee count ranges. |
| `revenue` | string[] | Revenue ranges: `<$1M`, `$1M to <$10M`, `$10M to <$50M`, `$50M to <$100M`, `$100M to <$1B`, `$1B+`. |
| `headquarters_countries` | string[] | Company HQ country (`headquarters_country_name`). Use `GET /filter-values?field=headquarters_countries` for valid values. |
| `company_description` | string | Substring search on company about text (`org_about_us`). |
| `entity_types` | string[] | Legal entity type (`Public Company`, `Privately Held`, `Non Profit`, …). Use `field=entity_types` for values. |
| `technologies` | string[] | Technologies/tools the company uses (e.g. `Salesforce`, `HubSpot`). Matches across all technographic fields. |
| `has_mobile_app` | boolean | Only companies that have (`true`) / do not have (`false`) a mobile app. |
| `has_web_app` | boolean | Only companies that have (`true`) / do not have (`false`) a web application. |

#### Company numeric ranges

Numeric min/max bounds. `employees_*`/`revenue_*` use range overlap; the rest filter a single value.

| Field | Type | Description |
| --- | --- | --- |
| `employees_min` | number | Minimum exact employee count. |
| `employees_max` | number | Maximum exact employee count. |
| `revenue_min` | number | Minimum revenue in USD. |
| `revenue_max` | number | Maximum revenue in USD. |
| `followers_min` | number | Minimum LinkedIn followers. |
| `followers_max` | number | Maximum LinkedIn followers. |
| `founded_year_min` | number | Earliest founding year. |
| `founded_year_max` | number | Latest founding year. |
| `total_funding_min` | number | Minimum total funding raised (USD). |
| `total_funding_max` | number | Maximum total funding raised (USD). |
| `monthly_traffic_min` | number | Minimum total monthly web traffic. |
| `monthly_traffic_max` | number | Maximum total monthly web traffic. |

#### Person location

| Field | Type | Description |
| --- | --- | --- |
| `countries` | string[] | Person's country (`person_country_name`). |
| `regions` | string[] | Macro-regions: `NORAM`, `EMEA`, `APAC`, `LATAM`. |
| `continents` | string[] | `North America`, `Europe`, `Asia`, `South America`, `Africa`, `Oceania`, `Antarctica`. |
| `cities` | string[] | Person's city — substring match. |
| `states` | string[] | Person's state/province — substring match. |

#### Job location (office, not home address)

Where the role is based — not the person's home location. Use `countries`/`cities`/`states` above for person location.

| Field | Type | Description |
| --- | --- | --- |
| `job_location_country` | string[] | Country where the company/office is located. |
| `job_location_state` | string[] | State/province where the office is located — substring match. |
| `job_location_city` | string[] | City where the office is located — substring match. |

#### Person identity

| Field | Type | Description |
| --- | --- | --- |
| `first_name` | string | First name — substring match. |
| `last_name` | string | Last name — substring match. |
| `email_address` | string | Specific email address — exact match. |
| `linkedin_url` | string | LinkedIn profile URL — substring match. |
| `person_description` | string | Substring search on person bio (`about_me`). |
| `skills` | string | Substring search on the contact's skills. |

#### Email quality

| Field | Type | Description |
| --- | --- | --- |
| `email_status` | string[] | Verification status enum: `VALID`, `CATCH_ALL`, `INVALID`. Use `["VALID"]` for deliverable emails. Do not send `"verified"`. |
| `require_email` | boolean | Only return contacts with a non-empty `email_address`. |

#### Presence

| Field | Type | Description |
| --- | --- | --- |
| `require_phone` | boolean | Only return contacts with a phone number (`cellphone`). Default `false`. |

#### Excludes

| Field | Type | Description |
| --- | --- | --- |
| `exclude_domains` | string[] | Exclude these company domains. |
| `exclude_countries` | string[] | Exclude these person countries. |
| `exclude_headquarters_countries` | string[] | Exclude these company HQ countries. |
| `exclude_industries` | string[] | Exclude these industries. |
| `exclude_job_titles` | string[] | Exclude contacts whose title contains these keywords. |

#### Search options

Place alongside `filters` at the top level of the request body.

| Field | Type | Description |
| --- | --- | --- |
| `limit` | integer | Max rows this page (default 1000, max 50,000). |
| `offset` | integer | Skip rows for pagination (default 0). Use `next_offset` from the prior response. |
| `max_per_company` | integer | Cap contacts per company (1–50). Use for diverse results across many domains. |
| `columns` | string[] | Output columns by display label or internal name. When omitted, a default set plus any filtered columns is returned. REST JSON keeps raw column names; MCP responses and CSV exports use display labels. |
| `where_sql` | string | Advanced: a raw SQL `WHERE` predicate over the catalog's internal column names, AND-combined with the filters above. Reaches fields that have no dedicated filter — e.g. `"MONTHLY_GOOGLE_ADSPEND_ORG > 0"` matches companies actively running Google Ads. Also accepted by `search/count` and `search/export`. Invalid column names or syntax return `400`. |

Enum values for many list filters: `GET /api/v1/contacts/filter-values?field=…` — supported fields: `seniority`, `job_functions`, `company_size`, `revenue`, `regions`, `continents`, `countries`, `headquarters_countries`, `industries`, `personas`, `entity_types`, `email_status`.

Example request:

```bash
curl -sS -X POST "https://app.getleads.io/api/v1/contacts/search" 
  -H "Authorization: Bearer $GETLEADS_API_KEY" 
  -H "Content-Type: application/json" 
  -d '{"filters":{"domains":["acme.com"],"email_status":["VALID"]},"limit":10}'
```

### `POST /api/v1/contacts/search/count`

Aggregated match count for a filter set — free (0 credits), no records returned, no pagination needed. Takes the same auth and the same filter body as `POST /api/v1/contacts/search` (`limit`, `offset`, and `columns` are ignored). Use it to size a query before searching or exporting, or for coverage analysis.

Counts are exact up to 500,000. Broader queries return `total_matching: 500001` with `total_matching_is_minimum: true` ("at least 500k") — slice the query into disjoint segments (e.g. by country or employee band) and sum the counts for exact totals above that. For the total database size, use `GET /api/v1/contacts/health` (`record_count`).

Example request:

```bash
curl -sS -X POST "https://app.getleads.io/api/v1/contacts/search/count" 
  -H "Authorization: Bearer $GETLEADS_API_KEY" 
  -H "Content-Type: application/json" 
  -d '{"filters":{"countries":["Ireland"],"seniority":["C-Team"]}}'
```

Example response:

```json
{
  "ok": true,
  "total_matching": 41836,
  "max_export_rows": 50000,
  "exportable_rows": 41836,
  "export_capped": false,
  "credits_used": 0,
  "creditsRemaining": null,
  "message": "Found 41836 matching contacts. All 41836 can be exported in one CSV."
}
```

`exportable_rows` is how many of the matches a single CSV export would write (`min(total_matching, 50000)`, further bounded by remaining credits on the free plan); `export_capped` is `true` when the match count exceeds that.

### `POST /api/v1/contacts/search/export`

Start an async export of search matches to CSV on S3. Same filters as `POST /api/v1/contacts/search` (no `offset`). Returns immediately with `export_id` (HTTP 202); poll `GET /api/v1/contacts/search/export/{export_id}` until `job_status` is `completed`, then use `export_url`. Free plan: capped at `min(creditsRemaining, total_available)`. Unlimited: subject to daily (500k) and monthly (6M) export caps. Optional `max_rows` (1–50,000) caps how many rows this export writes; omit to export all matches up to plan/credit/50k limits. 1 credit per row exported.

Request body:

```json
{
  "filters": {
    "job_titles": ["Software Engineer"],
    "cities": ["San Francisco"]
  },
  "max_per_company": 3,
  "max_rows": 5000,
  "confirmed": true
}
```

Response (202 Accepted):

```json
{
  "ok": true,
  "export_id": "01KV8DNW282Y2V5YAQ51C2XWN1",
  "job_status": "queued",
  "rows_available": 46169,
  "export_row_cap": 5000,
  "rows_capped_by_credits": true,
  "message": "Export started. Poll GET /api/v1/contacts/search/export/{export_id} until job_status is completed."
}
```

### `GET /api/v1/contacts/search/export/{export_id}`

Poll export status from `POST /api/v1/contacts/search/export`. While `job_status` is `queued` or `running`, retry every few seconds. When `completed`, the response includes a presigned `export_url` (valid 24 hours).

Response (completed):

```json
{
  "ok": true,
  "export_id": "01KV8DNW282Y2V5YAQ51C2XWN1",
  "job_status": "completed",
  "export_url": "https://…",
  "expires_in_seconds": 86400,
  "rows_exported": 46169,
  "rows_available": 46169,
  "rows_capped_by_credits": false,
  "query_credits_used": 46169,
  "creditsRemaining": 1234
}
```

### `GET /api/v1/contacts/filter-values`

Query param `field` — returns allowed enum values for list filters used in search. Supported fields: `seniority`, `job_functions`, `company_size`, `revenue`, `regions`, `continents`, `countries`, `headquarters_countries`, `industries`, `personas`, `entity_types`, `email_status`.

---

## Funding signals

### `GET /api/v1/funding/signals`

Latest startup funding rounds from US and EU RSS feeds (TechCrunch, Sifted, EU-Startups, Tech.eu, and others). Each request fetches feeds live (typically 15–45s). Returns structured facts only — company, amount, round, announced date, and source URL. 1 credit per record returned; 0 if none. MCP tool `list_funding_signals`.

Requires `DYNAMODB_TABLE` for write-through history. Optional `SIGNALS_API_ENRICH=1` caps article fact enrichment per request. Default `min_confidence=0.5` filters noisy items.

Query params:

```text
limit          — 1–200, default 50
since          — YYYY-MM-DD (optional)
min_confidence — 0–1, default 0.5
region         — US | EU | GLOBAL (optional)
```

Example request:

```bash
curl -sS "https://app.getleads.io/api/v1/funding/signals?limit=20&min_confidence=0.5" 
  -H "Authorization: Bearer $GETLEADS_API_KEY"
```

---

## Acquisition signals

### `GET /api/v1/acquisitions/signals`

M&A and acquisition deals from RSS (TechCrunch M&A, PR Newswire). Each request fetches feeds live. Returns acquirer, target, optional deal amount, announced date, and source URL — facts only, never article text. 1 credit per record returned; 0 if none. MCP tool `list_acquisition_signals`.

Query params:

```text
limit          — 1–200, default 50
since          — YYYY-MM-DD (optional)
min_confidence — 0–1, default 0.5
acquirer       — substring filter on acquirer name
target         — substring filter on target name
has_amount     — true | 1 (only deals with disclosed amount)
min_amount     — numeric floor (implies has_amount)
```

Example request:

```bash
curl -sS "https://app.getleads.io/api/v1/acquisitions/signals?limit=20&has_amount=true" 
  -H "Authorization: Bearer $GETLEADS_API_KEY"
```