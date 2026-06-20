import csv
import io
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.db import ensure_database, get_db, rows_to_dicts
from app.schemas import DraftRequest, DraftUpdateRequest, EmailWebhook, JobCreateRequest, LeadUpdateRequest, SendEmailRequest, SendWhatsAppRequest, WhatsAppWebhook
from app.services.audit import log_event
from app.services.ai_reply import generate_auto_reply, generate_outreach_draft
from app.services.auth import clear_session_cookie, current_admin, require_admin, set_session_cookie, verify_credentials
from app.services.compliance import append_unsubscribe, cold_outreach_allowed, is_opted_out
from app.services.config_check import config_status
from app.services.crm import follow_up_due, pipeline_summary, update_lead
from app.services.deliverability import deliverability_status
from app.services.inbound_email import (
    InboundAttachment,
    ParsedInboundEmail,
    parse_generic_email_json,
    parse_mailgun_form,
    parse_postmark_json,
    parse_sendgrid_inbound,
    save_attachment_metadata,
)
from app.services.health import health_status, production_warnings
from app.services.intel import refresh_intel
from app.services.jobs import create_job, list_jobs, retry_job
from app.services.leads import LeadSignal, record_message, upsert_lead
from app.services.mailer import send_email
from app.services.prospecting import import_prospect_csv
from app.services.rate_limit import check_outbound_allowed
from app.services.unsubscribe import add_opt_out, verify_unsubscribe_token
from app.services.webhook_security import require_webhook_auth
from app.services.whatsapp import send_whatsapp


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_database()
    warnings = production_warnings(get_settings())
    for warning in warnings:
        log_event("startup_warning", "config", None, warning)
    yield


app = FastAPI(title="ExportPilot AI", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.middleware("http")
async def protect_docs(request: Request, call_next):
    if request.url.path.startswith("/api") and not current_admin(request):
        return JSONResponse({"detail": "Login required."}, status_code=401)
    if request.url.path in {"/docs", "/redoc", "/openapi.json"} and not current_admin(request):
        return RedirectResponse("/login", status_code=303)
    return await call_next(request)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if current_admin(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "settings": get_settings(), "error": ""})


@app.get("/health")
def health() -> dict:
    return health_status(get_settings())


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    settings = get_settings()
    if not verify_credentials(username, password, settings):
        log_event("login_failed", "auth", username, "invalid credentials", actor=username)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "settings": settings, "error": "Invalid username or password."},
            status_code=401,
        )
    response = RedirectResponse("/", status_code=303)
    set_session_cookie(response, username, settings)
    log_event("login_success", "auth", username, "admin logged in", actor=username)
    return response


@app.post("/logout")
def logout(request: Request):
    settings = get_settings()
    username = current_admin(request) or "unknown"
    response = RedirectResponse("/login", status_code=303)
    clear_session_cookie(response, settings)
    log_event("logout", "auth", username, "admin logged out", actor=username)
    return response


@app.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe_page(request: Request, email: str = "", token: str = ""):
    settings = get_settings()
    valid = bool(email and token and verify_unsubscribe_token(email, token, settings))
    return templates.TemplateResponse(
        "unsubscribe.html",
        {"request": request, "settings": settings, "email": email, "token": token, "valid": valid, "done": False},
        status_code=200 if valid else 400,
    )


