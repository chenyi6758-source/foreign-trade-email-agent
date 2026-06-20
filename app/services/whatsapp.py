import base64

import httpx

from app.config import Settings


async def send_whatsapp(to_phone: str, body: str, settings: Settings) -> str:
    provider = settings.whatsapp_provider.lower()
    if provider == "disabled":
        raise RuntimeError("WHATSAPP_PROVIDER is disabled.")
    if provider == "twilio":
        return await _send_twilio(to_phone, body, settings)
    if provider == "meta":
        return await _send_meta(to_phone, body, settings)
    raise RuntimeError(f"Unsupported WHATSAPP_PROVIDER: {settings.whatsapp_provider}")


async def _send_twilio(to_phone: str, body: str, settings: Settings) -> str:
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        raise RuntimeError("Twilio credentials are not configured.")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    auth = base64.b64encode(f"{settings.twilio_account_sid}:{settings.twilio_auth_token}".encode()).decode()
    payload = {
        "From": settings.twilio_whatsapp_from,
        "To": to_phone if to_phone.startswith("whatsapp:") else f"whatsapp:{to_phone}",
        "Body": body,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, data=payload, headers={"Authorization": f"Basic {auth}"})
        response.raise_for_status()
        return response.json().get("sid", "twilio-sent")


async def _send_meta(to_phone: str, body: str, settings: Settings) -> str:
    if not settings.meta_whatsapp_token or not settings.meta_whatsapp_phone_number_id:
        raise RuntimeError("Meta WhatsApp credentials are not configured.")

    url = f"https://graph.facebook.com/v21.0/{settings.meta_whatsapp_phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone.replace("whatsapp:", "").replace("+", ""),
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }
    headers = {"Authorization": f"Bearer {settings.meta_whatsapp_token}"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        messages = data.get("messages") or []
        return messages[0].get("id", "meta-sent") if messages else "meta-sent"
