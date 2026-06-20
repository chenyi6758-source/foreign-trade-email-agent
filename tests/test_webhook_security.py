import hashlib
import hmac

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.config import Settings, get_settings
from app.services.webhook_security import require_webhook_auth


def make_request(headers: dict[str, str], body: bytes = b'{"ok":true}') -> Request:
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/webhooks/email",
            "headers": [(key.lower().encode(), value.encode()) for key, value in headers.items()],
        },
        receive,
    )


@pytest.mark.asyncio
async def test_webhook_token_and_signature_auth(monkeypatch):
    settings = Settings(webhook_auth_enabled=True, webhook_shared_secret="secret")
    monkeypatch.setattr("app.services.webhook_security.get_settings", lambda: settings)

    await require_webhook_auth(make_request({"X-Webhook-Token": "secret"}))

    body = b'{"message":"hello"}'
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    await require_webhook_auth(make_request({"X-Webhook-Signature": f"sha256={signature}"}, body))

    with pytest.raises(HTTPException):
        await require_webhook_auth(make_request({"X-Webhook-Token": "wrong"}))