@app.post("/unsubscribe", response_class=HTMLResponse)
def unsubscribe_confirm(request: Request, email: str = Form(...), token: str = Form(...)):
    settings = get_settings()
    valid = verify_unsubscribe_token(email, token, settings)
    if valid:
        add_opt_out(email, "unsubscribe page")
        log_event("unsubscribe", "email", email, "user confirmed unsubscribe", actor=email)
    return templates.TemplateResponse(
        "unsubscribe.html",
        {"request": request, "settings": settings, "email": email, "token": token, "valid": valid, "done": valid},
        status_code=200 if valid else 400,
    )


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, admin: str = Depends(require_admin)) -> HTMLResponse:
    with get_db() as conn:
        leads = rows_to_dicts(conn.execute("SELECT * FROM leads ORDER BY updated_at DESC LIMIT 20").fetchall())
        messages = rows_to_dicts(conn.execute("SELECT * FROM messages ORDER BY created_at DESC LIMIT 20").fetchall())
        intel = rows_to_dicts(
            conn.execute("SELECT * FROM intel_items ORDER BY relevance_score DESC, created_at DESC LIMIT 20").fetchall()
        )
        drafts = rows_to_dicts(conn.execute("SELECT * FROM outreach_drafts ORDER BY created_at DESC LIMIT 20").fetchall())
        audits = rows_to_dicts(conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 12").fetchall())
    pipeline = pipeline_summary()
    due_leads = follow_up_due(limit=10)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "settings": get_settings(),
            "admin": admin,
            "config": config_status(get_settings()),
            "leads": leads,
            "messages": messages,
            "intel": intel,
            "drafts": drafts,
            "audits": audits,
            "pipeline": pipeline,
            "due_leads": due_leads,
        },
    )


@app.post("/webhooks/email")
async def email_webhook(payload: EmailWebhook, _webhook_auth: None = Depends(require_webhook_auth)) -> dict:
    settings = get_settings()
    lead = upsert_lead(
        LeadSignal(
            channel="email",
            name=payload.from_name,
            email=str(payload.from_email),
            message=f"{payload.subject}\n{payload.body}",
        )
    )
    record_message(lead["id"], "email", "inbound", str(payload.from_email), settings.sales_email, payload.body, payload.subject)
    log_event("inbound_received", "message", lead["id"], f"email from {payload.from_email}")

    if is_opted_out(email=str(payload.from_email)) or not settings.auto_reply_enabled:
        return {"ok": True, "lead": lead, "auto_reply": "skipped"}

    reply = await generate_auto_reply(payload.body, payload.from_name, "email", settings)
    record_message(lead["id"], "email", "outbound", settings.sales_email, str(payload.from_email), reply, f"Re: {payload.subject}", "drafted")

    if settings.smtp_host:
        try:
            msg_id = send_email(str(payload.from_email), f"Re: {payload.subject}", reply, settings)
            record_message(lead["id"], "email", "outbound", settings.sales_email, str(payload.from_email), reply, f"Re: {payload.subject}", "sent", msg_id)
            log_event("auto_reply_sent", "lead", lead["id"], f"email to {payload.from_email}")
            return {"ok": True, "lead": lead, "auto_reply": "sent"}
        except Exception as exc:
            log_event("auto_reply_send_failed", "lead", lead["id"], str(exc))
            return {"ok": True, "lead": lead, "auto_reply": "drafted", "send_error": str(exc)}

    return {"ok": True, "lead": lead, "auto_reply": "drafted", "reply": reply}


def _record_parsed_inbound_email(parsed: ParsedInboundEmail) -> dict:
    settings = get_settings()
    if not parsed.from_email:
        return {"ok": False, "error": "Missing sender email.", "provider": parsed.provider}

    lead = upsert_lead(
        LeadSignal(
            channel="email",
            name=parsed.from_name,
            email=parsed.from_email,
            message=f"{parsed.subject}\n{parsed.body}",
        )
    )
    message = record_message(
        lead["id"],
        "email",
        "inbound",
        parsed.from_email,
        settings.sales_email,
        parsed.body,
        parsed.subject,
        "received",
        parsed.provider_message_id,
    )
    attachments = [save_attachment_metadata(message["id"], attachment) for attachment in parsed.attachments]
    log_event(
        "inbound_provider_email_received",
        "message",
        message["id"],
        f"{parsed.provider} email from {parsed.from_email}; attachments={len(attachments)}",
    )
    return {"ok": True, "provider": parsed.provider, "lead": lead, "message": message, "attachments": attachments}


def _csv_response(filename: str, rows: list[dict]) -> StreamingResponse:
    buffer = io.StringIO()
    fieldnames = sorted({key for row in rows for key in row.keys()})
    if fieldnames:
        writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    response = StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@app.post("/webhooks/email/generic")
async def generic_email_webhook(request: Request, _webhook_auth: None = Depends(require_webhook_auth)) -> dict:
    payload = await request.json()
    return _record_parsed_inbound_email(parse_generic_email_json(payload))


