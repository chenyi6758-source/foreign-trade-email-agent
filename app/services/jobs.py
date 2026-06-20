from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable

from app.config import get_settings
from app.db import get_db, rows_to_dicts
from app.services.audit import log_event
from app.services.compliance import append_unsubscribe, is_opted_out
from app.services.crm import follow_up_due
from app.services.intel import refresh_intel
from app.services.leads import record_message
from app.services.mailer import send_email
from app.services.rate_limit import check_outbound_allowed


JOB_TYPES = {"follow_up_reminder", "refresh_intel", "send_email", "send_draft"}
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


def utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat(sep=" ")


def normalize_payload(payload: dict | None) -> str:
    return json.dumps(payload or {}, ensure_ascii=False, sort_keys=True)


def decode_payload(row: dict) -> dict:
    try:
        row["payload"] = json.loads(row.get("payload_json") or "{}")
    except json.JSONDecodeError:
        row["payload"] = {}
    return row


def create_job(job_type: str, payload: dict | None = None, run_at: str | None = None, max_attempts: int = 3) -> dict:
    if job_type not in JOB_TYPES:
        raise ValueError(f"Unsupported job type: {job_type}")
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO jobs(type, payload_json, run_at, max_attempts)
            VALUES (?, ?, ?, ?)
            """,
            (job_type, normalize_payload(payload), run_at or utc_now(), max_attempts),
        )
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (cur.lastrowid,)).fetchone()
    return decode_payload(dict(row))


def list_jobs(status: str | None = None, limit: int = 100) -> list[dict]:
    limit = max(1, min(limit, 500))
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY datetime(run_at) ASC, id ASC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY datetime(run_at) ASC, id ASC LIMIT ?",
                (limit,),
            ).fetchall()
    return [decode_payload(row) for row in rows_to_dicts(rows)]


def get_job(job_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return decode_payload(dict(row)) if row else None


def claim_next_job() -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT * FROM jobs
            WHERE status = 'queued'
              AND datetime(run_at) <= datetime('now')
              AND attempts < max_attempts
            ORDER BY datetime(run_at) ASC, id ASC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        conn.execute(
            """
            UPDATE jobs
            SET status = 'running',
                attempts = attempts + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'queued'
            """,
            (row["id"],),
        )
        claimed = conn.execute("SELECT * FROM jobs WHERE id = ?", (row["id"],)).fetchone()
    return decode_payload(dict(claimed))


def complete_job(job_id: int, result: dict | None = None) -> dict | None:
    detail = normalize_payload({"result": result or {}})
    with get_db() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = 'completed',
                last_error = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (detail, job_id),
        )
    return get_job(job_id)


def fail_job(job_id: int, error: str, retry_delay_seconds: int = 300) -> dict | None:
    job = get_job(job_id)
    if not job:
        return None
    next_status = "failed" if job["attempts"] >= job["max_attempts"] else "queued"
    next_run_at = (datetime.utcnow() + timedelta(seconds=retry_delay_seconds)).replace(microsecond=0).isoformat(sep=" ")
    with get_db() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = ?,
                last_error = ?,
                run_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (next_status, error[:1000], next_run_at, job_id),
        )
    return get_job(job_id)


def retry_job(job_id: int) -> dict | None:
    job = get_job(job_id)
    if not job:
        return None
    if job["status"] not in TERMINAL_STATUSES and job["status"] != "queued":
        return None
    with get_db() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = 'queued',
                last_error = '',
                run_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (utc_now(), job_id),
        )
    return get_job(job_id)


def enqueue_due_follow_up_jobs(limit: int = 50) -> list[dict]:
    due_leads = follow_up_due(limit=limit)
    existing = list_jobs(status="queued", limit=500) + list_jobs(status="running", limit=500)
    existing_keys = {
        (job["type"], str(job.get("payload", {}).get("lead_id")))
        for job in existing
        if job["type"] == "follow_up_reminder"
    }
    created = []
    for lead in due_leads:
        key = ("follow_up_reminder", str(lead["id"]))
        if key in existing_keys:
            continue
        created.append(
            create_job(
                "follow_up_reminder",
                {
                    "lead_id": lead["id"],
                    "email": lead.get("email"),
                    "phone": lead.get("phone"),
                    "stage": lead.get("stage"),
                    "priority": lead.get("priority"),
                    "next_follow_up_at": lead.get("next_follow_up_at"),
                    "notes": lead.get("notes"),
                },
            )
        )
    return created


async def process_job(job: dict) -> dict:
    payload = job.get("payload") or {}
    settings = get_settings()

    if job["type"] == "follow_up_reminder":
        lead_id = payload.get("lead_id")
        log_event("follow_up_due", "lead", lead_id, f"Follow-up is due: {payload.get('notes') or ''}")
        return {"reminded": True, "lead_id": lead_id}

    if job["type"] == "refresh_intel":
        return await refresh_intel(settings)

    if job["type"] == "send_email":
        to_email = str(payload["to_email"])
        if is_opted_out(email=to_email):
            raise RuntimeError("Recipient opted out.")
        allowed, reason = check_outbound_allowed(settings)
        if not allowed:
            raise RuntimeError(reason)
        body = append_unsubscribe(str(payload["body"]), settings, to_email)
        provider_id = send_email(to_email, str(payload["subject"]), body, settings)
        record_message(
            payload.get("lead_id"),
            "email",
            "outbound",
            settings.sales_email,
            to_email,
            body,
            str(payload["subject"]),
            "sent",
            provider_id,
        )
        log_event("queued_email_sent", "job", job["id"], f"to {to_email}")
        return {"provider_id": provider_id}

    if job["type"] == "send_draft":
        draft_id = int(payload["draft_id"])
        with get_db() as conn:
            draft = conn.execute("SELECT * FROM outreach_drafts WHERE id = ?", (draft_id,)).fetchone()
        if not draft:
            raise RuntimeError("Draft not found.")
        if draft["status"] not in {"ready_to_send", "approved"}:
            raise RuntimeError(f"Draft status is {draft['status']}, not ready to send.")
        to_email = draft["recipient"]
        if is_opted_out(email=to_email):
            raise RuntimeError("Recipient opted out.")
        allowed, reason = check_outbound_allowed(settings)
        if not allowed:
            raise RuntimeError(reason)
        body = append_unsubscribe(draft["body"], settings, to_email)
        provider_id = send_email(to_email, draft["subject"], body, settings)
        with get_db() as conn:
            conn.execute(
                """
                UPDATE outreach_drafts
                SET status = 'sent',
                    approved_at = COALESCE(approved_at, CURRENT_TIMESTAMP),
                    sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (draft_id,),
            )
        record_message(draft["lead_id"], "email", "outbound", settings.sales_email, to_email, body, draft["subject"], "sent", provider_id)
        log_event("queued_draft_sent", "draft", draft_id, f"to {to_email}")
        return {"provider_id": provider_id, "draft_id": draft_id}

    raise RuntimeError(f"Unsupported job type: {job['type']}")


async def run_due_jobs(
    limit: int = 10,
    processor: Callable[[dict], Awaitable[dict]] | None = None,
) -> dict[str, Any]:
    processed = []
    for _ in range(max(1, limit)):
        job = claim_next_job()
        if not job:
            break
        try:
            result = await (processor(job) if processor else process_job(job))
            processed.append({"job_id": job["id"], "status": "completed", "result": result})
            complete_job(job["id"], result)
        except Exception as exc:
            processed.append({"job_id": job["id"], "status": "failed", "error": str(exc)})
            fail_job(job["id"], str(exc))
    return {"processed": processed, "count": len(processed)}


def run_due_jobs_sync(limit: int = 10) -> dict[str, Any]:
    return asyncio.run(run_due_jobs(limit=limit))
