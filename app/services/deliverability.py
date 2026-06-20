from app.config import Settings


def sender_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower() if "@" in email else ""


def deliverability_status(settings: Settings) -> dict:
    domain = sender_domain(settings.smtp_from_email)
    checks = [
        {
            "name": "smtp_configured",
            "ok": bool(settings.smtp_host and settings.smtp_from_email),
            "detail": "SMTP host and from email are configured.",
        },
        {
            "name": "unsubscribe_link",
            "ok": settings.unsubscribe_enabled and settings.unsubscribe_is_hardened,
            "detail": "Marketing emails include a signed unsubscribe link.",
        },
        {
            "name": "outbound_pacing",
            "ok": settings.max_outbound_per_day <= 200 and settings.min_seconds_between_outbound >= 10,
            "detail": "Daily limit and send pacing reduce spam risk.",
        },
        {
            "name": "cold_outreach_approval",
            "ok": settings.require_approval_for_cold_outreach and not settings.auto_send_outbound,
            "detail": "Cold outreach requires human approval before sending.",
        },
    ]
    return {
        "sender_domain": domain,
        "checks": checks,
        "manual_dns_records": [
            f"SPF: add your SMTP provider to TXT record for {domain or 'your domain'}.",
            f"DKIM: enable DKIM signing in your email provider for {domain or 'your domain'}.",
            f"DMARC: publish _dmarc.{domain or 'your domain'} TXT record with a monitoring policy first.",
        ],
        "recommended_warmup": [
            "Start with low daily volume and increase gradually.",
            "Send only to relevant business contacts and stop after opt-out.",
            "Keep bounce rate low by cleaning invalid addresses before sending.",
        ],
    }
