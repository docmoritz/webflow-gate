---
name: Webflow Gate
typ: dienst
zweck: Empfaengt Webflow-Formular-Submits per Webhook und erzeugt daraus CRM-Eintraege, AWeber-Tags und AR-Benachrichtigungen
trigger: permanent
output: HTTP-API (Webhook-Endpunkt)
abhaengigkeiten: webflow, twenty-crm, aweber, telegram
endpunkt: https://mailgate.docmoritz.academy/webhook/webflow-form
repo: docmoritz/webflow-gate
wiki: true
---

# Webflow Gate

Weltübergreifender Dienst der Webflow-Formular-Submits empfängt und daraus:
- **Twenty CRM** — Person anlegen/updaten + Nachricht als Email-Custom-Object
- **AWeber** — Tags setzen (OAuth mit Token-Refresh)
- **Telegram** — AR-Benachrichtigung senden

Die Formular-Konfiguration liegt in `forms.yaml` im Repo-Root.

## Technisches

**Entry-Point:** `src/main.py` → FastAPI-App `app`

**Starten:**
```bash
# Docker (Produktion via Coolify)
docker build -t webflow-gate .
docker run --env-file .env -p 8000:8000 webflow-gate

# Lokal (Entwicklung)
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Wichtige Env-Vars (siehe `.env.example`):**

| Variable | Zweck |
|---|---|
| `WEBFLOW_WEBHOOK_SECRET` | HMAC-Signatur-Prüfung für Webflow-Webhooks |
| `TWENTY_API_KEY` | Twenty CRM REST API Key |
| `TWENTY_BASE_URL` | Twenty CRM Base URL (Standard: https://crm.docmoritz.academy) |
| `AWEBER_CLIENT_ID` | AWeber OAuth Client ID |
| `AWEBER_CLIENT_SECRET` | AWeber OAuth Client Secret |
| `AWEBER_ACCOUNT_ID` | AWeber Account ID (1450640) |
| `AWEBER_TOKEN_FILE` | Pfad zur Token-Datei (Standard: /data/aweber_tokens.json) |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID für AR-Benachrichtigungen |

## Traefik-Routing

```
mailgate.docmoritz.academy/webhook/webflow-* → webflow-gate Container (Port 8000)
```

## Formular-Konfiguration

Neue Formulare in `forms.yaml` eintragen. Das Feld `field_map` unterstützt zwei Varianten:
- `name_full`: Vollname → wird am ersten Leerzeichen in `firstname`/`lastname` gesplittet
- `firstname` + `lastname`: direkte Felder
