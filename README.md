# Foreign Trade Email Agent

Safe-by-default AI email assistant for foreign trade teams. It reads recent inbound email through IMAP, classifies intent with Claude, drafts a professional reply, and can send through SMTP after you explicitly disable dry-run mode.

## What was missing in the original package

- No safe default: generated replies were sent automatically.
- Inbox scanning used `1:*`, which can process the entire mailbox on first run.
- `npm test` pointed to a missing file.
- `nodemailer@6.x` had audit findings.
- No environment validation, no dry-run mode, and no guard against overlapping scan loops.
- The archive included `node_modules`, which is not suitable for GitHub.

## Quick Start

```bash
npm install
cp .env.example .env
npm run once
```

The first run is dry-run by default. It prints proposed replies but does not send email.

To enable real sending after testing:

```env
DRY_RUN=false
```

Then run:

```bash
npm start
```

## Scripts

```bash
npm run once       # scan once and exit
npm start          # scan forever using CHECK_INTERVAL
npm run contacts   # view local contacts and thread history
npm run outreach -- --to buyer@example.com --name "John" --company "ABC Trading"
npm test
npm run check
```

## Safety Controls

- `DRY_RUN=true` by default.
- `MAX_EMAILS_PER_SCAN` limits how many recent messages are inspected.
- `UNSEEN_ONLY=true` can restrict processing to unread messages.
- A run lock prevents overlapping scans when AI or mail calls are slow.
- Processed message state is stored in `data/db.json`.
- Dry runs do not mark messages processed unless `MARK_DRY_RUN_PROCESSED=true`.

## GitHub Open Source Checklist

- Keep `.env` out of git.
- Do not commit `data/db.json`, real customer emails, or `node_modules`.
- Add a clear disclaimer before production use: AI email replies should be reviewed for regulated or high-value customers.
- Rotate any mailbox app passwords that were ever shared in archives.

## Codex/Hermes Skill

A complete skill package is included at:

```text
skill/foreign-trade-email-agent/
```

Install it by copying that folder into your Codex skills directory, or keep it inside this repo as project-local guidance.
