# Configuration Reference

Required for mailbox automation:

- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`
- `IMAP_HOST`, `IMAP_PORT`, `IMAP_USER`, `IMAP_PASS`
- `ANTHROPIC_API_KEY`
- `COMPANY_NAME`, `COMPANY_PRODUCTS`, `YOUR_NAME`, `YOUR_TITLE`

Safety settings:

- `DRY_RUN=true`: preview and record drafts only.
- `DRY_RUN=false`: send real email.
- `MAX_EMAILS_PER_SCAN=20`: scan only recent messages.
- `UNSEEN_ONLY=true`: scan unread mail only.
- `MARK_DRY_RUN_PROCESSED=false`: allow repeated dry-run previews.

Recommended first run:

```bash
npm install
cp .env.example .env
npm run once
```

Production checklist:

- Use a dedicated mailbox or app password.
- Test on a small mailbox before a real sales inbox.
- Keep `MAX_EMAILS_PER_SCAN` low during rollout.
- Monitor `data/db.json` and SMTP sending logs.
- Back up `data/db.json` if conversation history matters.
