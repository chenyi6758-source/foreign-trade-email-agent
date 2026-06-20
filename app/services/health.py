from __future__ import annotations

from datetime import datetime

from app.config import Settings
from app.db import get_db


def production_warnings(settings: Settings) -> list[str]:
    warnings: list[str] = []
    production = settings.app_env.lower() in {"prod", "production"}

    if settings.admin_password == "change-me-now":
        warnings.append("ADMIN_PASSWORD still uses the default value.")
    if settings.session_secret == "change-this-session-secret":
        warnings.append("SESSION_SECRET still uses the default value.")
    if settings.webhook_auth_enabled and settings.webhook_shared_secret == "change-this-webhook-secret":
        warnings.append("WEBHOOK_SHARED_SECRET still uses the default value.")
    if settings.unsubscribe_enabled and settings.unsubscribe_secret == "change-this-unsubscribe-secret":
        warnings.append("UNSUBSCRIBE_SECRET still uses the default value.")
    if production and not settings.app_base_url.startswith("https://"):
        warnings.append("APP_BASE_URL should use HTTPS in production.")
    if production and settings.app_host in {"127.0.0.1", "localhost"}:
        warnings.append("APP_HOST is local-only; production deployments usually bind behind a reverse proxy.")
    return warnings


def health_status(settings: Settings) -> dict:
    checks = {
        "database": False,
        "auth_hardened": settings.auth_is_hardened,
        "webhook_auth_hardened": settings.webhook_auth_is_hardened,
        "unsubscribe_hardened": settings.unsubscribe_is_hardened,
    }
    errors: list[str] = []

    try:
        with get_db() as conn:
            conn.execute("SELECT 1").fetchone()
        checks["database"] = True
    except Exception as exc:
        errors.append(f"database: {exc}")

    warnings = production_warnings(settings)
    status = "ok" if checks["database"] and not errors else "down"
    if status == "ok" and warnings:
        status = "degraded"

    return {
        "status": status,
        "app": settings.app_name,
        "env": settings.app_env,
        "checked_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
    }
