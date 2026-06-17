---
name: foreign-trade-autopilot
description: Build, inspect, configure, and safely extend a foreign-trade AI automation workspace covering email autopilot, outreach, CRM, lead discovery, market intelligence, WhatsApp adapter boundaries, and GitHub/open-source packaging. Use when Codex needs to work on this project, diagnose automation risks, add modules, prepare Hermes/Codex skill resources, or help operate the agent safely.
---

# Foreign Trade Autopilot

Use this skill for the `foreign-trade-autopilot` project or similar foreign trade automation workspaces.

## Workflow

1. Start by reading `README.md`, `.env.example`, and `src/capabilities.js`.
2. Preserve the safe default: `DRY_RUN=true`. Never make live sending the default.
3. Treat email as one module, not the whole product. Keep room for CRM, leads, market intelligence, and messaging channels.
4. Avoid full mailbox scans. Keep `MAX_EMAILS_PER_SCAN` bounded and prefer recent or unread messages.
5. Keep `.env`, `data/`, `node_modules/`, customer data, and mailbox credentials out of git.
6. Run `npm test`, `npm run check`, and `npm audit --omit=dev` after meaningful code changes.

## Module Guidance

- Email: read `src/main.js`, `src/mailer.js`, and `src/ai.js` before changing inbox or sending behavior.
- CRM: read `src/db.js` before changing contacts, threads, or processed-message state.
- Leads: extend `src/leads.js` for CSV, search snippets, directories, or scraped page text.
- Market intelligence: extend `src/market_intel.js` for RSS/news normalization and daily digest output.
- WhatsApp: use `src/whatsapp.js` as the adapter boundary. Do not add live WhatsApp sending without explicit user approval, QR-login handling, dry-run, rate limiting, and account-risk notes.
- Skill packaging: keep this skill concise and put longer setup details in `references/configuration.md`.

## Safety Rules

- Do not send real email or messages unless the user explicitly asks for live sending and `DRY_RUN=false` or `--live` is set.
- Do not mark dry-run emails as processed unless `MARK_DRY_RUN_PROCESSED=true`.
- Do not invent prices, certifications, lead times, product parameters, stock, or legal claims.
- Recommend human review for high-value customers, complaints, pricing, compliance, legal topics, and WhatsApp rollout.

## Common Commands

```bash
npm install
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
