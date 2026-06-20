# Feasibility Lab

This project includes an offline feasibility lab. It verifies the core business loop without real SMTP, WhatsApp, OpenAI, RSS, or public network credentials.

## Run It

```powershell
cd C:\Users\雷歆瑶\Documents\Codex\2026-06-16\new-chat-5\outputs\foreign-trade-autopilot
python scripts\feasibility_lab.py
```

API smoke test:

```powershell
python scripts\api_smoke_test.py
```

Unit tests:

```powershell
python -m pytest tests -q
```

## What It Verifies

- Inbound email creates a lead, scores it, records the message, and drafts a reply.
- Inbound WhatsApp creates a lead, scores it, records the message, and drafts a reply.
- Prospect CSV import works.
- Lead scoring recognizes buying intent.
- CRM follow-up fields update correctly.
- Cold outreach creates a draft instead of sending automatically.
- Draft approval flow exists.
- Opt-out checks block opted-out recipients.
- Deliverability checklist is generated.
- Provider-style inbound email payloads and attachment metadata are accepted.
- Jobs can be created and listed through the protected API.
- Health checks report database and deployment warning status.
- Lead, message, and audit CSV export routes are available after login.
- SQLite backups can be created with `scripts\backup_sqlite.py`.

## Output Files

```text
data/feasibility_report.html
data/feasibility_report.json
```

The API smoke test also creates:

```text
data/api_smoke_test.db
```

## Current Feasibility Judgment

The project is feasible as a local SOHO assistant and internal pilot:

1. Buyer messages can enter the system.
2. The system can identify and score leads.
3. The system can draft replies and cold outreach.
4. Human approval remains in the loop by default.
5. Follow-up work can be scheduled through the job queue.
6. Compliance checks such as opt-out and unsubscribe are present.
7. Basic deployment and operations checks are present.

It still needs real provider integration before production:

1. Real SMTP sending account.
2. Real inbound email provider such as Mailgun, SendGrid, or Postmark.
3. Real WhatsApp provider if WhatsApp is part of the workflow.
4. Real LLM API key if you want higher-quality writing.
5. HTTPS reverse proxy and process supervision.
6. Scheduled backups and periodic restore drills.
