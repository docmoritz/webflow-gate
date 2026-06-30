"""Webflow Gate — FastAPI-Hauptmodul."""
import asyncio
import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from .config import WEBFLOW_WEBHOOK_SECRET, load_forms
from .forms import parse_submit
from .twenty_crm import handle_twenty_crm
from .aweber import handle_aweber
from .telegram import handle_telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Webflow Gate", version="1.0.0")


def _verify_signature(body: bytes, signature: str) -> bool:
    if not WEBFLOW_WEBHOOK_SECRET:
        logger.warning("WEBFLOW_WEBHOOK_SECRET nicht gesetzt — Signatur-Prüfung deaktiviert")
        return True
    expected = hmac.new(
        WEBFLOW_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature.lower())


@app.post("/webhook/webflow-form")
async def webflow_form(request: Request, x_webflow_signature: str = Header(default="")):
    body = await request.body()

    if x_webflow_signature and not _verify_signature(body, x_webflow_signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    form_name = payload.get("name") or payload.get("data", {}).get("name", "")
    raw_data: dict[str, Any] = payload.get("data", payload)

    forms = load_forms()

    if form_name not in forms:
        logger.info("Unbekanntes Formular '%s' empfangen — ignoriert", form_name)
        return JSONResponse({"status": "ignored", "form": form_name})

    form_config = forms[form_name]
    submit = parse_submit(form_name, raw_data, form_config)

    logger.info(
        "Formular '%s' empfangen von %s %s <%s>",
        form_name, submit.firstname, submit.lastname, submit.email,
    )

    await asyncio.gather(
        handle_twenty_crm(submit),
        handle_aweber(submit),
        handle_telegram(submit),
        return_exceptions=True,
    )

    return JSONResponse({"status": "ok", "form": form_name})


@app.get("/health")
async def health():
    return {"status": "ok"}
