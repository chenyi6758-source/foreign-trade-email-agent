# Architecture

ExportPilot AI is a SQLite-first FastAPI application for small export sales teams and SOHO operators.

## Main Components

```text
Inbound providers
  -> FastAPI webhooks
  -> lead upsert and message record
  -> reply or draft generation
  -> dashboard and protected API
  -> SQLite database

Scheduler
  -> jobs table
  -> worker
  -> email, draft, follow-up, and intel tasks
```

## Application Layers

- `app/main.py`: FastAPI routes, dashboard rendering, webhook entry points, protected APIs.
- `app/db.py`: SQLite schema and connection helpers.
- `app/schemas.py`: Pydantic request models.
- `app/services/`: business logic for auth, CRM, AI replies, jobs, email, WhatsApp, compliance, health, and exports.
- `scripts/`: local automation, smoke tests, worker, scheduler, backups, and server launchers.
- `tests/`: unit and integration-style tests using FastAPI `TestClient`.

## Data Model

Core tables:

- `leads`: buyer/contact records, CRM stage, score, owner, follow-up time, notes, deal value.
- `messages`: inbound and outbound email/WhatsApp messages.
- `inbound_attachments`: attachment metadata and SHA-256 hashes.
- `outreach_drafts`: cold outreach drafts and approval status.
- `opt_outs`: email/phone unsubscribe records.
- `jobs`: SQLite task queue.
- `audit_logs`: operational event trail.
- `intel_items`: RSS/market intelligence records.

## Safety Defaults

- Admin login protects `/`, `/docs`, `/redoc`, `/openapi.json`, and `/api/*`.
- Webhooks require token or HMAC authentication.
- Cold outreach is draft-first by default.
- Outbound sending checks opt-outs and rate limits.
- Attachments are stored as files and metadata; they are not executed.

## Scaling Path

This project intentionally starts simple. A practical upgrade path is:

1. Keep SQLite for local/SOHO use.
2. Add scheduled backups and restore drills.
3. Move the app, worker, and scheduler under a process supervisor.
4. Add PostgreSQL when multiple users or larger datasets require it.
5. Move jobs to Redis/RQ, Celery, or a managed queue when workload grows.