@app.post("/webhooks/email/sendgrid")
async def sendgrid_email_webhook(request: Request, _webhook_auth: None = Depends(require_webhook_auth)) -> dict:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
    else:
        form = await request.form()
        payload = dict(form)
    return _record_parsed_inbound_email(parse_sendgrid_inbound(payload))


@app.post("/webhooks/email/postmark")
async def postmark_email_webhook(request: Request, _webhook_auth: None = Depends(require_webhook_auth)) -> dict:
    payload = await request.json()
    return _record_parsed_inbound_email(parse_postmark_json(payload))


@app.post("/webhooks/email/mailgun")
async def mailgun_email_webhook(request: Request, _webhook_auth: None = Depends(require_webhook_auth)) -> dict:
    form = await request.form()
    payload = dict(form)
    parsed = parse_mailgun_form(payload)
    for key, value in form.multi_items():
        if isinstance(value, UploadFile):
            parsed.attachments.append(
                InboundAttachment(
                    filename=value.filename or key,
                    content_type=value.content_type or "application/octet-stream",
                    content=await value.read(),
                )
            )
    return _record_parsed_inbound_email(parsed)


@app.post("/webhooks/whatsapp")
async def whatsapp_webhook_json(payload: WhatsAppWebhook, _webhook_auth: None = Depends(require_webhook_auth)) -> dict:
    return await _handle_whatsapp(payload.from_phone, payload.from_name, payload.body, payload.source)


@app.post("/webhooks/whatsapp/twilio")
async def whatsapp_webhook_twilio(
    From: str = Form(...),
    Body: str = Form(...),
    ProfileName: str | None = Form(None),
    _webhook_auth: None = Depends(require_webhook_auth),
) -> dict:
    return await _handle_whatsapp(From, ProfileName, Body, "twilio")


async def _handle_whatsapp(from_phone: str, from_name: str | None, body: str, source: str) -> dict:
    settings = get_settings()
    lead = upsert_lead(LeadSignal(channel="whatsapp", name=from_name, phone=from_phone, message=body))
    record_message(lead["id"], "whatsapp", "inbound", from_phone, "company-whatsapp", body, status="received")
    log_event("inbound_received", "message", lead["id"], f"whatsapp from {from_phone}")

    if body.strip().lower() in {"stop", "unsubscribe"}:
        with get_db() as conn:
            conn.execute("INSERT INTO opt_outs(phone, reason) VALUES (?, ?)", (from_phone, "user requested opt-out"))
        log_event("opt_out", "lead", lead["id"], f"phone {from_phone}")
        return {"ok": True, "lead": lead, "auto_reply": "opted_out"}

    if is_opted_out(phone=from_phone) or not settings.auto_reply_enabled:
        return {"ok": True, "lead": lead, "auto_reply": "skipped"}

    reply = await generate_auto_reply(body, from_name, "whatsapp", settings)
    record_message(lead["id"], "whatsapp", "outbound", "company-whatsapp", from_phone, reply, status="drafted")

    if settings.whatsapp_provider != "disabled":
        try:
            provider_id = await send_whatsapp(from_phone, reply, settings)
            record_message(lead["id"], "whatsapp", "outbound", "company-whatsapp", from_phone, reply, status="sent", provider_message_id=provider_id)
            log_event("auto_reply_sent", "lead", lead["id"], f"whatsapp to {from_phone}")
            return {"ok": True, "lead": lead, "auto_reply": "sent"}
        except Exception as exc:
            log_event("auto_reply_send_failed", "lead", lead["id"], str(exc))
            return {"ok": True, "lead": lead, "auto_reply": "drafted", "send_error": str(exc)}

    return {"ok": True, "lead": lead, "auto_reply": "drafted", "reply": reply}


@app.get("/api/leads")
def list_leads() -> list[dict]:
    with get_db() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM leads ORDER BY updated_at DESC").fetchall())


