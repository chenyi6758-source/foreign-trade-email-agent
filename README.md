# ExportPilot AI

ExportPilot AI is a FastAPI-based MVP for export sales teams and solo foreign-trade operators. It captures inbound buyer messages, scores and manages leads, drafts compliant outreach, tracks follow-ups, and keeps slow work in a small SQLite-backed job queue.

The project is designed to be useful on a local Windows laptop first, then deployable to a small VPS when you are ready.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Release Checklist](docs/RELEASE.md)
- [Commercial Readiness Notes](COMMERCIAL_READY.md)
- [Feasibility Lab](FEASIBILITY.md)
- [Security Policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## What It Does

- Receives inbound email webhooks and creates leads/messages.
- Supports provider-style inbound routes for Mailgun, SendGrid, Postmark, and generic JSON payloads.
- Stores inbound attachment metadata and SHA-256 hashes without executing attachments.
- Receives WhatsApp webhooks and drafts replies.
- Imports prospect CSV files from trade shows, B2B platforms, customs data, or manual research.
- Scores leads by buying intent such as RFQ, quotation, price, MOQ, sample, tender, distributor, and importer.
- Generates cold-outreach drafts that require human approval by default.
- Adds unsubscribe text and `List-Unsubscribe` headers for outbound email.
- Provides a protected dashboard and protected `/api/*` endpoints.
- Provides webhook token/HMAC authentication.
- Provides a SQLite job queue for scheduled follow-ups, queued email sends, draft sends, and RSS/intel refreshes.
- Provides health checks, CSV exports, SQLite backups, and a production launcher script.

## Tech Stack

- Python 3.11+
- FastAPI
- SQLite
- Jinja2
- SMTP
- Twilio WhatsApp or Meta WhatsApp Cloud API
- OpenAI-compatible LLM endpoint, optional

## Quick Start

```powershell
cd C:\Users\雷歆瑶\Documents\Codex\2026-06-16\new-chat-5\outputs\foreign-trade-autopilot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Default admin settings are in `.env.example`. Change these before any real use:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me-now
SESSION_SECRET=change-this-session-secret
WEBHOOK_SHARED_SECRET=change-this-to-a-long-random-webhook-secret
UNSUBSCRIBE_SECRET=change-this-to-a-long-random-unsubscribe-secret
```

## Webhook Routes

Generic email webhook:

```text
POST /webhooks/email
```

Provider-specific inbound email routes:

```text
POST /webhooks/email/generic
POST /webhooks/email/mailgun
POST /webhooks/email/sendgrid
POST /webhooks/email/postmark
```

WhatsApp routes:

```text
POST /webhooks/whatsapp
POST /webhooks/whatsapp/twilio
```

When `WEBHOOK_AUTH_ENABLED=true`, include one of:

```text
X-Webhook-Token: your-shared-secret
X-Webhook-Signature: sha256=<hmac-sha256-of-raw-body>
```

## Useful API Routes

```text
GET    /api/leads
PATCH  /api/leads/{lead_id}
GET    /api/leads/pipeline
GET    /api/leads/follow-ups
GET    /api/messages
GET    /api/intel
POST   /api/intel/refresh
POST   /api/prospects/import-csv
POST   /api/campaigns/drafts
PATCH  /api/campaigns/drafts/{draft_id}
POST   /api/campaigns/drafts/{draft_id}/approve-send
POST   /api/send/email
POST   /api/send/whatsapp
GET    /api/deliverability/status
POST   /api/jobs
GET    /api/jobs
POST   /api/jobs/{job_id}/retry
GET    /api/export/leads.csv
GET    /api/export/messages.csv
GET    /api/export/audit.csv
```

Operational route:

```text
GET /health
```

## Job Queue

The queue is intentionally SQLite-friendly. It is enough for a solo operator or a small team before moving to Redis/Celery.

Supported job types:

```text
follow_up_reminder
refresh_intel
send_email
send_draft
```

Create a job through the API:

```json
{
  "type": "follow_up_reminder",
  "payload": {
    "lead_id": 1,
    "note": "Send quotation follow-up"
  }
}
```

Run the scheduler once:

```powershell
python scripts\scheduler.py --intel
```

Run the worker once:

```powershell
python scripts\worker.py --once
```

Run the worker continuously:

```powershell
python scripts\worker.py --poll-seconds 30
```

## Backups and Export

Create a timestamped SQLite backup:

```powershell
python scripts\backup_sqlite.py
```

CSV exports are protected by admin login:

```text
/api/export/leads.csv
/api/export/messages.csv
/api/export/audit.csv
```

## Production Launcher

```powershell
Copy-Item .env.production.example .env.production
notepad .env.production
powershell -ExecutionPolicy Bypass -File scripts\run_prod.ps1
```

For a public server, run it behind HTTPS with Caddy, Nginx, or another reverse proxy. The app exposes `/health` for uptime checks.

## Verification

Unit tests:

```powershell
python -m pytest tests -q
```

API smoke test:

```powershell
python scripts\api_smoke_test.py
```

Feasibility lab:

```powershell
python scripts\feasibility_lab.py
```

Release check:

```powershell
python scripts\release_check.py
```

The feasibility lab runs without real SMTP, WhatsApp, OpenAI, or RSS credentials. Real sending and live market intelligence still require provider accounts and network access.

## Safety Defaults

- Cold outreach is draft-only by default.
- Auto-send is disabled by default.
- Unsubscribe text is appended to outbound email.
- Opted-out contacts are blocked before sending.
- Webhook authentication is enabled by default.
- Admin login protects the dashboard, OpenAPI docs, and `/api/*`.

## Suggested Production Path

1. Configure real SMTP and verify SPF, DKIM, DMARC, and bounce handling.
2. Configure Mailgun, SendGrid, or Postmark inbound parsing.
3. Connect WhatsApp through Twilio or Meta only after business verification.
4. Run `scripts\scheduler.py` through Windows Task Scheduler.
5. Run `scripts\worker.py` through Windows Task Scheduler, NSSM, PM2, or a VPS process manager.
6. Schedule `scripts\backup_sqlite.py` before storing real customer records.

## License

Add a license before publishing publicly. MIT is a practical default for an open-source MVP, but choose based on your business plan.
