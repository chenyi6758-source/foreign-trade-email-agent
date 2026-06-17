---
name: foreign-trade-email-agent
description: Build, inspect, configure, and safely operate a foreign-trade AI email assistant that uses IMAP, SMTP, Anthropic Claude, lowdb, and dry-run safeguards. Use when Codex needs to improve this project, set up a runnable trade email agent, diagnose mailbox automation risks, draft configuration, or package the agent for GitHub/open-source release.
---

# Foreign Trade Email Agent

Use this skill for work on the `foreign-trade-email-agent` project or similar email automation agents.

## Workflow

1. Inspect `.env.example`, `src/config.js`, and `README.md` before changing runtime behavior.
2. Preserve the safe default: `DRY_RUN=true`. Never make live sending the default.
3. Avoid full mailbox scans. Keep `MAX_EMAILS_PER_SCAN` bounded and prefer recent or unread messages.
4. Keep `.env`, `data/`, `node_modules/`, real customer emails, and mailbox credentials out of git.
5. Run `npm test` and `npm run check` after code changes.
6. If dependencies change, run `npm audit --omit=dev` and explain any remaining findings.

## Safety Rules

- Do not send real email unless the user explicitly asks for live sending and `.env` has `DRY_RUN=false` or the command uses `--live`.
- Do not mark dry-run emails as processed unless `MARK_DRY_RUN_PROCESSED=true`.
- Treat AI output as a draft for business-critical customers. Recommend human review for high-value deals, complaints, legal topics, and pricing promises.
- Do not invent prices, certifications, lead times, or product specifications.

## Common Commands

```bash
npm install
npm run once
npm start
npm run contacts
npm run outreach -- --to buyer@example.com --name "John" --company "ABC Trading"
npm test
npm run check
```

## Files To Read

- Read `references/configuration.md` when setting up `.env` or explaining deployment.
- Read `src/mailer.js` before changing IMAP/SMTP behavior.
- Read `src/ai.js` before changing Claude prompts or model configuration.
- Read `src/db.js` before changing processed-message semantics.
