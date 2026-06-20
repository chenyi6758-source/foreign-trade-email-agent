import base64
import hashlib
import hmac
from urllib.parse import urlencode

from app.config import Settings
from app.db import get_db


def _sign(email: str, settings: Settings) -> str:
    return hmac.new(settings.unsubscribe_secret.encode("utf-8"), email.lower().encode("utf-8"), hashlib.sha256).hexdigest()


def create_unsubscribe_token(email: str, settings: Settings) -> str:
    raw = f"{email.lower()}:{_sign(email, settings)}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def verify_unsubscribe_token(email: str, token: str, settings: Settings) -> bool:
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        token_email, signature = raw.rsplit(":", 1)
        if token_email != email.lower():
            return False
        return hmac.compare_digest(signature, _sign(email, settings))
    except Exception:
        return False


def unsubscribe_url(email: str, settings: Settings) -> str:
    base = settings.app_base_url.rstrip("/") + settings.unsubscribe_path
    return f"{base}?{urlencode({'email': email, 'token': create_unsubscribe_token(email, settings)})}"


def add_opt_out(email: str, reason: str = "unsubscribe page") -> None:
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM opt_outs WHERE email = ?", (email,)).fetchone()
        if existing:
            return
        conn.execute("INSERT INTO opt_outs(email, reason) VALUES (?, ?)", (email, reason))


def list_unsubscribe_header(email: str, settings: Settings) -> str:
    return f"<{unsubscribe_url(email, settings)}>"
