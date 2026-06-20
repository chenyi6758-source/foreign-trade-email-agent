# Release Checklist

Use this checklist before pushing the project to GitHub or creating a public release.

## Local Verification

```powershell
python -m pytest tests
python scripts\api_smoke_test.py
python scripts\feasibility_lab.py
python scripts\release_check.py
```

Expected result:

- Unit tests pass.
- API smoke test passes.
- Feasibility lab reports 100% pass rate in offline mode.
- Release check reports no tracked databases, logs, `.env` files, obvious secret patterns, or broken local docs links.

## Repository Naming

Recommended GitHub repository name:

```text
exportpilot-ai
```

Recommended description:

```text
SQLite-first FastAPI assistant for foreign-trade SOHO lead capture, CRM follow-up, compliant outreach drafts, and scheduled sales workflows.
```

Recommended topics:

```text
foreign-trade
sales-automation
fastapi
sqlite
crm
email-automation
lead-generation
soho
export-business
```

## Before Public Push

- Confirm `.env` is not present in `git ls-files`.
- Confirm `data/` contains only `data/.gitkeep` in Git.
- Confirm all example credentials are placeholders.
- Confirm `LICENSE`, `SECURITY.md`, and `CONTRIBUTING.md` are present.
- Confirm README links work.
- Decide whether GitHub repo visibility should be public or private.

## After Push

- Check GitHub Actions.
- Add repository description and topics.
- Add a screenshot or short demo GIF when the dashboard UI is finalized.
- Create a first release tag only after a real provider integration is tested.
