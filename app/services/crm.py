from app.db import get_db, rows_to_dicts


PIPELINE_STAGES = ["new", "contacted", "qualified", "quoted", "negotiating", "won", "lost", "nurture"]


def update_lead(lead_id: int, updates: dict) -> dict | None:
    allowed_fields = {
        "stage",
        "owner",
        "priority",
        "next_follow_up_at",
        "notes",
        "deal_value",
        "status",
        "consent_status",
        "country",
    }
    clean = {key: value for key, value in updates.items() if key in allowed_fields and value is not None}
    if not clean:
        return None

    assignments = [f"{key} = ?" for key in clean]
    params = list(clean.values()) + [lead_id]
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not existing:
            return None
        conn.execute(
            f"UPDATE leads SET {', '.join(assignments)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            params,
        )
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(row)


def pipeline_summary() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT stage, COUNT(*) AS total, COALESCE(SUM(deal_value), 0) AS deal_value
            FROM leads
            GROUP BY stage
            """
        ).fetchall()
    found = {row["stage"]: dict(row) for row in rows}
    return [
        {
            "stage": stage,
            "total": found.get(stage, {}).get("total", 0),
            "deal_value": found.get(stage, {}).get("deal_value", 0),
        }
        for stage in PIPELINE_STAGES
    ]


def follow_up_due(limit: int = 50) -> list[dict]:
    with get_db() as conn:
        return rows_to_dicts(
            conn.execute(
                """
                SELECT * FROM leads
                WHERE next_follow_up_at IS NOT NULL
                  AND next_follow_up_at != ''
                  AND datetime(next_follow_up_at) <= datetime('now', '+1 day')
                ORDER BY datetime(next_follow_up_at) ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        )
