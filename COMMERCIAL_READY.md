# Commercial Readiness Notes

ExportPilot AI is now a runnable commercial MVP for internal trials, internships, and solo foreign-trade operators. It is not yet a fully managed SaaS product, but the core operating loop is in place.

## Completed Capabilities

- Admin login protects the dashboard, OpenAPI docs, and `/api/*`.
- Webhooks require a shared token or HMAC signature.
- CRM fields support owner, stage, priority, follow-up time, notes, country, consent status, and deal value.
- Email deliverability helpers add unsubscribe headers and provide a DNS/checklist endpoint.
- Inbound email parsing supports generic JSON, Mailgun, SendGrid, and Postmark style routes.
- Attachment metadata is stored with filename, content type, byte size, storage path, and SHA-256 hash.
- CSV prospect import supports basic lead sourcing workflows.
- Cold outreach drafts require approval by default.
- Audit logs track important operational events.
- A SQLite job queue supports follow-up reminders, RSS/intel refreshes, queued email sends, and queued draft sends.
- Worker and scheduler scripts are available for local automation.
- Offline feasibility and API smoke tests are available.

## Optimization Roadmap

Progress is currently step 6 / 8.

1. Login restriction: complete.
2. Webhook token/HMAC authentication: complete.
3. CRM follow-up pipeline: complete.
4. Email deliverability and unsubscribe: complete.
5. Real inbound email parsing and attachment handling: complete.
6. Task queue and scheduled follow-up: base implementation complete.
7. Deployment, HTTPS, and process supervision: base implementation complete.
8. Database upgrade, backups, and export: base implementation complete.

Steps 6-8 are intentionally SQLite-first. They are suitable for a SOHO or small team workflow. If traffic grows, the queue can later move to Redis/RQ, Celery, or a managed queue, and the database can move to PostgreSQL.

## Admin Configuration

Set strong secrets in `.env` before real use:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-to-a-strong-password
SESSION_SECRET=change-this-to-a-long-random-secret
SESSION_TTL_HOURS=12
```

Protected areas:

```text
/
/docs
/redoc
/openapi.json
/api/*
```

## Webhook Security

Set:

```env
WEBHOOK_AUTH_ENABLED=true
WEBHOOK_SHARED_SECRET=change-this-to-a-long-random-webhook-secret
WEBHOOK_TOKEN_HEADER=X-Webhook-Token
WEBHOOK_SIGNATURE_HEADER=X-Webhook-Signature
```

Simple token mode:

```text
X-Webhook-Token: your-shared-secret
```

HMAC mode:

```text
X-Webhook-Signature: sha256=<hex-hmac>
```

The signature is:

```text
HMAC_SHA256(raw_request_body, WEBHOOK_SHARED_SECRET)
```

## Provider Webhooks

Use these routes for inbound email:

```text
POST /webhooks/email
POST /webhooks/email/generic
POST /webhooks/email/mailgun
POST /webhooks/email/sendgrid
POST /webhooks/email/postmark
```

Use these routes for WhatsApp:

```text
POST /webhooks/whatsapp
POST /webhooks/whatsapp/twilio
```

## SMTP Configuration

```env
SMTP_HOST=smtp.your-company.com
SMTP_PORT=587
SMTP_USERNAME=sales@your-company.com
SMTP_PASSWORD=your-smtp-password-or-app-password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=sales@your-company.com
SMTP_FROM_NAME=Your Company Sales
SALES_EMAIL=sales@your-company.com
```

Use an app password when your mailbox provider requires one.

## LLM Configuration

Any OpenAI-compatible `/v1/chat/completions` provider can work:

```env
LLM_PROVIDER=openai-compatible
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
```

If no model key is configured, the project falls back to simple rule-based drafts.

## Job Queue

Supported jobs:

```text
follow_up_reminder
refresh_intel
send_email
send_draft
```

API:

```text
POST /api/jobs
GET  /api/jobs
POST /api/jobs/{job_id}/retry
```

Local scheduler:

```powershell
python scripts\scheduler.py --intel
```

Local worker:

```powershell
python scripts\worker.py --once
python scripts\worker.py --poll-seconds 30
```

For production, run the scheduler through Windows Task Scheduler or cron, and run the worker through a process supervisor.

## Deployment and Operations

Health check:

```text
GET /health
```

Production environment template:

```text
.env.production.example
```

Windows production launcher:

```powershell
Copy-Item .env.production.example .env.production
notepad .env.production
powershell -ExecutionPolicy Bypass -File scripts\run_prod.ps1
```

Run behind HTTPS with a reverse proxy such as Caddy or Nginx. Keep `APP_HOST=127.0.0.1` when the reverse proxy runs on the same machine.

## Backups and Export

Create a SQLite backup:

```powershell
python scripts\backup_sqlite.py
```

Protected CSV export endpoints:

```text
GET /api/export/leads.csv
GET /api/export/messages.csv
GET /api/export/audit.csv
```

## Remaining Production Work

Before larger production use:

1. Configure HTTPS and a reverse proxy such as Caddy or Nginx.
2. Run the app, scheduler, and worker through Windows Task Scheduler, NSSM, systemd, or Docker Compose.
3. Schedule `scripts\backup_sqlite.py`.
4. Decide whether to migrate to PostgreSQL for multi-user production use.
5. Add bounce handling and complaint handling from your email provider.
6. Add privacy policy, retention rules, and an explicit consent workflow.
7. Replace generic RSS feeds with industry-specific sourcing, customs, trade show, tender, and chamber-of-commerce sources.
8. Add role-based access if more than one salesperson uses the dashboard.

## Verification

Run:

```powershell
python -m pytest tests -q
python scripts\api_smoke_test.py
python scripts\feasibility_lab.py
```

Current expected state: tests pass, API smoke test passes, and feasibility lab reports a 100% pass rate in offline mode.
