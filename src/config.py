import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

WEBFLOW_WEBHOOK_SECRET: str = os.environ.get("WEBFLOW_WEBHOOK_SECRET", "")

TWENTY_API_KEY: str = os.environ.get("TWENTY_API_KEY", "")
TWENTY_BASE_URL: str = os.environ.get("TWENTY_BASE_URL", "https://crm.docmoritz.academy")

AWEBER_CLIENT_ID: str = os.environ.get("AWEBER_CLIENT_ID", "")
AWEBER_CLIENT_SECRET: str = os.environ.get("AWEBER_CLIENT_SECRET", "")
AWEBER_ACCOUNT_ID: str = os.environ.get("AWEBER_ACCOUNT_ID", "1450640")
AWEBER_TOKEN_FILE: str = os.environ.get("AWEBER_TOKEN_FILE", "/data/aweber_tokens.json")

TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_AUFSICHTSRAT_CHAT_ID", "")

MSC_EMAIL_GATE_URL: str = os.environ.get("MSC_EMAIL_GATE_URL", "")
MSC_EMAIL_GATE_API_KEY: str = os.environ.get("MSC_EMAIL_GATE_API_KEY", "")

_forms_path = Path(__file__).parent.parent / "forms.yaml"

def load_forms() -> dict:
    with open(_forms_path) as f:
        return yaml.safe_load(f).get("forms", {})
