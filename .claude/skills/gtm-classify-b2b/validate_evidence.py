"""Pure helpers for validating classifier evidence against source clean_text."""


def evidence_fragments(value):
    if isinstance(value, str):
        value = value.strip()
        return [value] if value else []
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def evidence_is_exact(value, clean_text, label):
    """Unclear rows may explain missing content; every other quote must be literal."""
    if str(label or "").strip().lower() == "unclear":
        return True
    fragments = evidence_fragments(value)
    if not fragments or not isinstance(clean_text, str):
        return False
    return all(fragment in clean_text for fragment in fragments)


def find_evidence_failures(classifications, verifications, clean_texts):
    failures = []
    for domain, row in classifications.items():
        if not evidence_is_exact(row.get("evidence"), clean_texts.get(domain), row.get("label")):
            failures.append(f"{domain}:classify")
        verification = verifications.get(domain)
        if verification and not evidence_is_exact(
            verification.get("evidence"),
            clean_texts.get(domain),
            verification.get("verify_label"),
        ):
            failures.append(f"{domain}:verify")
    return failures
