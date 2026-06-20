from pydantic import BaseModel, Field, field_validator


def _validate_email(value: str) -> str:
    if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
        raise ValueError("Invalid email address.")
    return value.strip()


class EmailWebhook(BaseModel):
    from_email: str
    from_name: str | None = None
    subject: str = ""
    body: str
    source: str = "email"

    @field_validator("from_email")
    @classmethod
    def validate_from_email(cls, value: str) -> str:
        return _validate_email(value)


class WhatsAppWebhook(BaseModel):
    from_phone: str
    from_name: str | None = None
    body: str
    source: str = "whatsapp"


class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    lead_id: int | None = None

    @field_validator("to_email")
    @classmethod
    def validate_to_email(cls, value: str) -> str:
        return _validate_email(value)


class SendWhatsAppRequest(BaseModel):
    to_phone: str
    body: str
    lead_id: int | None = None


class DraftRequest(BaseModel):
    recipient: str
    lead_id: int | None = None
    product: str | None = None
    pain_point: str | None = None
    market: str | None = None
    reason: str = Field(default="manual prospecting")

    @field_validator("recipient")
    @classmethod
    def validate_recipient(cls, value: str) -> str:
        return _validate_email(value)


class DraftUpdateRequest(BaseModel):
    subject: str | None = None
    body: str | None = None
    status: str | None = None


class LeadUpdateRequest(BaseModel):
    stage: str | None = None
    owner: str | None = None
    priority: str | None = None
    next_follow_up_at: str | None = None
    notes: str | None = None
    deal_value: float | None = None
    status: str | None = None
    consent_status: str | None = None
    country: str | None = None

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, value: str | None) -> str | None:
        if value is None:
            return value
        allowed = {"new", "contacted", "qualified", "quoted", "negotiating", "won", "lost", "nurture"}
        if value not in allowed:
            raise ValueError(f"stage must be one of: {', '.join(sorted(allowed))}")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str | None) -> str | None:
        if value is None:
            return value
        allowed = {"low", "normal", "high", "urgent"}
        if value not in allowed:
            raise ValueError(f"priority must be one of: {', '.join(sorted(allowed))}")
        return value


class JobCreateRequest(BaseModel):
    type: str
    payload: dict = Field(default_factory=dict)
    run_at: str | None = None
    max_attempts: int = Field(default=3, ge=1, le=10)
