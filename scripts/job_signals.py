"""Weekly job-signal pipeline for Unprospect.

The pipeline deliberately separates evidence from interpretation:
1. Apify harvests public job postings.
2. The full posting and raw payload are retained.
3. A deterministic prefilter creates a compact review packet, but never rejects data.
4. A human or LLM imports a structured fit decision with evidence present in the posting.
5. Existing Supabase contacts are matched without spending enrichment credits.
6. Copy and sending remain disabled until a separate, approved module exists.

Live Apify calls require ``--live``. Sending cannot be enabled from this script alone.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "job_signals.json"
APIFY_BASE = "https://api.apify.com/v2"
TERMINAL_RUN_STATUSES = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}

POSITIVE_TERMS = (
    "outbound",
    "cold outreach",
    "cold email",
    "cold calling",
    "cold call",
    "prospeccion",
    "prospección",
    "generacion de leads",
    "generación de leads",
    "lead generation",
    "generacion de demanda",
    "generación de demanda",
    "demand generation",
    "new business",
    "nuevos negocios",
    "nuevas cuentas",
    "apertura de cuentas",
    "apertura de mercado",
    "pipeline",
    "new logo",
    "hunter",
    "sdr",
    "bdr",
    "sales development",
    "business development",
    "market databases",
    "industry lists",
    "source potential clients",
    "map companies",
    "elaboración de base de datos",
    "prospección telefónica",
    "telemarketing",
)

NEGATIVE_TERMS = (
    "ventas de piso",
    "venta de piso",
    "mostrador",
    "retail store",
    "tienda departamental",
    "customer success",
    "servicio al cliente",
    "cuentas existentes",
    "inbound only",
    "solo inbound",
    "account management",
    "customer management",
    "existing customers",
    "clientes actuales",
    "upsell",
    "up-selling",
    "cross-sell",
    "cross-selling",
    "retention",
    "retención",
    "renewals",
)

HIDDEN_EMPLOYER_TERMS = (
    "our client is looking",
    "client is looking for",
    "nuestro cliente está buscando",
    "nuestro cliente busca",
)

JOB_LOCATION_REQUIREMENT_PATTERNS = (
    (r"based in colombia\s*\(required\)", "Colombia"),
    (r"must be based in colombia", "Colombia"),
    (r"residir en colombia", "Colombia"),
    (r"residencia en colombia", "Colombia"),
)

SIGNAL_FITS = {"unreviewed", "high", "medium", "low", "no_signal"}
ACCOUNT_FITS = {"unreviewed", "high", "medium", "low", "no_fit"}
COMPANY_REGION_FITS = {"unreviewed", "latam", "non_latam", "uncertain"}
PROSPECTING_SCOPES = {
    "unknown",
    "national",
    "regional_latam",
    "international",
    "mixed",
}
EMPLOYER_CONFIDENCE = {"unreviewed", "verified", "likely", "hidden", "uncertain"}
CAMPAIGN_ACTIONS = {"review", "contact", "hold", "exclude"}

SMALL_COMPANY_BUYERS = (
    "founder",
    "co-founder",
    "cofounder",
    "fundador",
    "fundadora",
    "ceo",
    "director general",
    "directora general",
    "gerente general",
    "owner",
    "dueño",
    "dueña",
    "socio director",
    "socia directora",
)

SALES_LEADERS = (
    "chief revenue officer",
    "cro",
    "vp sales",
    "vp of sales",
    "head of sales",
    "sales director",
    "director comercial",
    "directora comercial",
    "director de ventas",
    "directora de ventas",
    "gerente comercial",
    "gerente de ventas",
    "head of business development",
    "business development director",
)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    config = read_json(config_path)
    if config.get("analysis", {}).get("copy_module") is not None:
        raise ValueError("copy_module must remain null until the new copy system is approved")
    geography = config.get("geography", {})
    if geography.get("job_location_qualifies_company_region") is not False:
        raise ValueError(
            "job_location_qualifies_company_region must remain false; "
            "a job location is not evidence of the employer's headquarters"
        )
    if not configured_search_locations(config):
        raise ValueError("At least one geography.search_locations value is required")
    return config


def resolve_repo_path(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def load_keywords(path: str | Path) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    with resolve_repo_path(path).open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            value = raw_line.strip()
            if not value or value.startswith("#"):
                continue
            key = value.casefold()
            if key not in seen:
                seen.add(key)
                result.append(value)
    return result


def configured_search_locations(config: dict[str, Any]) -> list[str]:
    """Return deduplicated LinkedIn search regions, with legacy config support."""
    geography = config.get("geography", {})
    values = geography.get("search_locations")
    if values is None and geography.get("location"):
        values = [geography["location"]]
    if isinstance(values, str):
        values = [values]
    result: list[str] = []
    seen: set[str] = set()
    for raw in values or []:
        value = normalize_space(raw)
        key = value.casefold()
        if value and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def build_search_urls(
    keywords: Iterable[str], location: str, freshness_seconds: int
) -> list[str]:
    base = "https://www.linkedin.com/jobs/search/"
    urls = []
    for keyword in keywords:
        query = urllib.parse.urlencode(
            {
                "keywords": keyword,
                "location": location,
                "f_TPR": f"r{freshness_seconds}",
            }
        )
        urls.append(f"{base}?{query}")
    return urls


def actor_input(config: dict[str, Any], max_results: int | None = None) -> dict[str, Any]:
    harvest = config["harvest"]
    keywords = load_keywords(harvest["keywords_file"])
    urls = [
        url
        for location in configured_search_locations(config)
        for url in build_search_urls(
            keywords,
            location,
            int(harvest["freshness_seconds"]),
        )
    ]
    count = int(max_results or harvest["max_results"])
    if count < 10:
        raise ValueError("The selected Apify actor requires at least 10 results")
    return {
        "urls": urls,
        "scrapeCompany": bool(harvest.get("scrape_company", True)),
        "count": count,
        "splitByLocation": bool(harvest.get("split_by_location", False)),
    }


def estimate_cost(config: dict[str, Any], max_results: int | None = None) -> float:
    harvest = config["harvest"]
    count = int(max_results or harvest["max_results"])
    return round(count * float(harvest["estimated_usd_per_result"]), 4)


def normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    match = re.search(r"\d[\d,]*", str(value))
    if not match:
        return None
    try:
        return int(match.group(0).replace(",", ""))
    except ValueError:
        return None


def normalize_timestamp(value: Any) -> str | None:
    text = normalize_space(value)
    if not text:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return f"{text}T00:00:00+00:00"
    return text


def domain_from_website(value: Any) -> str | None:
    text = normalize_space(value)
    if not text:
        return None
    if "://" not in text:
        text = "https://" + text
    try:
        host = (urllib.parse.urlparse(text).hostname or "").lower()
    except ValueError:
        return None
    if host.startswith("www."):
        host = host[4:]
    return host or None


def company_address_country_code(value: Any) -> str | None:
    """Extract the actor-provided address country without treating it as verified HQ."""
    payload = value
    if isinstance(value, str):
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return None
    if not isinstance(payload, dict):
        return None
    code = normalize_space(payload.get("addressCountry")).upper()
    return code or None


def description_hash(description: str) -> str:
    return hashlib.sha256(description.encode("utf-8")).hexdigest()


def _matched_terms(text: str, terms: Iterable[str]) -> list[str]:
    folded = text.casefold()
    return [term for term in terms if term.casefold() in folded]


def extract_evidence(
    description: str,
    terms: Iterable[str] = POSITIVE_TERMS,
    limit: int = 12,
) -> list[str]:
    """Return exact source fragments around matched terms, never paraphrases."""
    if not description:
        return []
    chunks = [
        normalize_space(chunk)
        for chunk in re.split(r"(?:[•●▪◦]|\r?\n)+|(?<=[.!?])\s+", description)
        if normalize_space(chunk)
    ]
    evidence: list[str] = []
    seen: set[str] = set()
    folded_terms = tuple(term.casefold() for term in terms)
    for chunk in chunks:
        folded = chunk.casefold()
        if any(term in folded for term in folded_terms):
            exact = chunk[:900]
            key = exact.casefold()
            if key not in seen:
                seen.add(key)
                evidence.append(exact)
                if len(evidence) >= limit:
                    return evidence

    # Some scraped descriptions have no usable sentence boundaries. Keep local windows.
    full_folded = description.casefold()
    for term in folded_terms:
        start = full_folded.find(term)
        if start < 0:
            continue
        left = max(0, start - 240)
        right = min(len(description), start + len(term) + 360)
        exact = description[left:right].strip()
        key = normalize_space(exact).casefold()
        if exact and key not in seen:
            seen.add(key)
            evidence.append(exact)
            if len(evidence) >= limit:
                break
    return evidence


def prefilter(title: str, description: str) -> tuple[str, list[str]]:
    """Set review priority only. This function is never a final fit decision."""
    text = normalize_space(f"{title} {description}")
    positive = _matched_terms(text, POSITIVE_TERMS)
    negative = _matched_terms(text, NEGATIVE_TERMS)
    if len(positive) >= 2:
        priority = "high"
    elif positive:
        priority = "medium"
    elif negative:
        priority = "low"
    else:
        priority = "review"
    reasons = [f"positive:{term}" for term in positive[:8]]
    reasons.extend(f"negative:{term}" for term in negative[:8])
    return priority, reasons


def job_location_requirement(description: str) -> str | None:
    folded = normalize_space(description).casefold()
    for pattern, country in JOB_LOCATION_REQUIREMENT_PATTERNS:
        if re.search(pattern, folded, flags=re.IGNORECASE):
            return country
    return None


def source_warnings(description: str) -> list[str]:
    """Return source-integrity warnings, never account-geo conclusions."""
    folded = normalize_space(description).casefold()
    if any(term in folded for term in HIDDEN_EMPLOYER_TERMS):
        return ["hidden_employer"]
    return []


def compact_excerpt(
    title: str,
    company: str,
    description: str,
    max_chars: int,
    evidence_limit: int,
) -> str:
    evidence = extract_evidence(description, limit=evidence_limit)
    header = f"Puesto: {normalize_space(title)}\nEmpresa: {normalize_space(company)}"
    if evidence:
        body = "\n".join(f"- {item}" for item in evidence)
    else:
        body = normalize_space(description)[: max(0, max_chars - len(header) - 2)]
    return f"{header}\n{body}"[:max_chars]


def normalize_job(item: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    title = normalize_space(item.get("title") or item.get("jobTitle"))
    company_name = normalize_space(item.get("companyName") or item.get("company"))
    description = str(
        item.get("descriptionText")
        or item.get("description")
        or item.get("jobDescription")
        or ""
    ).strip()
    job_url = normalize_space(item.get("link") or item.get("url") or item.get("jobUrl")) or None
    source_job_id = normalize_space(item.get("id") or item.get("jobId"))
    if not source_job_id:
        basis = "|".join((job_url or "", title, company_name, description[:500]))
        source_job_id = "hash:" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:24]

    company_website = normalize_space(item.get("companyWebsite")) or None
    industries = item.get("industries")
    if isinstance(industries, list):
        industries = ", ".join(normalize_space(value) for value in industries if value)
    industries = normalize_space(industries) or None
    priority, reasons = prefilter(title, description)
    warnings = source_warnings(description)
    if warnings:
        priority = "low"
        reasons.extend(warnings)
    analysis = config["analysis"]
    employer_confidence = "hidden" if "hidden_employer" in warnings else "unreviewed"

    return {
        "workspace": config["workspace"],
        "source": config["source"],
        "source_job_id": source_job_id,
        "job_url": job_url,
        "role_title": title or None,
        "job_function": normalize_space(item.get("jobFunction")) or None,
        "seniority": normalize_space(item.get("seniorityLevel")) or None,
        "employment_type": normalize_space(item.get("employmentType")) or None,
        "location": normalize_space(item.get("location")) or None,
        "job_location_requirement": job_location_requirement(description),
        "posted_at": normalize_timestamp(item.get("postedAt")),
        "description_text": description or None,
        "description_hash": description_hash(description),
        "analysis_excerpt": compact_excerpt(
            title,
            company_name,
            description,
            int(analysis["excerpt_max_chars"]),
            int(analysis["evidence_sentence_limit"]),
        ),
        "company_name": company_name or None,
        "company_domain": domain_from_website(company_website),
        "company_website": company_website,
        "company_linkedin_url": normalize_space(item.get("companyLinkedinUrl")) or None,
        "company_logo_url": normalize_space(item.get("companyLogo")) or None,
        "company_employee_count": safe_int(item.get("companyEmployeesCount")),
        "company_industries": industries,
        "company_address_country_code": company_address_country_code(
            item.get("companyAddress")
        ),
        "company_hq_country": None,
        "company_region_fit": "unreviewed",
        "prefilter_priority": priority,
        "prefilter_reasons": reasons,
        "fit": "unreviewed",
        "signal_fit": "unreviewed",
        "account_fit": "unreviewed",
        "prospecting_scope": "unknown",
        "prospecting_markets": [],
        "outbound_motions": [],
        "employer_confidence": employer_confidence,
        "campaign_action": "hold" if employer_confidence == "hidden" else "review",
        "needs_human_review": True,
        "copy_status": "not_started",
        "email_subject": None,
        "email_1_body": None,
        "email_2_body": None,
        "pipeline_status": "ready_for_analysis",
        "raw_payload": item,
    }


def dedupe_jobs(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["workspace"], row["source"], row["source_job_id"])
        current = result.get(key)
        if current is None or len(row.get("description_text") or "") > len(
            current.get("description_text") or ""
        ):
            result[key] = row
    return list(result.values())


def review_packet(row: dict[str, Any]) -> dict[str, Any]:
    description = row.get("description_text") or ""
    return {
        "id": row.get("id"),
        "source_job_id": row["source_job_id"],
        "job_url": row.get("job_url"),
        "role_title": row.get("role_title"),
        "company_name": row.get("company_name"),
        "company_domain": row.get("company_domain"),
        "company_website": row.get("company_website"),
        "company_linkedin_url": row.get("company_linkedin_url"),
        "company_employee_count": row.get("company_employee_count"),
        "company_industries": row.get("company_industries"),
        "company_address_country_code": row.get("company_address_country_code"),
        "company_hq_country": row.get("company_hq_country"),
        "company_region_fit": row.get("company_region_fit", "unreviewed"),
        "location": row.get("location"),
        "job_location_requirement": row.get("job_location_requirement"),
        "posted_at": row.get("posted_at"),
        "prefilter_priority": row.get("prefilter_priority"),
        "prefilter_reasons": row.get("prefilter_reasons", []),
        "analysis_excerpt": row.get("analysis_excerpt"),
        "source_integrity": {
            "description_chars": len(description),
            "description_hash": row.get("description_hash") or description_hash(description),
            "full_source_retained": True,
        },
        "required_output": {
            "fit": "optional legacy overall: unreviewed | high | medium | no_fit | excluded",
            "fit_confidence": "0..1",
            "signal_fit": "high | medium | low | no_signal",
            "account_fit": "high | medium | low | no_fit | unreviewed",
            "company_hq_country": "verified/inferred country or null",
            "company_region_fit": "latam | non_latam | uncertain | unreviewed",
            "prospecting_scope": "national | regional_latam | international | mixed | unknown",
            "prospecting_markets": "short list of countries/regions named in the posting",
            "outbound_motions": "short list such as email, phone, linkedin, field, partners",
            "employer_confidence": "verified | likely | hidden | uncertain | unreviewed",
            "campaign_action": "contact | review | hold | exclude",
            "extracted_problem": "one factual sentence; no copy",
            "evidence_quotes": "exact fragments from analysis_excerpt/full posting",
            "analysis_reason": "brief rationale",
            "needs_human_review": "boolean",
        },
    }


REVIEW_MARKET_PATTERNS = (
    ("Mexico", r"\b(?:mexico|méxico|mexican)\b"),
    ("LATAM", r"\b(?:latam|latin america|latinoam[eé]rica|américa latina)\b"),
    ("United States", r"\b(?:united states|u\.s\.|usa|us market|u\.s\. market)\b"),
    ("Canada", r"\bcanada\b"),
    ("Brazil", r"\b(?:brazil|brasil)\b"),
    ("Colombia", r"\bcolombia\b"),
    ("Spain", r"\b(?:spain|españa)\b"),
    ("Europe", r"\b(?:europe|europa|emea)\b"),
    ("Global / international", r"\b(?:global|international|internacional)\b"),
)

REVIEW_TARGET_TERMS = (
    "b2b",
    "companies",
    "businesses",
    "enterprises",
    "organizations",
    "clientes",
    "empresas",
    "cuentas objetivo",
    "target accounts",
    "decision makers",
    "tomadores de decisión",
    "prospects",
)

REVIEW_LOW_VALUE_TERMS = (
    "equal opportunity",
    "we offer",
    "benefits",
    "prestaciones",
    "requirements",
    "requisitos",
    "habilidades",
    "skills",
    "about us",
    "acerca de nosotros",
)

REVIEW_HIDDEN_EMPLOYER_TERMS = HIDDEN_EMPLOYER_TERMS + (
    "confidential client",
    "cliente confidencial",
    "empresa líder busca",
    "para uno de nuestros clientes",
    "for one of our clients",
)

LATAM_COUNTRY_CODES = {
    "AR", "BO", "BR", "CL", "CO", "CR", "CU", "DO", "EC", "SV", "GT",
    "HN", "MX", "NI", "PA", "PY", "PE", "PR", "UY", "VE",
}


def _review_chunks(description: str) -> list[str]:
    """Split a posting into readable exact-source fragments."""
    clean = html.unescape(description or "").replace("\xa0", " ")
    chunks = [
        normalize_space(chunk).strip(" -–—•●▪◦")
        for chunk in re.split(r"(?:[•●▪◦]|\r?\n)+|(?<=[.!?])\s+", clean)
    ]
    return [chunk for chunk in chunks if 35 <= len(chunk) <= 900]


def _review_fragment_score(fragment: str) -> int:
    folded = fragment.casefold()
    score = 0
    score += 3 * sum(term.casefold() in folded for term in POSITIVE_TERMS)
    score += 2 * sum(term in folded for term in REVIEW_TARGET_TERMS)
    score += 2 * sum(
        bool(re.search(pattern, folded, flags=re.IGNORECASE))
        for _, pattern in REVIEW_MARKET_PATTERNS
    )
    score -= 2 * sum(term in folded for term in REVIEW_LOW_VALUE_TERMS)
    if re.match(
        r"^(?:experiencia|experience|requirements?|requisitos?|qualifications?|skills?|education|educación|licenciatura|bachelor|must have|nice to have)\b",
        folded,
    ):
        score -= 5
    if any(
        term in folded
        for term in (
            "prospect", "generate", "build", "identify", "develop", "contact",
            "reach out", "research", "create", "open new", "generar", "identificar",
            "desarrollar", "contactar", "construir", "abrir cuentas", "buscar clientes",
        )
    ):
        score += 2
    if any(
        term in folded
        for term in (
            "responsab",
            "your role",
            "you will",
            "serás",
            "objetivo del puesto",
            "what you will do",
            "qué harás",
        )
    ):
        score += 2
    return score


def review_description_fragments(description: str, limit: int = 3) -> list[str]:
    """Select high-information exact fragments; never paraphrase the posting."""
    ranked = sorted(
        enumerate(_review_chunks(description)),
        key=lambda item: (-_review_fragment_score(item[1]), item[0]),
    )
    result: list[str] = []
    seen: set[str] = set()
    for _, fragment in ranked:
        key = fragment.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(fragment)
        if len(result) >= limit:
            break
    return result


def review_market_mentions(description: str) -> list[str]:
    folded = normalize_space(html.unescape(description or "")).casefold()
    return [
        label
        for label, pattern in REVIEW_MARKET_PATTERNS
        if re.search(pattern, folded, flags=re.IGNORECASE)
    ]


def possible_us_for_us(description: str) -> bool:
    folded = normalize_space(html.unescape(description or "")).casefold()
    patterns = (
        r"\b(?:us|u\.s\.|usa|united states)[ -]?(?:based )?(?:market|clients|customers|businesses|accounts)\b",
        r"\b(?:sell|selling|sales|prospect|prospecting|outbound)\b.{0,80}\b(?:us|u\.s\.|usa|united states)\b",
        r"\b(?:mercado|clientes|cuentas) (?:de |en |estadounidenses?|norteamerican[oa]s?)\b",
    )
    return any(re.search(pattern, folded, flags=re.IGNORECASE) for pattern in patterns)


def is_clean_high_signal(row: dict[str, Any]) -> bool:
    reasons = row.get("prefilter_reasons") or []
    return row.get("prefilter_priority") == "high" and not any(
        str(reason).startswith("negative:") for reason in reasons
    )


def company_review_key(row: dict[str, Any]) -> str:
    """Match the current human-review count: company name first, then stable fallbacks."""
    name = normalize_space(row.get("company_name")).casefold()
    if name:
        return "name:" + name
    domain = normalize_space(row.get("company_domain")).casefold()
    if domain:
        return "domain:" + domain
    linkedin = normalize_space(row.get("company_linkedin_url")).casefold()
    if linkedin:
        return "linkedin:" + linkedin
    return "job:" + normalize_space(row.get("source_job_id")).casefold()


def build_company_review_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Consolidate clean postings into one auditable human-review row per company."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if is_clean_high_signal(row):
            groups.setdefault(company_review_key(row), []).append(row)

    output: list[dict[str, Any]] = []
    for group in groups.values():
        group.sort(key=lambda row: row.get("posted_at") or "", reverse=True)
        primary = max(
            group,
            key=lambda row: (
                len(row.get("description_text") or ""),
                row.get("posted_at") or "",
            ),
        )
        descriptions = [row.get("description_text") or "" for row in group]
        combined = "\n".join(descriptions)
        company_descriptions = [
            normalize_space((row.get("raw_payload") or {}).get("companyDescription"))
            for row in group
            if normalize_space((row.get("raw_payload") or {}).get("companyDescription"))
        ]
        company_description = max(company_descriptions, key=len) if company_descriptions else ""

        briefs: list[str] = []
        brief_seen: set[str] = set()
        target_fragments: list[str] = []
        for row in group:
            fragments = review_description_fragments(row.get("description_text") or "", 3)
            if fragments:
                brief = (
                    f"{normalize_space(row.get('role_title')) or 'Puesto sin título'}: "
                    + " | ".join(fragments)
                )
                brief_key = normalize_space(brief).casefold()
                if brief_key not in brief_seen and len(briefs) < 4:
                    brief_seen.add(brief_key)
                    briefs.append(brief)
            for fragment in _review_chunks(row.get("description_text") or ""):
                if any(term in fragment.casefold() for term in REVIEW_TARGET_TERMS):
                    target_fragments.append(fragment)

        reasons = {
            str(reason).removeprefix("positive:")
            for row in group
            for reason in (row.get("prefilter_reasons") or [])
            if str(reason).startswith("positive:")
        }
        warnings: list[str] = []
        flag_us_market = possible_us_for_us(combined)
        if flag_us_market:
            warnings.append("Posible venta hacia USA; verificar que la empresa sí esté basada en LATAM")
        folded = normalize_space(html.unescape(combined)).casefold()
        if any(term.casefold() in folded for term in REVIEW_HIDDEN_EMPLOYER_TERMS):
            warnings.append("Posible empleador oculto / vacante publicada por intermediario")
        industries = normalize_space(primary.get("company_industries"))
        company_name_folded = normalize_space(primary.get("company_name")).casefold()
        recruiter_name = any(
            term in company_name_folded
            for term in (
                "reclut", "talent", "consultores", "headhunt", "human resources",
                "people4business", "powerbell", "cazando talento",
            )
        )
        recruiter_description = any(
            re.search(pattern, folded, flags=re.IGNORECASE)
            for pattern in (
                r"\bempresa (?:líder|importante).{0,140}\bbusca\b",
                r"\bpara integrarse a una empresa\b",
                r"\b(?:nuestro|our) cliente\b",
            )
        )
        flag_recruiter = (
            "staffing" in industries.casefold()
            or "recruit" in industries.casefold()
            or recruiter_name
            or recruiter_description
        )
        if flag_recruiter:
            warnings.append("Empresa o fuente relacionada con reclutamiento; confirmar empleador real")
        source_country = normalize_space(primary.get("company_address_country_code")).upper()
        flag_non_latam_source = bool(
            source_country and source_country not in LATAM_COUNTRY_CODES and source_country != "OO"
        )
        if source_country and source_country not in LATAM_COUNTRY_CODES:
            if source_country == "OO":
                warnings.append("Código de país de la fuente no interpretable; HQ sin verificar")
            else:
                warnings.append(
                    f"Fuente de LinkedIn indica país {source_country}; HQ LATAM no verificada"
                )
        flag_missing_domain = not bool(primary.get("company_domain"))
        if flag_missing_domain:
            warnings.append("Falta dominio")
        if len(group) > 1:
            warnings.append(f"{len(group)} vacantes consolidadas; revisar diferencias")

        target_unique: list[str] = []
        target_seen: set[str] = set()
        for fragment in target_fragments:
            key = fragment.casefold()
            if key not in target_seen:
                target_seen.add(key)
                target_unique.append(fragment)
            if len(target_unique) >= 3:
                break

        output.append(
            {
                "review_status": "Pendiente",
                "manual_company_base": "Sin revisar",
                "manual_b2b": "Sin revisar",
                "manual_employer": "Sin revisar",
                "manual_fit": "Sin revisar",
                "manual_notes": "",
                "company_name": primary.get("company_name"),
                "company_domain": primary.get("company_domain"),
                "company_website": primary.get("company_website"),
                "company_linkedin_url": primary.get("company_linkedin_url"),
                "company_logo_url": primary.get("company_logo_url"),
                "company_employee_count_source": primary.get("company_employee_count"),
                "company_industries_source": primary.get("company_industries"),
                "company_country_hint_source": primary.get("company_address_country_code"),
                "company_description_source": company_description[:1200],
                "job_count": len(group),
                "role_titles": " | ".join(
                    dict.fromkeys(normalize_space(row.get("role_title")) for row in group)
                ),
                "latest_posted_at": max(
                    (row.get("posted_at") or "" for row in group), default=""
                ),
                "job_locations": " | ".join(
                    dict.fromkeys(
                        normalize_space(row.get("location"))
                        for row in group
                        if normalize_space(row.get("location"))
                    )
                ),
                "market_mentions": ", ".join(review_market_mentions(combined)),
                "outbound_terms": ", ".join(sorted(reasons, key=str.casefold)),
                "description_brief_exact": "\n\n".join(briefs)[:5000],
                "target_customer_evidence_exact": "\n".join(target_unique)[:2200],
                "automatic_warnings": " | ".join(warnings),
                "flag_us_market": "Sí" if flag_us_market else "No",
                "flag_recruiter": "Sí" if flag_recruiter else "No",
                "flag_non_latam_source": "Sí" if flag_non_latam_source else "No",
                "flag_missing_domain": "Sí" if flag_missing_domain else "No",
                "job_urls": "\n".join(
                    row.get("job_url") for row in group if row.get("job_url")
                ),
                "source_job_ids": ", ".join(
                    str(row.get("source_job_id")) for row in group
                ),
                "description_chars_total": sum(len(value) for value in descriptions),
                "description_hashes": ", ".join(
                    str(row.get("description_hash") or description_hash(row.get("description_text") or ""))
                    for row in group
                ),
            }
        )
    return sorted(output, key=lambda row: normalize_space(row.get("company_name")).casefold())


def write_company_review_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _http_json(
    url: str,
    body: Any | None = None,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    timeout: int = 120,
) -> tuple[Any, dict[str, str]]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request_headers = {"Accept": "application/json", **(headers or {})}
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        url, data=data, method=method, headers=request_headers
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
        return (json.loads(payload) if payload else None), dict(response.headers)


def available_apify_tokens(config: dict[str, Any]) -> list[str]:
    tokens = []
    for name in config["harvest"]["token_env_names"]:
        value = os.environ.get(name)
        if value and value not in tokens:
            tokens.append(value)
    return tokens


def run_apify(
    config: dict[str, Any], max_results: int | None = None, poll_seconds: int = 15
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    tokens = available_apify_tokens(config)
    if not tokens:
        raise RuntimeError("No Apify token found in configured environment variables")
    payload = actor_input(config, max_results)
    actor = config["harvest"]["actor_id"]
    last_error: Exception | None = None
    run: dict[str, Any] | None = None
    token: str | None = None

    for candidate in tokens:
        try:
            response, _ = _http_json(
                f"{APIFY_BASE}/acts/{actor}/runs?token={urllib.parse.quote(candidate)}",
                payload,
                method="POST",
            )
            run = response["data"]
            token = candidate
            break
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in (402, 403, 429):
                raise
    if run is None or token is None:
        raise RuntimeError("All configured Apify tokens were rejected") from last_error

    while run["status"] not in TERMINAL_RUN_STATUSES:
        time.sleep(poll_seconds)
        response, _ = _http_json(
            f"{APIFY_BASE}/actor-runs/{run['id']}?token={urllib.parse.quote(token)}"
        )
        run = response["data"]

    items: list[dict[str, Any]] = []
    if run["status"] == "SUCCEEDED":
        offset = 0
        while True:
            page, _ = _http_json(
                f"{APIFY_BASE}/datasets/{run['defaultDatasetId']}/items"
                f"?token={urllib.parse.quote(token)}&clean=true&limit=1000&offset={offset}"
            )
            if not page:
                break
            items.extend(page)
            offset += len(page)
            if len(page) < 1000:
                break
    return run, items


def _supabase_credentials() -> tuple[str, str]:
    base = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not base or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    return base.rstrip("/"), key


def supabase_request(
    path: str,
    body: Any | None = None,
    method: str = "GET",
    prefer: str | None = None,
) -> Any:
    base, key = _supabase_credentials()
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "User-Agent": "unprospect-job-signals/1.0",
    }
    if prefer:
        headers["Prefer"] = prefer
    result, _ = _http_json(base + "/rest/v1/" + path, body, method, headers)
    return result


def supabase_insert_run(row: dict[str, Any]) -> str:
    result = supabase_request(
        "job_signal_runs",
        [row],
        method="POST",
        prefer="return=representation",
    )
    return result[0]["id"]


def supabase_upsert_signals(rows: list[dict[str, Any]], batch_size: int = 100) -> int:
    if not rows:
        return 0
    done = 0
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        supabase_request(
            "job_signals?on_conflict=workspace,source,source_job_id",
            batch,
            method="POST",
            prefer="resolution=merge-duplicates,return=minimal",
        )
        done += len(batch)
    return done


def _postgrest_value(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def fetch_signals(
    workspace: str,
    statuses: Iterable[str],
    limit: int = 500,
    run_id: str | None = None,
    prefilter_priority: str | None = None,
) -> list[dict[str, Any]]:
    values = ",".join(statuses)
    query = (
        f"job_signals?workspace=eq.{_postgrest_value(workspace)}"
        f"&pipeline_status=in.({values})"
    )
    if run_id:
        query += f"&run_id=eq.{_postgrest_value(run_id)}"
    if prefilter_priority:
        query += f"&prefilter_priority=eq.{_postgrest_value(prefilter_priority)}"
    query += "&select=*" + f"&limit={int(limit)}"
    return supabase_request(query) or []


def patch_signal(signal_id: str, body: dict[str, Any]) -> None:
    body = {**body, "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    supabase_request(
        f"job_signals?id=eq.{_postgrest_value(signal_id)}",
        body,
        method="PATCH",
        prefer="return=minimal",
    )


def load_json_or_jsonl(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        value = json.loads(text)
        if not isinstance(value, list):
            raise ValueError("Expected a JSON array")
        return value
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def load_review_source(path: Path) -> list[dict[str, Any]]:
    if path.is_dir():
        rows: list[dict[str, Any]] = []
        for child in sorted(path.glob("*.json")):
            rows.extend(load_json_or_jsonl(child))
        return rows
    return load_json_or_jsonl(path)


def quote_is_grounded(quote: str, source: str) -> bool:
    return normalize_space(quote).casefold() in normalize_space(source).casefold()


def analysis_pipeline_status(fit: str, needs_human_review: bool) -> str:
    if fit not in {"high", "medium"}:
        return "not_fit"
    if needs_human_review:
        return "qualified"
    return "ready_for_contact"


def dimensional_pipeline_status(
    fit: str,
    signal_fit: str,
    account_fit: str,
    company_region_fit: str,
    employer_confidence: str,
    campaign_action: str,
    needs_human_review: bool,
) -> str:
    """Gate contactability without confusing job signal, account, and geography."""
    if (
        campaign_action == "exclude"
        or signal_fit == "no_signal"
        or account_fit == "no_fit"
        or company_region_fit == "non_latam"
    ):
        return "not_fit"
    if signal_fit in {"high", "medium"}:
        contactable = (
            campaign_action == "contact"
            and account_fit in {"high", "medium"}
            and company_region_fit == "latam"
            and employer_confidence in {"verified", "likely"}
            and not needs_human_review
        )
        return "ready_for_contact" if contactable else "qualified"
    return analysis_pipeline_status(fit, needs_human_review)


def _decision_string_list(value: Any, field: str, source_job_id: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list for {source_job_id}")
    return [item for item in (normalize_space(raw) for raw in value) if item]


def import_analysis(path: Path, workspace: str, analysis_version: str) -> int:
    decisions = load_json_or_jsonl(path)
    allowed_fit = {"unreviewed", "high", "medium", "no_fit", "excluded"}
    updated = 0
    for decision in decisions:
        source_job_id = normalize_space(decision.get("source_job_id"))
        if not source_job_id:
            raise ValueError("Every analysis row requires source_job_id")
        fit = decision.get("fit", "unreviewed")
        if fit not in allowed_fit:
            raise ValueError(f"Invalid fit for {source_job_id}: {fit}")
        signal_fit = decision.get("signal_fit", "unreviewed")
        account_fit = decision.get("account_fit", "unreviewed")
        company_region_fit = decision.get("company_region_fit", "unreviewed")
        prospecting_scope = decision.get("prospecting_scope", "unknown")
        employer_confidence = decision.get("employer_confidence", "unreviewed")
        campaign_action = decision.get("campaign_action", "review")
        dimensions = (
            ("signal_fit", signal_fit, SIGNAL_FITS),
            ("account_fit", account_fit, ACCOUNT_FITS),
            ("company_region_fit", company_region_fit, COMPANY_REGION_FITS),
            ("prospecting_scope", prospecting_scope, PROSPECTING_SCOPES),
            ("employer_confidence", employer_confidence, EMPLOYER_CONFIDENCE),
            ("campaign_action", campaign_action, CAMPAIGN_ACTIONS),
        )
        for field, value, allowed in dimensions:
            if value not in allowed:
                raise ValueError(f"Invalid {field} for {source_job_id}: {value}")
        prospecting_markets = _decision_string_list(
            decision.get("prospecting_markets"), "prospecting_markets", source_job_id
        )
        outbound_motions = _decision_string_list(
            decision.get("outbound_motions"), "outbound_motions", source_job_id
        )
        confidence = float(decision.get("fit_confidence"))
        if not 0 <= confidence <= 1:
            raise ValueError(f"fit_confidence must be 0..1 for {source_job_id}")
        rows = supabase_request(
            "job_signals"
            f"?workspace=eq.{_postgrest_value(workspace)}"
            f"&source_job_id=eq.{_postgrest_value(source_job_id)}"
            "&select=id,description_text"
            "&limit=1"
        )
        if not rows:
            raise ValueError(f"Unknown source_job_id: {source_job_id}")
        source = rows[0].get("description_text") or ""
        quotes = decision.get("evidence_quotes") or []
        if not isinstance(quotes, list):
            raise ValueError(f"evidence_quotes must be a list for {source_job_id}")
        ungrounded = [quote for quote in quotes if not quote_is_grounded(str(quote), source)]
        if ungrounded:
            raise ValueError(f"Ungrounded evidence for {source_job_id}: {ungrounded[0]!r}")
        if (fit in {"high", "medium"} or signal_fit in {"high", "medium"}) and not quotes:
            raise ValueError(f"Positive fit requires source evidence for {source_job_id}")
        needs_review = bool(decision.get("needs_human_review", confidence < 0.8))
        status = dimensional_pipeline_status(
            fit,
            signal_fit,
            account_fit,
            company_region_fit,
            employer_confidence,
            campaign_action,
            needs_review,
        )
        patch_signal(
            rows[0]["id"],
            {
                "fit": fit,
                "fit_confidence": confidence,
                "signal_fit": signal_fit,
                "account_fit": account_fit,
                "company_hq_country": normalize_space(
                    decision.get("company_hq_country")
                )
                or None,
                "company_region_fit": company_region_fit,
                "prospecting_scope": prospecting_scope,
                "prospecting_markets": prospecting_markets,
                "outbound_motions": outbound_motions,
                "employer_confidence": employer_confidence,
                "campaign_action": campaign_action,
                "extracted_problem": normalize_space(decision.get("extracted_problem")) or None,
                "evidence_quotes": quotes,
                "analysis_reason": normalize_space(decision.get("analysis_reason")) or None,
                "analysis_version": analysis_version,
                "analyzed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "needs_human_review": needs_review,
                "pipeline_status": status,
            },
        )
        updated += 1
    return updated


def title_rank(title: str, employee_count: int | None) -> int:
    folded = normalize_space(title).casefold()
    if not folded:
        return 0
    small = employee_count is not None and employee_count <= 20
    primary = SMALL_COMPANY_BUYERS if small else SALES_LEADERS
    secondary = SALES_LEADERS if small else SMALL_COMPANY_BUYERS
    if any(term in folded for term in primary):
        return 100
    if any(term in folded for term in secondary):
        return 70
    if any(term in folded for term in ("sales", "ventas", "comercial", "negocios")):
        return 30
    return 0


def _parse_timestamp(value: Any) -> dt.datetime | None:
    text = normalize_space(value)
    if not text:
        return None
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def choose_contact(
    contacts: list[dict[str, Any]],
    employee_count: int | None,
    verified_statuses: Iterable[str],
    recontact_after_days: int,
) -> tuple[dict[str, Any] | None, str | None]:
    verified = {value.casefold() for value in verified_statuses}
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=recontact_after_days)
    candidates: list[tuple[int, int, dict[str, Any], str]] = []
    for contact in contacts:
        if contact.get("do_not_contact"):
            continue
        last_contacted = _parse_timestamp(contact.get("last_contacted_at"))
        if last_contacted and last_contacted.astimezone(dt.timezone.utc) > cutoff:
            continue
        rank = title_rank(contact.get("title") or "", employee_count)
        email = normalize_space(contact.get("email"))
        email_status = normalize_space(contact.get("email_status")).casefold()
        linkedin = normalize_space(contact.get("linkedin_url"))
        if email and email_status in verified:
            candidates.append((2, rank, contact, "email"))
        elif linkedin:
            candidates.append((1, rank, contact, "linkedin"))
    if not candidates:
        return None, None
    _, _, contact, channel = max(candidates, key=lambda item: (item[0], item[1]))
    return contact, channel


def match_existing_contacts(config: dict[str, Any], limit: int = 500) -> dict[str, int]:
    workspace = config["workspace"]
    signals = fetch_signals(workspace, ["ready_for_contact"], limit)
    result = {"signals": len(signals), "email": 0, "linkedin": 0, "unmatched": 0}
    contact_config = config["contact"]
    for signal in signals:
        domain = signal.get("company_domain")
        if not domain:
            result["unmatched"] += 1
            continue
        companies = supabase_request(
            "companies"
            f"?domain=eq.{_postgrest_value(domain)}"
            "&select=id,employee_count,do_not_contact"
            "&limit=1"
        )
        if not companies or companies[0].get("do_not_contact"):
            result["unmatched"] += 1
            continue
        company = companies[0]
        contacts = supabase_request(
            "contacts"
            f"?company_id=eq.{_postgrest_value(company['id'])}"
            "&select=id,first_name,last_name,full_name,title,email,email_status,linkedin_url,"
            "do_not_contact,last_contacted_at"
        ) or []
        employee_count = signal.get("company_employee_count") or company.get("employee_count")
        contact, channel = choose_contact(
            contacts,
            employee_count,
            contact_config["verified_email_statuses"],
            int(contact_config["recontact_after_days"]),
        )
        buyer_hint = (
            "founder_or_ceo"
            if employee_count is not None
            and employee_count <= int(contact_config["small_company_employee_max"])
            else "sales_leader"
        )
        if not contact or not channel:
            patch_signal(
                signal["id"],
                {"company_id": company["id"], "buyer_role_hint": buyer_hint},
            )
            result["unmatched"] += 1
            continue
        patch_signal(
            signal["id"],
            {
                "company_id": company["id"],
                "buyer_role_hint": buyer_hint,
                "contact_id": contact["id"],
                "contact_channel": channel,
                "contact_email_status": contact.get("email_status"),
                "contact_matched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "pipeline_status": "ready_for_copy",
            },
        )
        result[channel] += 1
    return result


def cmd_plan(args: argparse.Namespace, config: dict[str, Any]) -> None:
    payload = actor_input(config, args.max_results)
    estimate = estimate_cost(config, args.max_results)
    output = {
        "live_call": False,
        "actor_id": config["harvest"]["actor_id"],
        "keyword_count": len(payload["urls"]),
        "max_results": payload["count"],
        "estimated_max_cost_usd": estimate,
        "hard_budget_usd": config["harvest"]["hard_budget_usd"],
        "full_descriptions_retained": True,
        "copy_enabled": False,
        "sending_enabled": False,
        "actor_input": payload,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_normalize(args: argparse.Namespace, config: dict[str, Any]) -> None:
    items = read_json(Path(args.input))
    if not isinstance(items, list):
        raise ValueError("Input must be a JSON array of Apify items")
    rows = dedupe_jobs(normalize_job(item, config) for item in items)
    write_json(Path(args.output), rows)
    print(f"normalized={len(items)} unique={len(rows)} output={args.output}")


def cmd_harvest(args: argparse.Namespace, config: dict[str, Any]) -> None:
    if not args.live:
        cmd_plan(args, config)
        return
    estimate = estimate_cost(config, args.max_results)
    hard_budget = float(config["harvest"]["hard_budget_usd"])
    if estimate > hard_budget:
        raise RuntimeError(
            f"Estimated max cost ${estimate:.4f} exceeds hard budget ${hard_budget:.4f}"
        )
    run, items = run_apify(config, args.max_results, args.poll_seconds)
    rows = dedupe_jobs(normalize_job(item, config) for item in items)
    if args.output:
        write_json(Path(args.output), rows)
    persisted = 0
    if args.persist:
        run_id = supabase_insert_run(
            {
                "workspace": config["workspace"],
                "source": config["source"],
                "provider_run_id": run.get("id"),
                "provider_dataset_id": run.get("defaultDatasetId"),
                "status": run.get("status", "FAILED").lower().replace("-", "_"),
                "keyword_count": len(actor_input(config, args.max_results)["urls"]),
                "harvested_count": len(items),
                "unique_count": len(rows),
                "estimated_cost_usd": estimate,
                "actual_cost_usd": run.get("usageTotalUsd"),
                "config_snapshot": config,
                "error": run.get("statusMessage"),
                "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            }
        )
        for row in rows:
            row["run_id"] = run_id
        persisted = supabase_upsert_signals(rows)
    print(
        json.dumps(
            {
                "provider_status": run.get("status"),
                "harvested": len(items),
                "unique": len(rows),
                "persisted": persisted,
                "actual_cost_usd": run.get("usageTotalUsd"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def cmd_export_review(args: argparse.Namespace, config: dict[str, Any]) -> None:
    if args.input:
        rows = read_json(Path(args.input))
    else:
        rows = fetch_signals(config["workspace"], ["ready_for_analysis"], args.limit)
    priority_order = {"high": 0, "medium": 1, "review": 2, "low": 3}
    rows = sorted(
        rows,
        key=lambda row: (
            priority_order.get(row.get("prefilter_priority"), 9),
            row.get("posted_at") or "",
        ),
    )[: args.limit]
    packets = [review_packet(row) for row in rows]
    write_json(Path(args.output), packets)
    print(f"review_packets={len(packets)} output={args.output}")


def cmd_export_company_review(args: argparse.Namespace, config: dict[str, Any]) -> None:
    if args.input:
        source_rows = load_review_source(Path(args.input))
    else:
        if not args.run_id:
            raise ValueError("--run-id is required when reading company review data from Supabase")
        source_rows = fetch_signals(
            config["workspace"],
            ["ready_for_analysis", "qualified"],
            args.limit,
            run_id=args.run_id,
            prefilter_priority="high",
        )
    review_rows = build_company_review_rows(source_rows)
    write_json(Path(args.output), review_rows)
    if args.csv_output:
        write_company_review_csv(Path(args.csv_output), review_rows)
    print(
        f"source_jobs={len(source_rows)} clean_companies={len(review_rows)} "
        f"output={args.output} csv={args.csv_output or 'not_requested'}"
    )


def cmd_import_analysis(args: argparse.Namespace, config: dict[str, Any]) -> None:
    count = import_analysis(Path(args.input), config["workspace"], args.analysis_version)
    print(f"analysis_imported={count}")


def cmd_match_contacts(args: argparse.Namespace, config: dict[str, Any]) -> None:
    result = match_existing_contacts(config, args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_send(_: argparse.Namespace, config: dict[str, Any]) -> None:
    if not config["sending"]["enabled"]:
        raise RuntimeError(
            "Sending is disabled. Build and approve the new copy module first; "
            "then configure a sender and an explicit approval gate."
        )
    raise RuntimeError("No sender adapter is configured")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Show input and maximum cost; no network call")
    plan.add_argument("--max-results", type=int)
    plan.set_defaults(handler=cmd_plan)

    normalize = subparsers.add_parser("normalize", help="Normalize an Apify JSON fixture")
    normalize.add_argument("--input", required=True)
    normalize.add_argument("--output", required=True)
    normalize.set_defaults(handler=cmd_normalize)

    harvest = subparsers.add_parser("harvest", help="Plan by default; --live starts paid Apify run")
    harvest.add_argument("--live", action="store_true")
    harvest.add_argument("--persist", action="store_true")
    harvest.add_argument("--max-results", type=int)
    harvest.add_argument("--poll-seconds", type=int, default=15)
    harvest.add_argument("--output")
    harvest.set_defaults(handler=cmd_harvest)

    export = subparsers.add_parser("export-review", help="Create compact evidence packets")
    export.add_argument("--input", help="Optional normalized JSON; otherwise reads Supabase")
    export.add_argument("--output", required=True)
    export.add_argument("--limit", type=int, default=100)
    export.set_defaults(handler=cmd_export_review)

    company_review = subparsers.add_parser(
        "export-company-review",
        help="Consolidate clean high-priority postings into one auditable row per company",
    )
    company_review.add_argument(
        "--input", help="Optional JSON file or directory; otherwise reads Supabase"
    )
    company_review.add_argument("--run-id", help="Required for direct Supabase reads")
    company_review.add_argument("--output", required=True, help="JSON review output")
    company_review.add_argument("--csv-output", help="Optional UTF-8 CSV review output")
    company_review.add_argument("--limit", type=int, default=1000)
    company_review.set_defaults(handler=cmd_export_company_review)

    analysis = subparsers.add_parser("import-analysis", help="Validate and import fit decisions")
    analysis.add_argument("--input", required=True)
    analysis.add_argument("--analysis-version", required=True)
    analysis.set_defaults(handler=cmd_import_analysis)

    contacts = subparsers.add_parser("match-contacts", help="Match existing free Supabase contacts")
    contacts.add_argument("--limit", type=int, default=500)
    contacts.set_defaults(handler=cmd_match_contacts)

    send = subparsers.add_parser("send", help="Blocked until copy and sender are approved")
    send.set_defaults(handler=cmd_send)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        args.handler(args, config)
        return 0
    except (ValueError, RuntimeError, urllib.error.URLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
