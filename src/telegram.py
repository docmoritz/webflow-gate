"""Telegram AR-Benachrichtigung."""
import logging

import httpx

from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from .forms import ParsedSubmit

logger = logging.getLogger(__name__)


async def handle_telegram(submit: ParsedSubmit) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram nicht konfiguriert — Push uebersprungen")
        return

    name = f"{submit.firstname} {submit.lastname}".strip() or submit.email
    has_message = "— Nachricht vorhanden" if submit.message else ""
    text = f"Neue Kontaktanfrage [{submit.welt.upper()}]: {name} ({submit.email}) {has_message}".strip()

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
        )
        if resp.status_code != 200:
            logger.warning("Telegram Push fehlgeschlagen: %s", resp.text)
        else:
            logger.info("Telegram Push gesendet: %s", text)
