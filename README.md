# Foreign Trade Email Agent

*Product codename: ExportPilot AI*

ExportPilot AI is a FastAPI-based MVP for export sales teams and solo foreign-trade operators. It captures inbound buyer messages, scores and manages leads, drafts compliant outreach, tracks follow-ups, and keeps slow work in a small SQLite-backed job queue.

The project is designed to be useful on a local Windows laptop first, then deployable to a small VPS when you are ready.

Inbound replies use a deterministic safety gate in addition to the LLM prompt:
normal product questions can follow the configured auto-reply path, while
messages involving pricing, certificates, contracts, payments, disputes,
legal issues, or product safety are kept as drafts for human review. This is a
conservative guardrail, not a substitute for a production compliance review.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Release Checklist](docs/RELEASE.md)
- [Commercial Readiness Notes](COMMERCIAL_READY.md)
- [Feasibility Lab](FEASIBILITY.md)
- [Security Policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## Tech Stack

- Python 3.11+
- FastAPI
- SQLite
- Jinja2
- SMTP
- Twilio WhatsApp or Meta WhatsApp Cloud API
- OpenAI-compatible LLM endpoint, optional

## Quick Start

```powershell
cd foreign-trade-email-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000` in your browser.

Default admin settings are in `.env.example`. Change these before any real use.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
