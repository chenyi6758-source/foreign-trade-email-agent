---
name: foreign-trade-soho-workflow
description: Run a safe foreign-trade SOHO AI assistant workflow for lead intake, lead scoring, outreach draft creation, follow-up planning, inbound email review, CRM updates, and daily sales summaries. Use when Codex, Hermes, Lobster, or another automation AI assistant should help a solo exporter or small trade team execute daily foreign-trade work rather than merely edit the project code.
---

# Foreign Trade SOHO Workflow

Use this skill to operate the `foreign-trade-autopilot` workspace as an AI sales assistant for a foreign trade SOHO user.

## Default Operating Mode

1. Work in dry-run/review-first mode unless the user explicitly authorizes live sending.
2. Treat AI-written emails and WhatsApp messages as drafts until a human approves them.
3. Never invent prices, stock, certifications, lead times, payment terms, shipping promises, or legal claims.
4. Store operational data in the project database through the existing app/API, not in ad hoc files.
5. Keep `.env`, `data/`, credentials, buyer lists, and real customer data out of git.

## Daily Workflow

1. Check setup: confirm `.env`, company profile, and `DRY_RUN=true`.
2. Intake leads: import CSV/text leads into the dashboard or data layer.
3. Score leads: prioritize buyers with email, website, importer/distributor signals, target keywords, and market fit.
4. Draft outreach: create first-touch email drafts for qualified leads.
5. Plan follow-up: schedule day 3, day 7, and day 14 follow-ups.
6. Review inbox: run one safe email scan for recent inbound replies.
7. Update CRM: keep lead stages, drafts, replies, and follow-up status current.
8. Produce summary: report new leads, high-score leads, drafts, overdue follow-ups, and next actions.

Read `references/workflow.md` for the full procedure and decision rules.

## Automation Commands

Use these from the project root:

```bash
npm run dashboard
npm run capabilities
npm run once
npm run contacts
npm test
npm run check
```

For a self-contained feasibility demo that does not send email or require external APIs:

```bash
node skill/foreign-trade-soho-workflow/scripts/run-demo-workflow.mjs
```

## Required Checks Before Live Sending

- The user explicitly asks for live sending.
- `.env` has `DRY_RUN=false`.
- The mailbox is a dedicated test or outreach mailbox.
- Daily sending limits are known.
- The draft content was reviewed for product facts and compliance.
- The lead is not duplicated, bounced, unsubscribed, or blacklisted.

If any check fails, keep the message as a draft and explain what is missing.
