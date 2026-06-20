import re
from dataclasses import dataclass

from app.config import get_settings
from app.db import get_db


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
COMPANY_HINT_RE = re.compile(r"\b(?:company|co\.|ltd|llc|inc|gmbh|sarl|pte|limited)\b", re.I)


@dataclass
class LeadSignal:
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    channel: str = "email"
    message: str = ""


def infer_company(text: str, fallback_name: str | None = None) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[-6:]:
        if COMPANY_HINT_RE.search(line) and len(line) < 120:
            return line
    return fallback_name if fallback_name and COMPANY_HINT_RE.search(fallback_name) else None


def score_lead(message: str) -> tuple[int, list[str]]:
    settings = get_settings()
    text = message.lower()
    score = 10
    tags: list[str] = []

    intent_words = {
        "rfq": 25,
        "quote": 20,
        "quotation": 20,
        "price": 15,
        "moq": 15,
        "sample": 15,
        "tender": 20,
        "distributor": 20,
        "importer": 15,
        "urgent": 10,
    }
    for word, points in intent_words.items():
        if word in text:
            score += points
            tags.append(word)

    for keyword in settings.keywords:
        if keyword and keyword in text:
            score += 8
            tags.append(keyword)

    if EMAIL_RE.search(message):
        score += 10
        tags.append("email_found")

    return min(score, 100), sorted(set(tags))


def upsert_lead(signal: LeadSignal) -> dict:
    score, tags = score_lead(signal.message)
    company = signal.company or infer_company(signal.message, signal.name)

    with get_db() as conn:
        existing = None
        if signal.email:
            existing = conn.execute("SELECT * FROM leads WHERE email = ?", (signal.email,)).fetchone()
        if existing is None and signal.phone:
            existing = conn.execute("SELECT * FROM leads WHERE phone = ?", (signal.phone,)).fetchone()

        if existing:
            lead_id = existing["id"]
            merged_tags = ",".join(sorted(set((existing["tags"] or "").split(",") + tags) - {""}))
            conn.execute(
                """
                UPDATE leads
                SET name = COALESCE(NULLIF(?, ''), name),
                    company = COALESCE(NULLIF(?, ''), company),
                    score = MAX(score, ?),
                    tags = ?,
                    status = CASE WHEN status = 'new' THEN 'active' ELSE status END,
                    last_message_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (signal.name or "", company or "", score, merged_tags, lead_id),
            )
        else:
            cur = conn.execute(
                """
                INSERT INTO leads(channel, name, email, phone, company, score, tags, consent_status, last_message_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active_inquiry', CURRENT_TIMESTAMP)
                """,
                (signal.channel, signal.name, signal.email, signal.phone, company, score, ",".join(tags)),
            )
            lead_id = int(cur.lastrowid)

        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(row)


def record_message(
    lead_id: int | None,
    channel: str,
    direction: str,
    sender: str,
    recipient: str,
    body: str,
    subject: str = "",
    status: str = "received",
    provider_message_id: str | None = None,
) -> dict:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO messages(lead_id, channel, direction, sender, recipient, subject, body, status, provider_message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (lead_id, channel, direction, sender, recipient, subject, body, status, provider_message_id),
        )
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)
