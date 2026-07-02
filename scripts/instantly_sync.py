"""Sincroniza Instantly -> Supabase (capa de memoria del GTM OS).

Trae de la API v2 de Instantly los envíos y replies y los refleja en
`outreach_log` y `replies`, para que /gtm-check-contact y /gtm-reply-analysis
consulten una sola fuente de verdad.

Requiere en el entorno:
  INSTANTLY_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

Uso:
  python scripts/instantly_sync.py --workspace unprospect [--campaign <instantly_campaign_id>]

NOTA: escrito contra la API v2 de Instantly (https://developer.instantly.ai);
sin probar contra una cuenta real todavía — validar paginación y campos en la
primera corrida (paso 2 del roadmap en ARCHITECTURE.md).
"""

import argparse
import json
import os
import urllib.parse
import urllib.request

INSTANTLY_BASE = "https://api.instantly.ai/api/v2"


def instantly_get(path, params=None):
    url = INSTANTLY_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + os.environ["INSTANTLY_API_KEY"],
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def instantly_paginate(path, params=None):
    params = dict(params or {})
    params.setdefault("limit", 100)
    while True:
        page = instantly_get(path, params)
        items = page.get("items", [])
        yield from items
        cursor = page.get("next_starting_after")
        if not cursor or not items:
            break
        params["starting_after"] = cursor


def supabase_upsert(table, rows, on_conflict=None):
    if not rows:
        return
    url = os.environ["SUPABASE_URL"] + "/rest/v1/" + table
    if on_conflict:
        url += "?on_conflict=" + on_conflict
    token = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    req = urllib.request.Request(
        url,
        data=json.dumps(rows).encode(),
        headers={
            "apikey": token,
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        r.read()


def domain_of(email):
    return email.split("@", 1)[1].lower() if email and "@" in email else None


def sync_emails(workspace, campaign_id=None):
    """Emails enviados -> outreach_log; replies recibidos -> replies."""
    sent, replies = [], []
    for em in instantly_paginate("/emails", {"campaign_id": campaign_id}):
        lead = (em.get("lead") or em.get("to_address_email_list") or "").lower()
        if em.get("email_type") in ("sent", "SENT", 1, "1"):
            sent.append({
                "workspace": workspace,
                "lead_email": lead,
                "lead_domain": domain_of(lead),
                "angle_slug": None,  # se resuelve vía campaigns.instantly_campaign_id
                "sequence_step": em.get("step") or 1,
                "sent_at": em.get("timestamp_email") or em.get("timestamp_created"),
            })
        elif em.get("email_type") in ("received", "RECEIVED", 2, "2"):
            frm = (em.get("from_address_email") or "").lower()
            replies.append({
                "workspace": workspace,
                "lead_email": frm,
                "lead_domain": domain_of(frm),
                "replied_at": em.get("timestamp_email") or em.get("timestamp_created"),
                "body": (em.get("body") or {}).get("text") if isinstance(em.get("body"), dict) else em.get("body"),
                "instantly_reply_id": em.get("id"),
            })
    supabase_upsert("outreach_log", sent)
    supabase_upsert("replies", replies, on_conflict="instantly_reply_id")
    return len(sent), len(replies)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default="unprospect")
    ap.add_argument("--campaign", default=None, help="instantly_campaign_id; omitir para todas")
    args = ap.parse_args()
    n_sent, n_replies = sync_emails(args.workspace, args.campaign)
    print(f"synced outreach_log={n_sent} replies={n_replies} workspace={args.workspace}")


if __name__ == "__main__":
    main()
