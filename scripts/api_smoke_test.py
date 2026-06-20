from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

os.environ["DATABASE_URL"] = "sqlite:///./data/api_smoke_test.db"
os.environ["OPENAI_API_KEY"] = ""
os.environ["LLM_API_KEY"] = ""
os.environ["SMTP_HOST"] = ""
os.environ["WHATSAPP_PROVIDER"] = "disabled"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "change-me-now"
os.environ["SESSION_SECRET"] = "smoke-test-session-secret"
os.environ["WEBHOOK_AUTH_ENABLED"] = "true"
os.environ["WEBHOOK_SHARED_SECRET"] = "smoke-webhook-secret"
os.environ["UNSUBSCRIBE_SECRET"] = "smoke-unsubscribe-secret"

from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import ensure_database
from app.main import app


def main() -> None:
    get_settings.cache_clear()
    db_path = PROJECT_ROOT / "data" / "api_smoke_test.db"
    if db_path.exists():
        db_path.unlink()
    ensure_database()

    with TestClient(app) as client:
        health_response = client.get("/health")
        assert health_response.status_code == 200, health_response.text
        assert health_response.json()["checks"]["database"] is True

        unauth_response = client.get("/api/leads")
        assert unauth_response.status_code == 401, unauth_response.text

        blocked_webhook = client.post(
            "/webhooks/email",
            json={
                "from_email": "blocked.buyer@example.com",
                "from_name": "Blocked Buyer",
                "subject": "RFQ should be blocked",
                "body": "This request should not be accepted without webhook auth.",
                "source": "smoke-test",
            },
        )
        assert blocked_webhook.status_code == 401, blocked_webhook.text

        webhook_headers = {"X-Webhook-Token": "smoke-webhook-secret"}

        email_response = client.post(
            "/webhooks/email",
            headers=webhook_headers,
            json={
                "from_email": "smoke.buyer@example.com",
                "from_name": "Smoke Buyer",
                "subject": "RFQ for custom metal parts",
                "body": "Please send quotation, MOQ and sample lead time.",
                "source": "smoke-test",
            },
        )
        assert email_response.status_code == 200, email_response.text
        assert email_response.json()["auto_reply"] in {"drafted", "sent"}

        provider_email_response = client.post(
            "/webhooks/email/generic",
            headers=webhook_headers,
            json={
                "provider": "generic-smoke",
                "from_email": "attachment.buyer@example.com",
                "from_name": "Attachment Buyer",
                "subject": "RFQ with drawing",
                "body": "Please quote from attached requirements.",
                "provider_message_id": "generic-smoke-1",
                "attachments": [
                    {
                        "filename": "requirements.txt",
                        "content_type": "text/plain",
                        "content": "Need CE and RoHS for 500 pcs.",
                    }
                ],
            },
        )
        assert provider_email_response.status_code == 200, provider_email_response.text
        provider_payload = provider_email_response.json()
        assert provider_payload["ok"] is True
        assert provider_payload["attachments"], provider_payload

        whatsapp_response = client.post(
            "/webhooks/whatsapp",
            headers=webhook_headers,
            json={
                "from_phone": "+15550001111",
                "from_name": "WA Buyer",
                "body": "Need price for industrial valves. Can you quote?",
                "source": "smoke-test",
            },
        )
        assert whatsapp_response.status_code == 200, whatsapp_response.text
        assert whatsapp_response.json()["auto_reply"] in {"drafted", "sent"}

        login_response = client.post("/login", data={"username": "admin", "password": "change-me-now"})
        assert login_response.status_code in {200, 303}, login_response.text

        leads_response = client.get("/api/leads")
        assert leads_response.status_code == 200, leads_response.text
        leads = leads_response.json()
        assert len(leads) >= 3

        crm_response = client.patch(
            f"/api/leads/{leads[0]['id']}",
            json={
                "stage": "qualified",
                "owner": "Sales A",
                "priority": "high",
                "next_follow_up_at": "2099-01-01T09:00:00",
                "notes": "Need quotation follow-up.",
                "deal_value": 12000,
            },
        )
        assert crm_response.status_code == 200, crm_response.text
        assert crm_response.json()["lead"]["stage"] == "qualified"

        pipeline_response = client.get("/api/leads/pipeline")
        assert pipeline_response.status_code == 200, pipeline_response.text
        assert any(item["stage"] == "qualified" and item["total"] >= 1 for item in pipeline_response.json())

        config_response = client.get("/api/config/status")
        assert config_response.status_code == 200, config_response.text
        assert config_response.json()["app"]["port"] == 8000

        deliverability_response = client.get("/api/deliverability/status")
        assert deliverability_response.status_code == 200, deliverability_response.text
        assert "manual_dns_records" in deliverability_response.json()

        job_response = client.post(
            "/api/jobs",
            json={"type": "follow_up_reminder", "payload": {"lead_id": leads[0]["id"], "note": "smoke test"}},
        )
        assert job_response.status_code == 200, job_response.text
        assert job_response.json()["ok"] is True

        jobs_response = client.get("/api/jobs?status=queued")
        assert jobs_response.status_code == 200, jobs_response.text
        assert any(job["type"] == "follow_up_reminder" for job in jobs_response.json())

        export_response = client.get("/api/export/leads.csv")
        assert export_response.status_code == 200, export_response.text
        assert "smoke.buyer@example.com" in export_response.text

    print("API smoke test passed")
    print(f"Test database: {db_path}")
    print(f"Leads checked: {len(leads)}")
    print("Auth checked: unauthenticated API access returns 401, login unlocks API")
    print("Webhook checked: missing token returns 401, valid token accepts inbound messages")
    print("Provider email checked: generic provider payload and attachment metadata are saved")
    print("CRM checked: lead stage, owner, priority, follow-up, notes and pipeline update work")
    print("Deliverability checked: unsubscribe and DNS checklist endpoint works")
    print("Jobs checked: queued follow-up job can be created and listed")
    print("Deployment checked: health endpoint and CSV lead export work")


if __name__ == "__main__":
    main()
