"""Twenty CRM Integration — Person anlegen/updaten + Email-Custom-Object."""
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from .config import TWENTY_API_KEY, TWENTY_BASE_URL
from .forms import ParsedSubmit

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {TWENTY_API_KEY}",
    "Content-Type": "application/json",
}


async def find_person_by_email(client: httpx.AsyncClient, email: str) -> Optional[dict]:
    resp = await client.get(
        f"{TWENTY_BASE_URL}/rest/people",
        params={"filter": f"emails.primaryEmail[eq]:{email}"},
        headers=HEADERS,
    )
    resp.raise_for_status()
    data = resp.json()
    people = data.get("data", {}).get("people", []) or data.get("people", [])
    return people[0] if people else None


async def create_or_update_person(client: httpx.AsyncClient, submit: ParsedSubmit) -> str:
    existing = await find_person_by_email(client, submit.email)

    payload: dict = {
        "name": {"firstName": submit.firstname, "lastName": submit.lastname},
        "emails": {"primaryEmail": submit.email},
    }
    if submit.consent:
        payload["dsgvoConsentAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if existing:
        person_id = existing["id"]
        resp = await client.patch(
            f"{TWENTY_BASE_URL}/rest/people/{person_id}",
            json=payload,
            headers=HEADERS,
        )
        resp.raise_for_status()
        logger.info("Twenty CRM: Person %s aktualisiert", person_id)
    else:
        resp = await client.post(
            f"{TWENTY_BASE_URL}/rest/people",
            json=payload,
            headers=HEADERS,
        )
        resp.raise_for_status()
        resp_data = resp.json()
        person_id = (
            resp_data.get("data", {}).get("createPerson", {}).get("id")
            or resp_data.get("id")
        )
        logger.info("Twenty CRM: Person %s angelegt", person_id)

    return person_id


async def create_email_object(
    client: httpx.AsyncClient, submit: ParsedSubmit, person_id: str
) -> None:
    if not submit.message:
        return

    payload = {
        "direction": "IN",
        "fromAddress": submit.email,
        "name": submit.form_name,
        "bodyText": submit.message,
        "personId": person_id,
    }
    resp = await client.post(
        f"{TWENTY_BASE_URL}/rest/emailMessages",
        json=payload,
        headers=HEADERS,
    )
    if resp.status_code not in (200, 201):
        logger.warning("Twenty CRM: Email-Objekt konnte nicht angelegt werden: %s", resp.text)
    else:
        logger.info("Twenty CRM: Email-Objekt angelegt fuer Person %s", person_id)


async def handle_twenty_crm(submit: ParsedSubmit) -> None:
    crm_config = submit.form_config.get("twenty_crm", {})
    if not crm_config.get("create_person", False):
        return
    if not TWENTY_API_KEY:
        logger.warning("TWENTY_API_KEY nicht gesetzt — CRM-Integration uebersprungen")
        return

    async with httpx.AsyncClient(timeout=15.0) as client:
        person_id = await create_or_update_person(client, submit)
        await create_email_object(client, submit, person_id)
