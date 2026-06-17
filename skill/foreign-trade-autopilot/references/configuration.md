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
- `PORT=8787`: local dashboard port.

Recommended first run:

```bash
npm install
cp .env.example .env
npm run capabilities
npm run dashboard
```

Recommended SOHO workflow:

1. Import buyer CSV in the dashboard.
2. Review high-score leads.
3. Generate first-touch drafts.
4. Review drafts manually before sending.
5. Follow up after 3, 7, and 14 days.
6. Use email autopilot for inbound replies.

Production checklist:

- Use a dedicated mailbox or app password.
- Test on a small mailbox before a real sales inbox.
- Keep `MAX_EMAILS_PER_SCAN` low during rollout.
- Monitor `data/db.json` and SMTP sending logs.
- Back up `data/db.json` if conversation history matters.
- Keep the dashboard on `localhost` unless authentication is added.
- Keep WhatsApp disconnected until a dedicated account, dry-run policy, and frequency limits are ready.
