import csv
from io import StringIO

from app.services.leads import LeadSignal, upsert_lead


def _pick(row: dict[str, str], names: list[str]) -> str | None:
    normalized = {key.strip().lower(): value.strip() for key, value in row.items() if key}
    for name in names:
        value = normalized.get(name)
        if value:
            return value
    return None


def import_prospect_csv(csv_text: str, source: str = "csv") -> list[dict]:
    reader = csv.DictReader(StringIO(csv_text))
    imported: list[dict] = []

    for row in reader:
        email = _pick(row, ["email", "e-mail", "mail"])
        phone = _pick(row, ["phone", "mobile", "whatsapp", "tel"])
        name = _pick(row, ["name", "contact", "contact name", "buyer"])
        company = _pick(row, ["company", "company name", "organization", "importer"])
        country = _pick(row, ["country", "market"])
        note = _pick(row, ["note", "notes", "message", "requirement", "inquiry"]) or ""

        if not email and not phone:
            continue

        message = " ".join(part for part in [company, country, note] if part)
        lead = upsert_lead(
            LeadSignal(
                channel=source,
                name=name,
                email=email,
                phone=phone,
                company=company,
                message=message,
            )
        )
        imported.append(lead)

    return imported