@app.patch("/api/leads/{lead_id}")
def update_lead_endpoint(lead_id: int, payload: LeadUpdateRequest) -> dict:
    lead = update_lead(lead_id, payload.model_dump())
    if not lead:
        return {"ok": False, "error": "Lead not found or no fields to update."}
    log_event("lead_updated", "lead", lead_id, "CRM fields updated")
    return {"ok": True, "lead": lead}


@app.get("/api/leads/pipeline")
def get_pipeline_summary() -> list[dict]:
    return pipeline_summary()


@app.get("/api/leads/follow-ups")
def get_follow_up_due() -> list[dict]:
    return follow_up_due()


@app.get("/api/messages")
def list_messages() -> list[dict]:
    with get_db() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM messages ORDER BY created_at DESC").fetchall())


@app.get("/api/intel")
def list_intel() -> list[dict]:
    with get_db() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM intel_items ORDER BY relevance_score DESC, created_at DESC").fetchall())


@app.get("/api/config/status")
def get_config_status() -> dict:
    return config_status(get_settings())


@app.get("/api/deliverability/status")
def get_deliverability_status() -> dict:
    return deliverability_status(get_settings())


@app.post("/api/jobs")
def create_job_endpoint(payload: JobCreateRequest) -> dict:
    try:
        job = create_job(payload.type, payload.payload, payload.run_at, payload.max_attempts)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    log_event("job_created", "job", job["id"], f"type={job['type']}")
    return {"ok": True, "job": job}


@app.get("/api/jobs")
def list_jobs_endpoint(status: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=500)) -> list[dict]:
    return list_jobs(status=status, limit=limit)


@app.post("/api/jobs/{job_id}/retry")
def retry_job_endpoint(job_id: int) -> dict:
    job = retry_job(job_id)
    if not job:
        return {"ok": False, "error": "Job not found or cannot be retried now."}
    log_event("job_retry_requested", "job", job_id, f"type={job['type']}")
    return {"ok": True, "job": job}


@app.get("/api/audit")
def list_audit_logs() -> list[dict]:
    with get_db() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 200").fetchall())


@app.get("/api/export/leads.csv")
def export_leads_csv() -> StreamingResponse:
    with get_db() as conn:
        rows = rows_to_dicts(conn.execute("SELECT * FROM leads ORDER BY updated_at DESC").fetchall())
    return _csv_response("leads.csv", rows)


@app.get("/api/export/messages.csv")
def export_messages_csv() -> StreamingResponse:
    with get_db() as conn:
        rows = rows_to_dicts(conn.execute("SELECT * FROM messages ORDER BY created_at DESC").fetchall())
    return _csv_response("messages.csv", rows)


