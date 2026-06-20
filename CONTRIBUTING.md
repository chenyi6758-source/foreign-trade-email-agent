# Contributing

Thanks for considering a contribution to Foreign Trade Autopilot.

## Development Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Run tests:

```powershell
python -m pytest tests
```

Run the API smoke test:

```powershell
python scripts\api_smoke_test.py
```

## Contribution Rules

- Do not commit `.env`, real credentials, customer data, SQLite databases, logs, or attachments.
- Keep cold outreach safe by default. New outbound automation should remain draft-first unless explicitly approved by the user.
- Add or update tests for changes to webhooks, sending, lead scoring, authentication, exports, jobs, or compliance behavior.
- Keep the SQLite-first path working unless the project explicitly moves to PostgreSQL.
- Prefer clear, boring operations over complex infrastructure.

## Pull Request Checklist

- Tests pass with `python -m pytest tests`.
- `python scripts\api_smoke_test.py` passes.
- Documentation reflects new routes, scripts, or environment variables.
- New external integrations are optional and fail safely when credentials are missing.
