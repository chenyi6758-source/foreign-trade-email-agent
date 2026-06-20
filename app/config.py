from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ExportPilot AI"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_base_url: str = "http://127.0.0.1:8000"
    database_url: str = "sqlite:///./data/app.db"

    admin_username: str = "admin"
    admin_password: str = "change-me-now"
    session_secret: str = "change-this-session-secret"
    session_cookie_name: str = "fta_session"
    session_ttl_hours: int = 12

    webhook_auth_enabled: bool = True
    webhook_shared_secret: str = "change-this-webhook-secret"
    webhook_token_header: str = "X-Webhook-Token"
    webhook_signature_header: str = "X-Webhook-Signature"

    llm_provider: str = "openai-compatible"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4.1-mini"
    llm_temperature: float = 0.4
    llm_timeout_seconds: int = 45
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    company_name: str = "Your Export Company"
    company_products: str = "export products"
    company_tone: str = "professional, warm, concise"
    sales_email: str = "sales@example.com"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_from_email: str = "sales@example.com"
    smtp_from_name: str = "Sales Team"

    whatsapp_provider: str = "disabled"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    meta_whatsapp_token: str = ""
    meta_whatsapp_phone_number_id: str = ""

    auto_reply_enabled: bool = True
    auto_send_outbound: bool = False
    require_approval_for_cold_outreach: bool = True
    max_outbound_per_day: int = 50
    min_seconds_between_outbound: int = 30
    unsubscribe_text: str = "Reply STOP to opt out."
    unsubscribe_enabled: bool = True
    unsubscribe_secret: str = "change-this-unsubscribe-secret"
    unsubscribe_path: str = "/unsubscribe"

    intel_feeds: str = Field(default="")
    target_markets: str = "United States, Germany, United Kingdom"
    target_keywords: str = "importer, distributor, sourcing, procurement, RFQ, tender, buyer"

    @property
    def sqlite_path(self) -> Path:
        if not self.database_url.startswith("sqlite:///"):
            raise ValueError("This MVP currently supports sqlite:/// DATABASE_URL only.")
        return Path(self.database_url.replace("sqlite:///", "", 1))

    @property
    def feed_urls(self) -> list[str]:
        return [item.strip() for item in self.intel_feeds.split(",") if item.strip()]

    @property
    def markets(self) -> list[str]:
        return [item.strip() for item in self.target_markets.split(",") if item.strip()]

    @property
    def keywords(self) -> list[str]:
        return [item.strip().lower() for item in self.target_keywords.split(",") if item.strip()]

    @property
    def effective_llm_api_key(self) -> str:
        return self.llm_api_key or self.openai_api_key

    @property
    def effective_llm_model(self) -> str:
        return self.llm_model or self.openai_model

    @property
    def effective_llm_base_url(self) -> str:
        return self.llm_base_url.rstrip("/")

    @property
    def auth_is_hardened(self) -> bool:
        return self.admin_password != "change-me-now" and self.session_secret != "change-this-session-secret"

    @property
    def webhook_auth_is_hardened(self) -> bool:
        return not self.webhook_auth_enabled or self.webhook_shared_secret != "change-this-webhook-secret"

    @property
    def unsubscribe_is_hardened(self) -> bool:
        return not self.unsubscribe_enabled or self.unsubscribe_secret != "change-this-unsubscribe-secret"


@lru_cache
def get_settings() -> Settings:
    return Settings()
