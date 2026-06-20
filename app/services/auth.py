import base64
import hashlib
import hmac
import time

from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.config import Settings, get_settings


def _sign(payload: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_credentials(username: str, password: str, settings: Settings) -> bool:
    return hmac.compare_digest(username, settings.admin_username) and hmac.compare_digest(password, settings.admin_password)


def create_session_token(username: str, settings: Settings) -> str:
    expires_at = int(time.time() + settings.session_ttl_hours * 3600)
    payload = f"{username}:{expires_at}"
    signature = _sign(payload, settings.session_secret)
    raw = f"{payload}:{signature}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def verify_session_token(token: str | None, settings: Settings) -> str | None:
    if not token:
        return None
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        username, expires_at_text, signature = raw.rsplit(":", 2)
        payload = f"{username}:{expires_at_text}"
        if not hmac.compare_digest(signature, _sign(payload, settings.session_secret)):
            return None
        if int(expires_at_text) < int(time.time()):
            return None
        if username != settings.admin_username:
            return None
        return username
    except Exception:
        return None


def current_admin(request: Request) -> str | None:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    return verify_session_token(token, settings)


def require_admin(request: Request) -> str:
    username = current_admin(request)
    if username:
        return username
    if request.url.path.startswith("/api"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required.")
    raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/login"})


def set_session_cookie(response: RedirectResponse, username: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=create_session_token(username, settings),
        httponly=True,
        samesite="lax",
        max_age=settings.session_ttl_hours * 3600,
    )


def clear_session_cookie(response: RedirectResponse, settings: Settings) -> None:
    response.delete_cookie(settings.session_cookie_name)
