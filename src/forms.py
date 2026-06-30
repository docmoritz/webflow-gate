"""Formular-Parser: normalisiert Webflow-Felder auf kanonisches Format."""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ParsedSubmit:
    form_name: str
    welt: str
    firstname: str
    lastname: str
    email: str
    message: str
    consent: bool
    form_config: dict


def parse_submit(form_name: str, raw_data: dict, form_config: dict) -> ParsedSubmit:
    """Normalisiert Webflow-Felder anhand der field_map aus forms.yaml."""
    field_map = form_config.get("field_map", {})

    def get_field(logical_key: str) -> str:
        webflow_key = field_map.get(logical_key, logical_key)
        return str(raw_data.get(webflow_key, "")).strip()

    firstname = get_field("firstname")
    lastname = get_field("lastname")

    if not firstname and not lastname:
        full = get_field("name_full")
        if full:
            parts = full.split(" ", 1)
            firstname = parts[0]
            lastname = parts[1] if len(parts) > 1 else ""

    email = get_field("email")
    message = get_field("message")
    consent_raw = get_field("consent")
    consent = consent_raw.lower() in ("true", "1", "yes", "on", "checked")

    return ParsedSubmit(
        form_name=form_name,
        welt=form_config.get("welt", "unknown"),
        firstname=firstname,
        lastname=lastname,
        email=email,
        message=message,
        consent=consent,
        form_config=form_config,
    )
