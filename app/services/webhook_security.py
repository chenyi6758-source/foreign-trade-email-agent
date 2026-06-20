import hashlib
import hmac

from fastapi import HTTPException, Request, status

from app.config import Settings, get_settings


def _normalize_signature(value: str) -> str:
    value = value.strip()
    if value.startswith("sha256="):
        return value.removeprefix("sha256=").strip()
    return value


def _expected_signature(body: bytes, settings: Settings) -> str:
    return hmac.new(settings.webhook_shared_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


async def require_webhook_auth(request: Request) -> None:
    settings = get_settings()
    if not settings.webhook_auth_enabled:
        return

    token = request.headers.get(settings.webhook_token_header)
    if token and hmac.compare_digest(token, settings.webhook_shared_secret):
        return

    signature = request.headers.get(settings.webhook_signature_header)
    if signature:
        body = await request.body()
        expected = _expected_signature(body, settings)
        if hmac.compare_digest(_normalize_signature(signature), expected):
            return

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook authentication.")
