"""Cleaner v2: markdown crawleado -> evidencia compacta para segmentación.

Objetivo: que un LLM pueda inferir industria, ICP, comprador, oferta, B2B, fit para
outbound y prueba social sin cargar navegación, formularios ni assets en el contexto.

El limpiador no es la fuente de verdad. ``pages[].raw_markdown`` y
``combined_markdown`` conservan el contenido recuperable; esta función genera dos vistas:

* ``clean_text``: texto completo, deduplicado y legible.
* ``segmentation_context``: selección con presupuesto, enfocada en las señales GTM.

La API histórica ``clean_markdown(md) -> str`` se conserva para no romper consumidores.
"""

from __future__ import annotations

from collections import Counter, OrderedDict
from html import unescape
import json
import re
from urllib.parse import unquote, urlparse


CLEAN_VERSION = "2.1"
DEFAULT_CONTEXT_CHARS = 10_000

PAGE_HEADER_RE = re.compile(r"^#\s+(/\S*)\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
TABLE_SEPARATOR_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?$")
RAW_URL_RE = re.compile(r"(?:https?://|mailto:|tel:)[^\s<>]+", re.IGNORECASE)
IMAGE_REF_START_RE = re.compile(r"!\[([^\]]*)\]\(")
LINK_REF_START_RE = re.compile(r"\[([^\]]*)\]\(")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PERCENT_RE = re.compile(r"(?<!\w)[+-]?\d+(?:[.,]\d+)?\s*%")
MONEY_RE = re.compile(
    r"(?:[$€£]\s?\d[\d,.]*(?:\s?(?:MXN|USD|EUR))?|\b\d[\d,.]*\s?(?:MXN|USD|EUR)\b)",
    re.IGNORECASE,
)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d \t().–—-]{6,}\d)")
CERT_RE = re.compile(
    r"\b(?:ISO\s?\d{3,6}(?::\d{4})?|SOC\s?[123]|PCI[- ]?DSS|SIPRES|CONDUSEF|"
    r"Great Place to Work|Empresa Socialmente Responsable|ESR)\b",
    re.IGNORECASE,
)


FOLD_TRANSLATION = str.maketrans({
    "á": "a", "à": "a", "ä": "a", "â": "a", "ã": "a",
    "é": "e", "è": "e", "ë": "e", "ê": "e",
    "í": "i", "ì": "i", "ï": "i", "î": "i",
    "ó": "o", "ò": "o", "ö": "o", "ô": "o", "õ": "o",
    "ú": "u", "ù": "u", "ü": "u", "û": "u",
    "ñ": "n", "ç": "c",
})


def _fold(text: str) -> str:
    """Minúsculas ES/EN sin acentos; conserva otros alfabetos y corre en C."""
    return text.casefold().translate(FOLD_TRANSLATION)


NAV_LABELS = {
    "inicio", "home", "nosotros", "about", "about us", "contacto", "contact",
    "blog", "menu", "cerrar", "close", "buscar", "search", "iniciar sesion",
    "login", "registrarse", "register", "espanol", "english", "aviso de privacidad",
    "privacy policy", "terminos y condiciones", "terms and conditions",
    "top of page", "bottom of page", "volver arriba", "back to top",
    "leer mas", "ver mas", "conoce mas", "learn more", "read more",
}

FORM_LABELS = {
    "nombre", "name", "apellido", "last name", "email", "correo", "correo electronico",
    "telefono", "phone", "mensaje", "message", "asunto", "subject", "empresa", "company",
    "enviar", "send", "submit", "aceptar", "accept", "requerido", "required",
}

UI_PREFIXES = (
    "saltar al contenido", "ir al contenido", "skip to content", "toggle navigation",
    "enviando formulario", "formulario recibido", "el servidor ha detectado",
    "introducir nombre", "introducir correo", "introducir mensaje", "escriba su mensaje",
    "aceptar cookies", "usamos cookies", "utilizamos cookies", "this site uses cookies",
    "we use cookies", "cookie settings", "configuracion de cookies", "cargando", "loading",
)

