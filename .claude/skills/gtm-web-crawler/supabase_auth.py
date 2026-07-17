"""Resuelve una llave server-side vigente sin imprimir ni persistir secretos."""

from __future__ import annotations

import re

import requests


def _headers(key: str) -> dict[str, str]:
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def _works(url: str, key: str) -> bool:
    if not key:
        return False
    try:
        response = requests.get(
            f"{url.rstrip('/')}/rest/v1/site_crawls",
            params={"select": "domain", "limit": "1"},
            headers=_headers(key), timeout=30,
        )
        return response.status_code < 400
    except requests.RequestException:
        return False


def resolve_service_key(url: str, configured: str, management_token: str) -> str:
    if _works(url, configured):
        return configured
    if not management_token:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY fue rechazada y falta SUPABASE_TOKEN")
    match = re.search(r"https://([a-z0-9]+)\.supabase", url)
    if not match:
        raise RuntimeError("SUPABASE_URL no contiene un project ref válido")
    response = requests.get(
        f"https://api.supabase.com/v1/projects/{match.group(1)}/api-keys",
        params={"reveal": "true"},
        headers={"Authorization": f"Bearer {management_token}"}, timeout=60,
    )
    response.raise_for_status()
    keys = response.json()
    candidates = [
        item.get("api_key", "") for item in keys
        if item.get("type") == "secret" or item.get("name") == "service_role"
    ]
    for candidate in candidates:
        if _works(url, candidate):
            return candidate
    raise RuntimeError("No encontré una llave server-side vigente para site_crawls")
