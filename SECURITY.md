# Security Policy

Foreign Trade Autopilot handles sales leads, email content, contact details, and outbound messaging. Treat all production data as sensitive.

## Supported Versions

This repository is an MVP. Security fixes should target the `main` branch.

## Reporting a Vulnerability

Do not open a public issue for secrets, authentication bypasses, data leaks, or sending abuse risks. Report privately to the repository owner.

Include:

- A short description of the issue.
- Affected route, script, or module.
- Steps to reproduce.
- Potential impact.
- Suggested fix, if known.

## Operational Security Checklist

- Change `ADMIN_PASSWORD`, `SESSION_SECRET`, `WEBHOOK_SHARED_SECRET`, and `UNSUBSCRIBE_SECRET`.
- Keep `.env` out of Git.
- Run behind HTTPS before exposing webhook URLs publicly.
- Use provider app passwords or scoped API keys.
- Enable SPF, DKIM, DMARC, and unsubscribe handling for outbound email.
- Schedule SQLite backups and periodically test restores.
- Review audit logs for unexpected login, webhook, and sending activity.
