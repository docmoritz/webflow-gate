"""AR-Ablage-Weiterleitung — schickt Formular-Nachrichten an msc-email-gate,
damit sie wie andere E-Mail-Objekte in der welt-neutralen AR-Ablage landen."""
import logging

import httpx

from .config import MSC_EMAIL_GATE_API_KEY, MSC_EMAIL_GATE_URL
from .forms import ParsedSubmit

logger = logging.getLogger(__name__)


async def handle_ar_ablage(submit: ParsedSubmit) -> None:
    ablage_config = submit.form_config.get("ar_ablage", {})
    empfaenger = ablage_config.get("empfaenger", "")

    if not empfaenger:
        return
    if not MSC_EMAIL_GATE_URL or not MSC_EMAIL_GATE_API_KEY:
        logger.warning("MSC_EMAIL_GATE_URL/API_KEY nicht gesetzt — AR-Ablage uebersprungen")
        return

    name = f"{submit.firstname} {submit.lastname}".strip() or submit.email
    text = f"Name: {name}\nEmail: {submit.email}\n\nNachricht:\n{submit.message}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{MSC_EMAIL_GATE_URL}/internal/ingest-form",
            json={
                "email": submit.email,
                "betreff": f"Webflow-Formular: {submit.form_name}",
                "text": text,
                "empfaenger": empfaenger,
            },
            headers={"X-Api-Key": MSC_EMAIL_GATE_API_KEY},
        )
        if resp.status_code != 200:
            logger.warning("AR-Ablage-Ingest fehlgeschlagen: %s", resp.text)
        else:
            logger.info("AR-Ablage-Ingest gesendet fuer %s", submit.email)
