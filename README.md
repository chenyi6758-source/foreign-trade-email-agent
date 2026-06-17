# Foreign Trade Autopilot

Foreign Trade Autopilot is a safe-by-default AI workspace for foreign trade SOHO operators and small export teams. It started as an email reply agent, but now grows toward a daily sales workspace: lead pool, outreach drafts, follow-up reminders, email handling, CRM records, market intelligence, and future WhatsApp integration.

The project intentionally keeps dangerous automation off by default. AI can draft and organize work first; live sending requires explicit configuration.

## Current Capabilities

| Area | Status | Command |
| --- | --- | --- |
| Email autopilot | Runnable | `npm run once` / `npm start` |
| Manual outreach email | Runnable | `npm run outreach -- --to buyer@example.com` |
| Local CRM records | Runnable | `npm run contacts` |
| SOHO dashboard | Runnable | `npm run dashboard` |
| Lead import and scoring | Starter module | `npm run leads:demo` |
| Market intelligence digest | Starter module | `npm run intel:demo` |
| WhatsApp channel | Adapter placeholder | `npm run whatsapp:status` |
| Hermes/Codex skill | Valid skill package | `skill/foreign-trade-autopilot/` |
| SOHO workflow skill | Validatable workflow skill | `skill/foreign-trade-soho-workflow/` |

## What This Solves For A SOHO Exporter

- Import buyer leads from CSV or copied directory data.
- Score leads by email, website, keywords, and buyer-type signals.
- Create first-touch outreach drafts without immediately sending them.
- Keep a simple draft queue for review.
- Schedule follow-up reminders after first outreach.
- Read recent inbound email and draft safe AI replies.
- Store contacts, conversation history, processed mail, leads, drafts, and follow-ups locally.

## Quick Start

```bash
npm install
cp .env.example .env
npm run capabilities
npm run dashboard
```

Open the local dashboard:

```text
http://localhost:8787
```

Run one safe email scan:

```bash
npm run once
```

By default `DRY_RUN=true`, so the first run previews replies and records drafts instead of sending real email.

## SOHO Daily Workflow

1. Collect buyer leads from exhibitions, directories, Google snippets, LinkedIn notes, or CSV files.
2. Paste/import them into the dashboard.
3. Review lead scores and company details.
4. Generate outreach drafts for the best leads.
5. Review and manually send or adapt the drafts.
6. Follow up after 3 days, then 7 days, then 14 days.
7. Use inbound email autopilot to classify replies and draft responses.

## Commands

```bash
npm run dashboard
npm run capabilities
npm run once
npm start
npm run contacts
npm run outreach -- --to buyer@example.com --name "John" --company "ABC Trading"
npm run leads:demo
npm run intel:demo
npm run whatsapp:status
npm test
npm run check
```

## Configuration

Copy `.env.example` to `.env` and fill in:

- SMTP and IMAP mailbox credentials
- `ANTHROPIC_API_KEY`
- company name, products, sender name, and title

Keep this setting for early testing:

```env
DRY_RUN=true
```

Only enable live sending after testing with a dedicated mailbox:

```env
DRY_RUN=false
```

## Safety Controls

- `DRY_RUN=true` by default.
- `MAX_EMAILS_PER_SCAN` limits each inbox scan.
- `UNSEEN_ONLY=true` can restrict scans to unread messages.
- The scan loop has a lock to avoid overlapping runs.
- Dry-run messages are not marked processed unless `MARK_DRY_RUN_PROCESSED=true`.
- WhatsApp is not connected by default because QR login, account risk, and sending limits need explicit rollout planning.
- The dashboard is local-only and has no authentication yet. Keep it on `localhost`.

## Project Structure

```text
src/
  ai.js              Claude classification and email drafting
  config.js          environment and CLI parsing
  db.js              local CRM, leads, drafts, follow-ups, mail state
  mailer.js          IMAP/SMTP email channel
  main.js            email autopilot entrypoint
  send_outreach.js   manual outreach command
  view_contacts.js   contact and thread viewer
  leads.js           lead extraction, CSV parsing, scoring, draft builder
  market_intel.js    starter market intelligence digest
  whatsapp.js        WhatsApp adapter boundary
  capabilities.js    capability table
  server.js          local SOHO dashboard API and static server
public/
  index.html
  styles.css
  app.js
skill/
  foreign-trade-autopilot/
```

## Roadmap

- Add lead stage changes in the dashboard.
- Add send-approved-draft workflow with rate limits.
- Add CSV export for leads, drafts, and follow-ups.
- Add product knowledge base: MOQ, certificates, packaging, lead time, target markets, FAQ.
- Add follow-up sequences: day 3, day 7, day 14.
- Add Gmail OAuth support.
- Add website/email discovery from buyer websites.
- Add RSS/news monitoring for daily market intelligence.
- Add WhatsApp adapter with dry-run, QR login, and strict sending limits.
- Add GitHub Actions for test and audit.
- Add SQLite/Postgres storage for production use.

## Open Source Notes

Do not commit `.env`, `data/`, real customer data, mailbox passwords, API keys, or `node_modules/`.

AI-generated business messages should be reviewed before sending to important buyers, complaint cases, pricing discussions, compliance issues, or legal topics.

## Hermes / Codex Skill

Two skill packages are included:

```text
skill/foreign-trade-autopilot/       # project development and maintenance
skill/foreign-trade-soho-workflow/   # daily SOHO business automation workflow
```

Use `foreign-trade-autopilot` to guide future project development. Use `foreign-trade-soho-workflow` when an AI assistant should help run the daily business workflow: import leads, score buyers, create outreach drafts, schedule follow-ups, review inbound email, and produce daily summaries.

Validate the workflow skill demo without sending email:

```bash
node skill/foreign-trade-soho-workflow/scripts/run-demo-workflow.mjs
```
