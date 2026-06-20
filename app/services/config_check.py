from app.config import Settings
from app.services.deliverability import deliverability_status


def config_status(settings: Settings) -> dict:
    llm_ready = bool(settings.effective_llm_api_key and settings.effective_llm_base_url and settings.effective_llm_model)
    smtp_ready = bool(settings.smtp_host and settings.smtp_from_email)
    whatsapp_ready = (
        settings.whatsapp_provider == "twilio"
        and bool(settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_whatsapp_from)
    ) or (
        settings.whatsapp_provider == "meta"
        and bool(settings.meta_whatsapp_token and settings.meta_whatsapp_phone_number_id)
    )

    return {
        "app": {
            "name": settings.app_name,
            "env": settings.app_env,
            "host": settings.app_host,
            "port": settings.app_port,
            "base_url": settings.app_base_url,
        },
        "auth": {
            "ready": settings.auth_is_hardened,
            "username": settings.admin_username,
            "session_ttl_hours": settings.session_ttl_hours,
            "default_password_in_use": settings.admin_password == "change-me-now",
            "default_session_secret_in_use": settings.session_secret == "change-this-session-secret",
        },
        "webhook_auth": {
            "enabled": settings.webhook_auth_enabled,
            "ready": settings.webhook_auth_is_hardened,
            "token_header": settings.webhook_token_header,
            "signature_header": settings.webhook_signature_header,
            "default_secret_in_use": settings.webhook_shared_secret == "change-this-webhook-secret",
        },
        "unsubscribe": {
            "enabled": settings.unsubscribe_enabled,
            "ready": settings.unsubscribe_is_hardened,
            "path": settings.unsubscribe_path,
            "default_secret_in_use": settings.unsubscribe_secret == "change-this-unsubscribe-secret",
        },
        "llm": {
            "ready": llm_ready,
            "provider": settings.llm_provider,
            "base_url": settings.effective_llm_base_url,
            "model": settings.effective_llm_model,
            "api_key_set": bool(settings.effective_llm_api_key),
        },
        "email": {
            "ready": smtp_ready,
            "host": settings.smtp_host,
            "port": settings.smtp_port,
            "from_email": settings.smtp_from_email,
            "username_set": bool(settings.smtp_username),
        },
        "whatsapp": {
            "ready": whatsapp_ready,
            "provider": settings.whatsapp_provider,
        },
        "guardrails": {
            "auto_reply_enabled": settings.auto_reply_enabled,
            "auto_send_outbound": settings.auto_send_outbound,
            "require_approval_for_cold_outreach": settings.require_approval_for_cold_outreach,
            "max_outbound_per_day": settings.max_outbound_per_day,
            "min_seconds_between_outbound": settings.min_seconds_between_outbound,
        },
        "deliverability": deliverability_status(settings),
    }
