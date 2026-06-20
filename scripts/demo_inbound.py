import asyncio
import os

import httpx


BASE_URL = "http://127.0.0.1:8000"
WEBHOOK_SHARED_SECRET = os.getenv("WEBHOOK_SHARED_SECRET", "change-this-webhook-secret")


async def main() -> None:
    headers = {"X-Webhook-Token": WEBHOOK_SHARED_SECRET}
    async with httpx.AsyncClient(timeout=20) as client:
        email_payload = {
            "from_email": "alice.buyer@example.com",
            "from_name": "Alice",
            "subject": "RFQ for CNC aluminum parts",
            "body": "Hi, please send quotation, MOQ and sample lead time for CNC aluminum parts. We are an importer in Germany.",
            "source": "demo",
        }
        email_response = await client.post(f"{BASE_URL}/webhooks/email", json=email_payload, headers=headers)
        print("Email webhook:", email_response.status_code, email_response.json())

        whatsapp_payload = {
            "from_phone": "+15551234567",
            "from_name": "Carlos",
            "body": "Need price for industrial valves, 500 pcs monthly. Can you quote?",
            "source": "demo",
        }
        whatsapp_response = await client.post(f"{BASE_URL}/webhooks/whatsapp", json=whatsapp_payload, headers=headers)
        print("WhatsApp webhook:", whatsapp_response.status_code, whatsapp_response.json())


if __name__ == "__main__":
    asyncio.run(main())