@app.get("/api/export/audit.csv")
def export_audit_csv() -> StreamingResponse:
    with get_db() as conn:
        rows = rows_to_dicts(conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC").fetchall())
    return _csv_response("audit.csv", rows)


@app.post("/api/prospects/import-csv")
async def import_prospects(file: UploadFile = File(...)) -> dict:
    content = (await file.read()).decode("utf-8-sig")
    leads = import_prospect_csv(content, source=f"csv:{file.filename}")
    log_event("prospects_imported", "lead", None, f"{len(leads)} leads from {file.filename}")
    return {"ok": True, "imported": len(leads), "leads": leads}


@app.post("/api/intel/refresh")
async def refresh_market_intel() -> dict:
    return await refresh_intel(get_settings())


@app.post("/api/send/email")
def api_send_email(payload: SendEmailRequest) -> dict:
    settings = get_settings()
    if is_opted_out(email=str(payload.to_email)):
        return {"ok": False, "error": "Recipient opted out."}
    allowed, reason = check_outbound_allowed(settings)
    if not allowed:
        return {"ok": False, "error": reason}
    body = append_unsubscribe(payload.body, settings, str(payload.to_email))
    provider_id = send_email(str(payload.to_email), payload.subject, body, settings)
    record_message(payload.lead_id, "email", "outbound", settings.sales_email, str(payload.to_email), body, payload.subject, "sent", provider_id)
    log_event("manual_email_sent", "lead", payload.lead_id, f"to {payload.to_email}")
    return {"ok": True, "provider_id": provider_id}


@app.post("/api/send/whatsapp")
async def api_send_whatsapp(payload: SendWhatsAppRequest) -> dict:
    settings = get_settings()
    if is_opted_out(phone=payload.to_phone):
        return {"ok": False, "error": "Recipient opted out."}
    allowed, reason = check_outbound_allowed(settings)
    if not allowed:
        return {"ok": False, "error": reason}
    provider_id = await send_whatsapp(payload.to_phone, payload.body, settings)
    record_message(payload.lead_id, "whatsapp", "outbound", "company-whatsapp", payload.to_phone, payload.body, status="sent", provider_message_id=provider_id)
    log_event("manual_whatsapp_sent", "lead", payload.lead_id, f"to {payload.to_phone}")
    return {"ok": True, "provider_id": provider_id}


@app.post("/api/campaigns/drafts")
async def create_outreach_draft(payload: DraftRequest) -> dict:
    settings = get_settings()
    subject, body = await generate_outreach_draft(str(payload.recipient), payload.product, payload.pain_point, payload.market, settings)
    body = append_unsubscribe(body, settings, str(payload.recipient))
    allowed, note = cold_outreach_allowed(settings, "unknown")
    status = "ready_to_send" if allowed and settings.auto_send_outbound else "pending_approval"

    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO outreach_drafts(lead_id, channel, recipient, subject, body, status, compliance_note)
            VALUES (?, 'email', ?, ?, ?, ?, ?)
            """,
            (payload.lead_id, str(payload.recipient), subject, body, status, note),
        )
        draft = dict(conn.execute("SELECT * FROM outreach_drafts WHERE id = ?", (cur.lastrowid,)).fetchone())
    log_event("outreach_draft_created", "draft", draft["id"], f"recipient {payload.recipient}; {note}")
    return {"ok": True, "draft": draft}


@app.patch("/api/campaigns/drafts/{draft_id}")
def update_outreach_draft(draft_id: int, payload: DraftUpdateRequest) -> dict:
    updates = []
    params: list[str | int] = []
    if payload.subject is not None:
        updates.append("subject = ?")
        params.append(payload.subject)
    if payload.body is not None:
        updates.append("body = ?")
        params.append(payload.body)
    if payload.status is not None:
        updates.append("status = ?")
        params.append(payload.status)
    if not updates:
        return {"ok": False, "error": "No fields to update."}

    params.append(draft_id)
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM outreach_drafts WHERE id = ?", (draft_id,)).fetchone()
        if not existing:
            return {"ok": False, "error": "Draft not found."}
        conn.execute(f"UPDATE outreach_drafts SET {', '.join(updates)} WHERE id = ?", params)
        draft = dict(conn.execute("SELECT * FROM outreach_drafts WHERE id = ?", (draft_id,)).fetchone())
    log_event("outreach_draft_updated", "draft", draft_id, "draft edited before approval")
    return {"ok": True, "draft": draft}


@app.post("/api/campaigns/drafts/{draft_id}/approve-send")
def approve_and_send_draft(draft_id: int) -> dict:
    settings = get_settings()
    with get_db() as conn:
        draft = conn.execute("SELECT * FROM outreach_drafts WHERE id = ?", (draft_id,)).fetchone()
        if not draft:
            return {"ok": False, "error": "Draft not found."}
        if is_opted_out(email=draft["recipient"]):
            return {"ok": False, "error": "Recipient opted out."}
        allowed, reason = check_outbound_allowed(settings)
        if not allowed:
            return {"ok": False, "error": reason}
        body = append_unsubscribe(draft["body"], settings, draft["recipient"])
        provider_id = send_email(draft["recipient"], draft["subject"], body, settings)
        conn.execute(
            "UPDATE outreach_drafts SET status = 'sent', approved_at = CURRENT_TIMESTAMP, sent_at = CURRENT_TIMESTAMP WHERE id = ?",
            (draft_id,),
        )
    record_message(draft["lead_id"], "email", "outbound", settings.sales_email, draft["recipient"], body, draft["subject"], "sent", provider_id)
    log_event("outreach_draft_sent", "draft", draft_id, f"to {draft['recipient']}")
    return {"ok": True, "provider_id": provider_id}