GENERIC_ALT = {
    "", "logo", "image", "imagen", "img", "icon", "icono", "banner", "hero",
    "arrow", "flecha", "menu", "close", "facebook", "instagram", "linkedin",
    "youtube", "whatsapp", "twitter", "x", "tiktok", "undefined",
}

VISUAL_HINTS = (
    "logo", "cliente", "client", "caso", "case", "testimonial", "success", "exito",
    "certif", "award", "premio", "partner", "alianza", "iso", "reconocimiento",
)

CATEGORY_TERMS = {
    "identity": (
        "quienes somos", "nosotros", "about us", "nuestra empresa", "mision", "vision",
        "fundada", "desde ", "somos una", "somos un", "empresa mexicana",
    ),
    "offer": (
        "servicio", "services", "producto", "products", "solucion", "solutions",
        "ofrecemos", "ayudamos", "plataforma", "software", "financiamiento", "credito",
        "consultoria", "especializamos", "que hacemos", "what we do",
    ),
    "audience": (
        "para empresas", "para negocios", "para pymes", "corporativo", "clientes",
        "dirigido a", "ayudamos a", "trabajamos con", "atendemos", "empresas que",
        "businesses", "companies", "organizations", "distribuidores", "fabricantes",
        "empresarios", "personas fisicas", "personas morales", "consumidor", "familias",
        "estudiante", "solicitante", "individuals", "students", "families",
    ),
    "industry": (
        "industria", "industrias", "sector", "sectores", "vertical", "mercado",
        "manufactura", "logistica", "transporte", "financier", "retail", "salud",
        "construccion", "tecnologia", "automotriz", "alimentos", "energia",
    ),
    "proof": (
        "caso de exito", "casos de exito", "case study", "success story", "testimonio",
        "testimonial", "nuestros clientes", "clientes que confian", "resultados",
        "certificado", "certificacion", "premio", "reconocimiento", "partner", "alianza",
        "anos de experiencia", "proyectos", "imagen:",
    ),
    "b2b": (
        "b2b", "empresa a empresa", "para empresas", "corporativo", "negocios", "pyme",
        "personas morales", "actividad empresarial",
        "organizaciones", "compañias", "companias", "c-level", "consejo de administracion",
        "proveedores", "distribuidores", "mayoreo", "wholesale", "business", "companies",
    ),
}

PATH_CATEGORY_TERMS = {
    "identity": ("nosotros", "about", "empresa", "company", "quienes-somos"),
    "offer": ("servicio", "service", "producto", "product", "solucion", "solution"),
    "audience": ("cliente", "customer", "mercado"),
    "industry": ("industria", "sector", "vertical"),
    "proof": ("caso", "case", "cliente", "testimonial", "proyecto", "success"),
}

LOW_VALUE_PATH_TERMS = (
    "privacidad", "privacy", "terminos", "terms", "legal", "cookies",
    "aviso-de-privacidad", "politica-de-privacidad",
)


