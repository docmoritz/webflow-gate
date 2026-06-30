"""AWeber Integration — Tags setzen mit OAuth Token-Refresh."""
import json
import logging
from pathlib import Path
from typing import Optional

import httpx

from .config import (
    AWEBER_ACCOUNT_ID,
    AWEBER_CLIENT_ID,
    AWEBER_CLIENT_SECRET,
    AWEBER_TOKEN_FILE,
)
from .forms import ParsedSubmit

logger = logging.getLogger(__name__)

AWEBER_TOKEN_URL = "https://auth.aweber.com/oauth2/token"
AWEBER_API_BASE = "https://api.aweber.com/1.0"


def _load_tokens() -> Optional[dict]:
    path = Path(AWEBER_TOKEN_FILE)
    if not path.exists():
        logger.warning("AWeber Token-Datei nicht gefunden: %s", AWEBER_TOKEN_FILE)
        return None
    with open(path) as f:
        return json.load(f)


def _save_tokens(tokens: dict) -> None:
    path = Path(AWEBER_TOKEN_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(tokens, f)


async def _refresh_access_token(client: httpx.AsyncClient, refresh_token: str) -> dict:
    resp = await client.post(
        AWEBER_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": AWEBER_CLIENT_ID,
            "client_secret": AWEBER_CLIENT_SECRET,
        },
    )
    resp.raise_for_status()
    tokens = resp.json()
    _save_tokens(tokens)
    logger.info("AWeber: Access-Token erneuert")
    return tokens


async def _get_valid_access_token(client: httpx.AsyncClient) -> Optional[str]:
    tokens = _load_tokens()
    if not tokens:
        return None

    access_token = tokens.get("access_token")
    if not access_token:
        return None

    test_resp = await client.get(
        f"{AWEBER_API_BASE}/accounts/{AWEBER_ACCOUNT_ID}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if test_resp.status_code == 401:
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            logger.error("AWeber: Kein Refresh-Token vorhanden")
            return None
        tokens = await _refresh_access_token(client, refresh_token)
        access_token = tokens.get("access_token")

    return access_token


async def _find_subscriber(
    client: httpx.AsyncClient, access_token: str, list_id: str, email: str
) -> Optional[dict]:
    resp = await client.get(
        f"{AWEBER_API_BASE}/accounts/{AWEBER_ACCOUNT_ID}/lists/{list_id}/subscribers",
        params={"ws.op": "find", "email": email},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if resp.status_code != 200:
        return None
    entries = resp.json().get("entries", [])
    return entries[0] if entries else None


async def _add_subscriber(
    client: httpx.AsyncClient,
    access_token: str,
    list_id: str,
    email: str,
    firstname: str,
    lastname: str,
    tags: list[str],
) -> None:
    payload = {
        "ws.op": "create",
        "email": email,
        "name": f"{firstname} {lastname}".strip(),
        "tags": __import__("json").dumps(tags),
        "update_existing": True,
        "ip_address": "127.0.0.1",
    }
    resp = await client.post(
        f"{AWEBER_API_BASE}/accounts/{AWEBER_ACCOUNT_ID}/lists/{list_id}/subscribers",
        data=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if resp.status_code not in (200, 201):
        logger.warning("AWeber: Subscriber anlegen fehlgeschlagen: %s", resp.text)
    else:
        logger.info("AWeber: Subscriber %s angelegt/aktualisiert mit Tags %s", email, tags)


async def _set_tags_on_subscriber(
    client: httpx.AsyncClient,
    access_token: str,
    subscriber_url: str,
    tags: list[str],
) -> None:
    resp = await client.patch(
        subscriber_url,
        json={"tags": {"add": tags, "remove": []}},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )
    if resp.status_code not in (200, 204):
        logger.warning("AWeber: Tags setzen fehlgeschlagen: %s", resp.text)
    else:
        logger.info("AWeber: Tags %s gesetzt", tags)


async def handle_aweber(submit: ParsedSubmit) -> None:
    aweber_config = submit.form_config.get("aweber", {})
    list_id = aweber_config.get("list_id", "")
    tags = aweber_config.get("tags", [])

    if not list_id or not tags:
        return
    if not AWEBER_CLIENT_ID:
        logger.warning("AWEBER_CLIENT_ID nicht gesetzt — AWeber-Integration uebersprungen")
        return

    async with httpx.AsyncClient(timeout=15.0) as client:
        access_token = await _get_valid_access_token(client)
        if not access_token:
            logger.error("AWeber: Kein gueltiger Access-Token — Tags nicht gesetzt")
            return

        subscriber = await _find_subscriber(client, access_token, list_id, submit.email)
        if subscriber:
            subscriber_url = subscriber.get("self_link", "")
            if subscriber_url:
                await _set_tags_on_subscriber(client, access_token, subscriber_url, tags)
        else:
            await _add_subscriber(
                client, access_token, list_id,
                submit.email, submit.firstname, submit.lastname, tags,
            )
