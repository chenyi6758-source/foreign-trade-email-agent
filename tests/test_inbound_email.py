from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import get_db
from app.services.inbound_email import parse_mailgun_form, parse_postmark_json


def test_provider_parsers_extract_sender_and_body():
    mailgun = parse_mailgun_form(
        {
            "sender": "buyer@example.com",
            "from": "Buyer <buyer@example.com>",
            "subject": "RFQ",
            "body-plain": "Please quote 1000 pcs.",
            "Message-Id": "mg-1",
        }
    )
    assert mailgun.provider == "mailgun"
    assert mailgun.from_email == "buyer@example.com"
    assert mailgun.body == "Please quote 1000 pcs."

    postmark = parse_postmark_json(
        {
            "FromFull": {"Email": "alice@example.com", "Name": "Alice"},
            "Subject": "Quotation request",
            "TextBody": "Need price and MOQ.",
            "MessageID": "pm-1",
            "Attachments": [{"Name": "drawing.pdf", "ContentType": "application/pdf"}],
        }
    )
    assert postmark.provider == "postmark"
    assert postmark.from_name == "Alice"
    assert len(postmark.attachments) == 1


def test_generic_email_webhook_records_attachment(tmp_path, monkeypatch):
    db_path = tmp_path / "app.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("WEBHOOK_SHARED_SECRET", "test-secret")
    monkeypatch.setenv("WEBHOOK_AUTH_ENABLED", "true")
    get_settings.cache_clear()

    from app.main import app

    with TestClient(app) as client:
        response = client.post(
            "/webhooks/email/generic",
            headers={"X-Webhook-Token": "test-secret"},
            json={
                "provider": "generic-test",
                "from_email": "buyer@example.com",
                "from_name": "Buyer",
                "subject": "RFQ for solar lights",
                "body": "Please quote solar lights with CE certificate.",
                "provider_message_id": "generic-1",
                "attachments": [
                    {
                        "filename": "requirements.txt",
                        "content_type": "text/plain",
                        "content": "Need CE and RoHS.",
                    }
                ],
            },
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["lead"]["email"] == "buyer@example.com"
    assert payload["message"]["provider_message_id"] == "generic-1"
    assert payload["attachments"][0]["filename"] == "requirements.txt"
    assert payload["attachments"][0]["sha256"]

    with get_db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inbound_attachments").fetchone()[0] == 1
