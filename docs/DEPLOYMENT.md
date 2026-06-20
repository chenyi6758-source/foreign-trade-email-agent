# Deployment Guide

This guide describes a small production deployment for a solo operator or small export team.

## 1. Prepare Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.production.example .env.production
notepad .env.production
```

Change all default secrets:

```text
ADMIN_PASSWORD
SESSION_SECRET
WEBHOOK_SHARED_SECRET
UNSUBSCRIBE_SECRET
```

## 2. Start the App

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_prod.ps1
```

Health check:

```text
http://127.0.0.1:8000/health
```

## 3. Run Worker and Scheduler

One scheduler run:

```powershell
python scripts\scheduler.py --intel
```

Worker:

```powershell
python scripts\worker.py --poll-seconds 30
```

On Windows, use Task Scheduler or NSSM to keep these running. On Linux, use systemd or Docker Compose.

## 4. Add HTTPS

Run the app on `127.0.0.1` and put Caddy, Nginx, Cloudflare Tunnel, or another reverse proxy in front of it.

Production `.env.production` should use:

```env
APP_ENV=production
APP_BASE_URL=https://your-domain.example.com
APP_HOST=127.0.0.1
APP_PORT=8000
```

## 5. Back Up SQLite

Manual backup:

```powershell
python scripts\backup_sqlite.py
```

Schedule this script daily before storing real customer records. Periodically test that a backup can be restored and opened.

## 6. Provider Setup

Email:

- Configure SMTP.
- Configure inbound Mailgun, SendGrid, Postmark, or a generic webhook relay.
- Configure SPF, DKIM, DMARC, and bounce handling.

WhatsApp:

- Use Twilio or Meta WhatsApp Cloud API.
- Keep template and opt-out rules aligned with your provider policy.

LLM:

- Configure an OpenAI-compatible endpoint if higher-quality drafting is needed.
- Keep rule-based fallback enabled for missing credentials.
