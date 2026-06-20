from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.db import get_db


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


@dataclass
class InboundAttachment:
    filename: str
    content_type: str = "application/octet-stream"
    content: bytes = b""


@dataclass
class ParsedInboundEmail:
    provider: str
    from_email: str
    from_name: str | None = None
    subject: str = ""
    text_body: str = ""
    html_body: str = ""
    provider_message_id: str | None = None
    attachments: list[InboundAttachment] = field(default_factory=list)

    @property
    def body(self) -> str:
        return self.text_body or strip_html(self.html_body)


def strip_html(html: str) -> str:
    text = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _first_email(value: str | None) -> str:
    if not value:
        return ""
    match = EMAIL_RE.search(value)
    return match.group(0) if match else value.strip()


def _display_name(value: str | None, email: str) -> str | None:
    if not value:
        return None
    cleaned = value.replace(email, "").replace("<>", "").replace("<", "").replace(">", "").strip(" \"'")
    return cleaned or None


def parse_mailgun_form(form: dict[str, Any]) -> ParsedInboundEmail:
    sender = str(form.get("sender") or form.get("from") or "")
    email = _first_email(sender)
    return ParsedInboundEmail(
        provider="mailgun",
        from_email=email,
        from_name=str(form.get("from") or "").replace(f"<{email}>", "").strip() or None,
        subject=str(form.get("subject") or ""),
        text_body=str(form.get("body-plain") or form.get("stripped-text") or form.get("text") or ""),
        html_body=str(form.get("body-html") or form.get("html") or ""),
        provider_message_id=str(form.get("Message-Id") or form.get("message-id") or "") or None,
    )


def parse_sendgrid_inbound(payload: dict[str, Any]) -> ParsedInboundEmail:
    sender = str(payload.get("from") or payload.get("sender") or "")
    email = _first_email(sender)
    return ParsedInboundEmail(
        provider="sendgrid",
        from_email=email,
        from_name=_display_name(sender, email),
        subject=str(payload.get("subject") or ""),
        text_body=str(payload.get("text") or ""),
        html_body=str(payload.get("html") or ""),
        provider_message_id=str(payload.get("headers") or "")[:240] or None,
    )


def parse_postmark_json(payload: dict[str, Any]) -> ParsedInboundEmail:
    email = str(payload.get("From") or payload.get("FromFull", {}).get("Email") or "")
    if isinstance(payload.get("FromFull"), dict):
        email = payload["FromFull"].get("Email") or email
        name = payload["FromFull"].get("Name")
    else:
        name = None
    attachments = []
    for item in payload.get("Attachments") or []:
        if isinstance(item, dict):
            attachments.append(
                InboundAttachment(
                    filename=item.get("Name") or "attachment.bin",
                    content_type=item.get("ContentType") or "application/octet-stream",
                    content=b"",
                )
            )
    return ParsedInboundEmail(
        provider="postmark",
        from_email=_first_email(email),
        from_name=name,
        subject=str(payload.get("Subject") or ""),
        text_body=str(payload.get("TextBody") or ""),
        html_body=str(payload.get("HtmlBody") or ""),
        provider_message_id=str(payload.get("MessageID") or "") or None,
        attachments=attachments,
    )


def parse_generic_email_json(payload: dict[str, Any]) -> ParsedInboundEmail:
    sender = str(payload.get("from_email") or payload.get("from") or payload.get("sender") or "")
    email = _first_email(sender)
    attachments = []
    for item in payload.get("attachments") or []:
        if isinstance(item, dict):
            attachments.append(
                InboundAttachment(
                    filename=item.get("filename") or "attachment.bin",
                    content_type=item.get("content_type") or "application/octet-stream",
                    content=(item.get("content") or "").encode("utf-8"),
                )
            )
    return ParsedInboundEmail(
        provider=str(payload.get("provider") or "generic"),
        from_email=email,
        from_name=str(payload.get("from_name") or "") or _display_name(sender, email),
        subject=str(payload.get("subject") or ""),
        text_body=str(payload.get("body") or payload.get("text") or ""),
        html_body=str(payload.get("html") or ""),
        provider_message_id=str(payload.get("provider_message_id") or payload.get("message_id") or "") or None,
        attachments=attachments,
    )


def parse_raw_email(raw: bytes, provider: str = "generic-raw") -> ParsedInboundEmail:
    message = BytesParser(policy=policy.default).parsebytes(raw)
    sender = str(message.get("from") or "")
    email = _first_email(sender)
    text_body = ""
    html_body = ""
    attachments: list[InboundAttachment] = []
    for part in message.walk():
        content_disposition = part.get_content_disposition()
        content_type = part.get_content_type()
        if content_disposition == "attachment":
            attachments.append(
                InboundAttachment(
                    filename=part.get_filename() or "attachment.bin",
                    content_type=content_type,
                    content=part.get_payload(decode=True) or b"",
                )
            )
        elif content_type == "text/plain" and not text_body:
            text_body = part.get_content()
        elif content_type == "text/html" and not html_body:
            html_body = part.get_content()
    return ParsedInboundEmail(
        provider=provider,
        from_email=email,
        from_name=_display_name(sender, email),
        subject=str(message.get("subject") or ""),
        text_body=text_body,
        html_body=html_body,
        provider_message_id=str(message.get("message-id") or "") or None,
        attachments=attachments,
    )


def save_attachment_metadata(message_id: int, attachment: InboundAttachment, base_dir: Path | None = None) -> dict:
    if base_dir is None:
        db_path = get_settings().sqlite_path
        if not db_path.is_absolute():
            db_path = Path.cwd() / db_path
        base = db_path.parent / "attachments"
    else:
        base = base_dir
    base.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(attachment.content).hexdigest()
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", attachment.filename).strip("._") or "attachment.bin"
    storage_path = base / f"{digest[:16]}_{safe_name}"
    storage_path.write_bytes(attachment.content)
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO inbound_attachments(message_id, filename, content_type, size_bytes, storage_path, sha256)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (message_id, attachment.filename, attachment.content_type, len(attachment.content), str(storage_path), digest),
        )
        row = conn.execute("SELECT * FROM inbound_attachments WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)
