from app.config import Settings
from app.db import get_db
from app.services.unsubscribe import unsubscribe_url


def is_opted_out(email: str | None = None, phone: str | None = None) -> bool:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT id FROM opt_outs
            WHERE (:email != '' AND email = :email)
               OR (:phone != '' AND phone = :phone)
            LIMIT 1
            """,
            {"email": email or "", "phone": phone or ""},
        ).fetchone()
    return row is not None


def cold_outreach_allowed(settings: Settings, consent_status: str) -> tuple[bool, str]:
    if settings.require_approval_for_cold_outreach:
        return False, "Cold outreach requires manual approval before sending."
    if consent_status not in {"opted_in", "customer", "active_inquiry"}:
        return False, "Recipient consent is unknown. Create a draft and review it first."
    return True, "Allowed."


def append_unsubscribe(body: str, settings: Settings, email: str | None = None) -> str:
    if settings.unsubscribe_text.lower() in body.lower():
        return body
    footer = settings.unsubscribe_text
    if settings.unsubscribe_enabled and email:
        footer = f"{footer}\nUnsubscribe: {unsubscribe_url(email, settings)}"
    return f"{body.rstrip()}\n\n{footer}"
