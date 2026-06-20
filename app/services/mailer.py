import smtplib
from email.message import EmailMessage

from app.config import Settings
from app.services.unsubscribe import list_unsubscribe_header


def send_email(to_email: str, subject: str, body: str, settings: Settings) -> str:
    if not settings.smtp_host:
        raise RuntimeError("SMTP_HOST is not configured.")

    message = EmailMessage()
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = to_email
    message["Subject"] = subject
    if settings.unsubscribe_enabled:
        message["List-Unsubscribe"] = list_unsubscribe_header(to_email, settings)
        message["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)

    return "smtp-sent"
