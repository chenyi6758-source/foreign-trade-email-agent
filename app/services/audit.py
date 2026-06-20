from app.db import get_db


def log_event(action: str, entity_type: str, entity_id: str | int | None = None, detail: str = "", actor: str = "system") -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO audit_logs(actor, action, entity_type, entity_id, detail)
            VALUES (?, ?, ?, ?, ?)
            """,
            (actor, action, entity_type, str(entity_id) if entity_id is not None else None, detail),
        )