def _unique(values: list[str], limit: int | None = None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
        if limit and len(out) >= limit:
            break
    return out


def _parse_destination(text: str, start: int) -> tuple[str, int] | None:
    """Lee el destino de ``](...)`` respetando paréntesis escapados/anidados."""
    depth = 1
    chars: list[str] = []
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            chars.append(text[i + 1])
            i += 2
            continue
        if ch == "(":
            depth += 1
            chars.append(ch)
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return "".join(chars).strip(), i + 1
            chars.append(ch)
        else:
            chars.append(ch)
        i += 1
    return None


def _informative_alt(alt: str) -> bool:
    folded = _fold(re.sub(r"\s+", " ", alt).strip())
    if folded in GENERIC_ALT:
        return False
    return len(re.sub(r"[^a-z0-9]", "", folded)) >= 3


def _visual_candidate(url: str, alt: str, path: str) -> bool:
    haystack = _fold(" ".join((unquote(url), alt, path)))
    if _informative_alt(alt):
        return True
    return any(term in haystack for term in VISUAL_HINTS)


def _evidence_link(url: str, text: str, path: str) -> bool:
    folded = _fold(" ".join((unquote(url), text, path)))
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme in {"mailto", "tel"}:
        return True
    if re.search(r"\.(?:pdf|docx?|xlsx?|pptx?)(?:$|[?#])", parsed.path, re.IGNORECASE):
        return True
    return any(term in folded for term in (
        "caso", "case", "cliente", "testimonial", "success", "exito", "certif",
        "servicio", "producto", "solucion", "industria", "sector", "proyecto",
    ))


def _replace_markdown_refs(text: str, path: str = "/") -> tuple[str, list[dict], list[dict]]:
    """Quita sintaxis markdown sin perder alt text/contactos y registra evidencia."""
    visuals: list[dict] = []
    links: list[dict] = []

    # Imágenes primero: `[![Logo](img)](home)` se vuelve un link normal cuyo
    # label es "Imagen: Logo", sin dejar markdown anidado roto.
    image_out: list[str] = []
    i = 0
    while True:
        match = IMAGE_REF_START_RE.search(text, i)
        if not match:
            image_out.append(text[i:])
            break
        image_out.append(text[i:match.start()])
        parsed = _parse_destination(text, match.end())
        if not parsed:
            image_out.append(text[match.start():match.end()])
            i = match.end()
            continue
        destination, end = parsed
        label = re.sub(r"\s+", " ", match.group(1)).strip()
        if _visual_candidate(destination, label, path):
            visuals.append({"path": path, "alt": label, "url": destination})
        image_out.append(f" Imagen: {label} " if _informative_alt(label) else " ")
        i = end

    image_cleaned = "".join(image_out)
    link_out: list[str] = []
    i = 0
    while True:
        match = LINK_REF_START_RE.search(image_cleaned, i)
        if not match:
            link_out.append(image_cleaned[i:])
            break
        link_out.append(image_cleaned[i:match.start()])
        parsed = _parse_destination(image_cleaned, match.end())
        if not parsed:
            link_out.append(image_cleaned[match.start():match.end()])
            i = match.end()
            continue
        destination, end = parsed
        label = re.sub(r"\s+", " ", match.group(1)).strip()
        if _evidence_link(destination, label, path):
            links.append({"path": path, "text": label, "url": destination})
        replacement = f" {label} "
        if destination.lower().startswith("mailto:"):
            email = destination[7:].split("?", 1)[0]
            if email and email.lower() not in label.lower():
                replacement += email + " "
        elif destination.lower().startswith("tel:"):
            phone = re.sub(r"[^+\d]", "", destination[4:])
            label_digits = re.sub(r"\D", "", label)
            if phone and len(label_digits) < 8:
                replacement += phone + " "
        link_out.append(replacement)
        i = end
    return "".join(link_out), visuals, links


def _replace_raw_urls(text: str, path: str, links: list[dict]) -> str:
    def repl(match: re.Match) -> str:
        url = match.group(0).rstrip(".,;:)")
        if _evidence_link(url, "", path):
            links.append({"path": path, "text": "", "url": url})
        return " "

    return RAW_URL_RE.sub(repl, text)


def _normalized_key(text: str) -> str:
    folded = _fold(text)
    return re.sub(r"[^a-z0-9%$+]+", " ", folded).strip()


def _normalize_path(path: str) -> tuple[str, bool]:
    """Canonicaliza rutas y marca variantes que sólo agregan tracking."""
    raw = path.strip() or "/"
    query = raw.split("?", 1)[1] if "?" in raw else ""
    tracking_only = bool(query) and all(
        part.split("=", 1)[0].lower().startswith(("_ga", "utm_", "gclid", "fbclid"))
        for part in query.split("&") if part
    )
    canonical = raw.split("?", 1)[0].split("#", 1)[0].rstrip("/") or "/"
    return canonical, tracking_only


def _has_protected_fact(text: str) -> bool:
    return bool(
        EMAIL_RE.search(text) or PERCENT_RE.search(text) or MONEY_RE.search(text)
        or CERT_RE.search(text) or _phone_values(text)
    )


def _phone_values(text: str) -> list[str]:
    phones: list[str] = []
    for match in PHONE_RE.finditer(text):
        value = match.group(0).strip()
        digits = re.sub(r"\D", "", value)
        if not 8 <= len(digits) <= 15:
            continue
        if re.fullmatch(r"20\d{2}[-/]\d{1,2}[-/]\d{1,2}(?:[- T]\d.*)?", value):
            continue
        if "." in value and " " not in value and value.count(".") >= 2:
            continue
        phones.append(value)
    return _unique(phones)


def extract_entities(text: str) -> dict[str, list[str]]:
    return {
        "emails": _unique(EMAIL_RE.findall(text), 50),
        "phones": _unique(_phone_values(text), 50),
        "percentages": _unique(PERCENT_RE.findall(text), 50),
        "money": _unique(MONEY_RE.findall(text), 50),
        "certifications": _unique(CERT_RE.findall(text), 50),
    }


def _categories(text: str, path: str = "/") -> list[str]:
    folded = _fold(text)
    path_folded = _fold(path)
    if any(term in folded for term in (
        "utilizamos cookies", "usamos cookies", "we use cookies", "web beacons",
        "tecnologias de rastreo", "datos personales", "aviso de privacidad",
    )) and not any(term in folded for term in ("caso de exito", "certificacion", "iso ")):
        return []
    if len(folded) > 180 and any(term in folded for term in (
        "no caigas en el fraude", "nunca solicitamos dinero", "proteger tu informacion",
        "actividad sospechosa", "no firmes ningun documento", "usurpacion de nombre",
    )):
        return []
    found: list[str] = []
    for category, terms in CATEGORY_TERMS.items():
        if any(term in folded for term in terms):
            found.append(category)
            continue
        if any(term in path_folded for term in PATH_CATEGORY_TERMS.get(category, ())):
            found.append(category)
    return found


def _split_long_line(line: str, limit: int = 900) -> list[str]:
    if len(line) <= limit or line.startswith("#"):
        return [line]
    sentences = re.split(r"(?<=[.!?])\s+", line)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= limit:
            current = f"{current} {sentence}".strip()
            continue
        if current:
            chunks.append(current)
        current = sentence
        while len(current) > limit:
            cut = current.rfind(" ", 0, limit)
            cut = cut if cut > limit // 2 else limit
            chunks.append(current[:cut].strip())
            current = current[cut:].strip()
    if current:
        chunks.append(current)
    return chunks


def _clean_line(raw: str, path: str) -> tuple[list[str], list[dict], list[dict], str | None]:
    original = raw
    line, visuals, links = _replace_markdown_refs(original, path)
    link_count = original.count("](") - original.count("![](")
    line = _replace_raw_urls(line, path, links)
    line = unescape(re.sub(r"<[^>]+>", " ", line))
    line = line.replace("\\(", "(").replace("\\)", ")")
    line = re.sub(r"^\s*>+\s?", "", line)
    line = re.sub(r"^\s*[-*+]\s+(?=\D)", "- ", line)
    line = re.sub(r"(?<!\w)[*_]{1,3}(?=\S)", "", line)
    line = re.sub(r"(?<=\S)[*_]{1,3}(?!\w)", "", line)
    line = re.sub(
        r"\b(?:Facebook|Instagram|LinkedIn|YouTube|TikTok|Twitter|X) page opens in new window\b",
        " ", line, flags=re.IGNORECASE,
    )
    line = re.sub(r"\b(?:Alternar men[uú]|Toggle menu|Go to\.\.)\b", " ", line, flags=re.IGNORECASE)
    line = re.sub(r"\]\((?:https?://|/)[^)]*\)", "", line)
    if line.startswith("[") and "]" not in line:
        line = line[1:]
    line = re.sub(r"[ \t]+", " ", line).strip(" \t|")

    if not line:
        return [], visuals, links, "empty"
    if re.fullmatch(r"[-=_~`#|: ]+", line) or TABLE_SEPARATOR_RE.match(line):
        return [], visuals, links, "separator"

    heading = HEADING_RE.match(line)
    heading_marks = heading.group(1) if heading else ""
    body = heading.group(2).strip() if heading else line
    folded = _fold(body).strip(" .:;,-")

    if any(folded.startswith(prefix) for prefix in UI_PREFIXES):
        return [], visuals, links, "ui"
    if folded in NAV_LABELS or folded in FORM_LABELS:
        return [], visuals, links, "nav_or_form"

    anchors = re.findall(r"\[([^\]]+)\]\(", original)
    nav_anchors = sum(1 for anchor in anchors if _fold(anchor).strip() in NAV_LABELS)
    if link_count >= 3 and anchors and nav_anchors / len(anchors) >= 0.6 and not _has_protected_fact(body):
        return [], visuals, links, "nav_cluster"

    alnum = re.sub(r"[^0-9A-Za-zÁÉÍÓÚÑáéíóúñ]", "", body)
    if len(alnum) < 2 and not _has_protected_fact(body):
        return [], visuals, links, "trivial"

    rendered = f"{heading_marks} {body}" if heading else body
    return _split_long_line(rendered), visuals, links, None


def _build_items(md: str, collect_visible: bool = True) -> tuple[list[dict], dict, str]:
    path = "/"
    skip_page = False
    items: list[dict] = []
    visuals: list[dict] = []
    links: list[dict] = []
    visible_lines: list[str] = []
    dropped = Counter()
    seen: dict[str, str] = {}
    duplicate_sources: dict[str, set[str]] = {}

    for raw in md.splitlines():
        page_match = PAGE_HEADER_RE.match(raw.strip())
        if page_match:
            path, skip_page = _normalize_path(page_match.group(1))
            continue
        if skip_page:
            dropped["tracking_page"] += 1
            continue

        raw_visuals: list[dict] = []
        raw_links: list[dict] = []
        if collect_visible:
            visible, raw_visuals, raw_links = _replace_markdown_refs(raw, path)
            visible = _replace_raw_urls(visible, path, raw_links)
            visible = re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", visible))).strip()
            if visible:
                visible_lines.append(visible)

        lines, line_visuals, line_links, reason = _clean_line(raw, path)
        visuals.extend(raw_visuals or line_visuals)
        links.extend(raw_links or line_links)
        if reason:
            dropped[reason] += 1
            continue

        for line in lines:
            key = _normalized_key(line)
            if key and key in seen:
                dropped["duplicate"] += 1
                duplicate_sources.setdefault(key, {seen[key]}).add(path)
                continue
            if key:
                seen[key] = path
            cats = _categories(line, path)
            protected = _has_protected_fact(line)
            items.append({
                "path": path,
                "text": line,
                "categories": cats,
                "protected": protected,
                "order": len(items),
            })

    visual_keys: set[tuple[str, str, str]] = set()
    clean_visuals: list[dict] = []
    for item in visuals:
        key = (item.get("path", ""), item.get("alt", ""), item.get("url", ""))
        if key not in visual_keys:
            visual_keys.add(key)
            clean_visuals.append(item)

    link_keys: set[tuple[str, str, str]] = set()
    clean_links: list[dict] = []
    for item in links:
        key = (item.get("path", ""), item.get("text", ""), item.get("url", ""))
        if key not in link_keys:
            link_keys.add(key)
            clean_links.append(item)

    metadata = {
        "version": CLEAN_VERSION,
        "input_chars": len(md),
        "input_lines": len(md.splitlines()),
        "dropped": dict(sorted(dropped.items())),
        "duplicate_groups": len(duplicate_sources),
        "visual_assets": clean_visuals[:50],
        "evidence_links": clean_links[:50],
    }
    return items, metadata, "\n".join(visible_lines)


def _render(items: list[dict]) -> str:
    pages: OrderedDict[str, list[str]] = OrderedDict()
    for item in items:
        pages.setdefault(item["path"], []).append(item["text"])
    chunks: list[str] = []
    for path, lines in pages.items():
        if not lines:
            continue
        chunks.append(f"# {path}\n" + "\n".join(lines))
    text = "\n\n".join(chunks)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _score(item: dict) -> float:
    text = item["text"]
    folded = _fold(text)
    score = 0.0
    score += min(len(text), 500) / 250
    score += 2.4 * len(item["categories"])
    if item["path"] == "/":
        score += 1.0
    if text.startswith("#"):
        score += 0.8
    if item.get("protected"):
        score += 1.5
    if re.search(r"\b\d{2,}\b", text):
        score += 0.5
    if any(term in folded for term in ("privacidad", "privacy", "terminos", "cookies")):
        score -= 8.0
    if any(term in _fold(item["path"]) for term in LOW_VALUE_PATH_TERMS):
        score -= 7.0
    if any(term in folded for term in (
        "web beacon", "datos personales", "tecnologias de rastreo", "usurpacion de nombre",
        "no caigas en el fraude", "actividad sospechosa", "proteger tu informacion",
    )):
        score -= 5.0
    if any(term in folded for term in ("domicilio", "telefono", "correo", "contacto")):
        score -= 0.5
    if len(text) < 25 and not item["categories"] and not item.get("protected"):
        score -= 1.5
    return score


def _select_context(items: list[dict], max_chars: int) -> list[dict]:
    if not items or max_chars <= 0:
        return []
    selected: set[int] = set()
    for item in items:
        item["score"] = _score(item)

    # Cobertura mínima: identidad/oferta/comprador/industria/prueba/B2B.
    for category in CATEGORY_TERMS:
        candidates = [item for item in items if category in item["categories"]]
        if candidates:
            useful = [item for item in candidates if not any(
                term in _fold(item["path"]) for term in LOW_VALUE_PATH_TERMS
            )]
            best = max(useful or candidates,
                       key=lambda item: (item["score"], -item["order"]))
            selected.add(best["order"])

    # El home suele contener la descripción más compacta aun sin palabras del diccionario.
    home = [
        item for item in items
        if item["path"] == "/" and len(item["text"]) >= 35 and item["score"] >= 0.5
    ]
    for item in sorted(home, key=lambda value: (-value["score"], value["order"]))[:3]:
        selected.add(item["order"])

    used = sum(len(items[index]["text"]) + 2 for index in selected)
    visual_count = sum(
        item["text"].lstrip("#- ").lower().startswith("imagen:")
        for item in items if item["order"] in selected
    )
    for item in sorted(items, key=lambda value: (-value["score"], value["order"])):
        if item["order"] in selected or item["score"] < 0.5:
            continue
        is_visual = item["text"].lstrip("#- ").lower().startswith("imagen:")
        if is_visual and visual_count >= 5:
            continue
        cost = len(item["text"]) + 2
        if used + cost > max_chars:
            continue
        selected.add(item["order"])
        used += cost
        visual_count += int(is_visual)

    ordered = [item for item in items if item["order"] in selected]
    # El render agrega headers; recorta por bloques, nunca a mitad de una evidencia.
    while ordered and len(_render(ordered)) > max_chars:
        counts = Counter(category for item in ordered for category in item["categories"])
        removable = [
            item for item in ordered
            if not item["categories"] or all(counts[category] > 1 for category in item["categories"])
        ]
        target = min(removable or ordered, key=lambda item: (item["score"], -item["order"]))
        ordered.remove(target)
    return ordered


def _entity_key(kind: str, value: str) -> str:
    if kind == "emails":
        return _fold(value).strip("_*")
    if kind == "phones":
        return re.sub(r"\D", "", value)
    if kind in {"percentages", "money"}:
        return re.sub(r"[\s,]", "", _fold(value))
    return _fold(value)


def _set_recall(kind: str, before: list[str], after: list[str]) -> float:
    source = {_entity_key(kind, value) for value in before if value}
    if not source:
        return 1.0
    target = {_entity_key(kind, value) for value in after if value}
    return len(source & target) / len(source)


def noise_line_count(text: str) -> int:
    count = 0
    for raw in text.splitlines():
        line = raw.lstrip("#- ").strip()
        if not line or line.startswith("/"):
            continue
        folded = _fold(line).strip(" .:;,-")
        if folded in NAV_LABELS or folded in FORM_LABELS:
            count += 1
        elif any(folded.startswith(prefix) for prefix in UI_PREFIXES):
            count += 1
    return count


def build_segmentation_context(md: str, max_context_chars: int = DEFAULT_CONTEXT_CHARS) -> dict:
    """Camino operativo rápido: construye sólo la vista que consume el LLM."""
    if not md:
        return {"text": "", "meta": {"version": CLEAN_VERSION, "input_chars": 0,
                                      "context_chars": 0, "context_categories": []}}
    items, meta, _ = _build_items(md, collect_visible=False)
    context_items = _select_context(items, max_context_chars)
    context = _render(context_items)
    meta.update({
        "context_chars": len(context),
        "clean_items": len(items),
        "context_items": len(context_items),
        "categories": sorted({category for item in items for category in item["categories"]}),
        "context_categories": sorted({
            category for item in context_items for category in item["categories"]
        }),
        "noise_lines_context": noise_line_count(context),
    })
    return {"text": context, "meta": meta}


def analyze_markdown(md: str, max_context_chars: int = DEFAULT_CONTEXT_CHARS) -> dict:
    if not md:
        return {
            "clean_text": "",
            "segmentation_context": "",
            "meta": {"version": CLEAN_VERSION, "input_chars": 0, "clean_chars": 0,
                     "context_chars": 0, "visual_assets": [], "evidence_links": []},
        }

    items, meta, visible_text = _build_items(md, collect_visible=True)
    clean_text = _render(items)
    context_items = _select_context(items, max_context_chars)
    context = _render(context_items)
    visible_entities = extract_entities(visible_text)
    clean_entities = extract_entities(clean_text)
    context_entities = extract_entities(context)
    category_input = sorted({category for item in items for category in item["categories"]})
    category_context = sorted({category for item in context_items for category in item["categories"]})
    source_categories = sorted(_categories(visible_text, "/"))

    meta.update({
        "clean_chars": len(clean_text),
        "context_chars": len(context),
        "clean_items": len(items),
        "context_items": len(context_items),
        "categories": category_input,
        "source_categories": source_categories,
        "context_categories": category_context,
        "source_entities": visible_entities,
        "entities": clean_entities,
        "noise_lines_clean": noise_line_count(clean_text),
        "noise_lines_context": noise_line_count(context),
        "entity_recall_clean": {
            key: round(_set_recall(key, values, clean_entities[key]), 4)
            for key, values in visible_entities.items()
        },
        "entity_recall_context": {
            key: round(_set_recall(key, values, context_entities[key]), 4)
            for key, values in visible_entities.items()
        },
    })
    return {"clean_text": clean_text, "segmentation_context": context, "meta": meta}


def clean_markdown(md: str) -> str:
    """API compatible: devuelve la vista completa limpia, sin aplicar presupuesto."""
    return analyze_markdown(md)["clean_text"]


def extract_visual_assets(md: str, path: str = "/") -> list[dict]:
    visuals: list[dict] = []
    for line in md.splitlines():
        _, found, _ = _replace_markdown_refs(line, path)
        visuals.extend(found)
    return visuals


def extract_evidence_links(md: str, path: str = "/") -> list[dict]:
    links: list[dict] = []
    for line in md.splitlines():
        visible, _, found = _replace_markdown_refs(line, path)
        _replace_raw_urls(visible, path, found)
        links.extend(found)
    unique: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for item in links:
        key = (item.get("path", ""), item.get("text", ""), item.get("url", ""))
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def attach_evidence_to_pages(pages: list[dict] | None, meta: dict) -> list[dict] | None:
    """Añade evidencia extraída a crawls legacy sin cambiar su forma ni su raw."""
    if not pages:
        return None
    enriched = [dict(page) for page in pages]
    by_path = {str(page.get("path") or "/").rstrip("/") or "/": page for page in enriched}
    for field in ("visual_assets", "evidence_links"):
        for evidence in meta.get(field) or []:
            path = str(evidence.get("path") or "/").rstrip("/") or "/"
            page = by_path.get(path)
            if page is None:
                continue
            values = page.setdefault(field, [])
            key = (evidence.get("url"), evidence.get("alt"), evidence.get("text"))
            existing = {
                (value.get("url"), value.get("alt"), value.get("text"))
                for value in values
            }
            if key not in existing:
                values.append(dict(evidence))
    return enriched


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="JSON de crawl con combined_markdown")
    parser.add_argument("--context", action="store_true", help="imprimir segmentation_context")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_CONTEXT_CHARS)
    parser.add_argument("--meta", action="store_true", help="imprimir metadata JSON")
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as handle:
        record = json.load(handle)
    result = analyze_markdown(record.get("combined_markdown", ""), args.max_chars)
    if args.meta:
        print(json.dumps(result["meta"], indent=2, ensure_ascii=False))
    else:
        print(result["segmentation_context"] if args.context else result["clean_text"])
