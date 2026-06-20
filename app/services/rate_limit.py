from datetime import datetime, timedelta

from app.config import Settings
from app.db import get_db


def check_outbound_allowed(settings: Settings) -> tuple[bool, str]:
    with get_db() as conn:
        today_count = conn.execute(
            """
            SELECT COUNT(*) AS total FROM messages
            WHERE direction = 'outbound'
              AND status = 'sent'
              AND date(created_at) = date('now')
            """
        ).fetchone()["total"]
        if today_count >= settings.max_outbound_per_day:
            return False, f"Daily outbound limit reached: {today_count}/{settings.max_outbound_per_day}."

        latest = conn.execute(
            """
            SELECT created_at FROM messages
            WHERE direction = 'outbound' AND status = 'sent'
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()

    if latest and settings.min_seconds_between_outbound > 0:
        try:
            latest_at = datetime.fromisoformat(str(latest["created_at"]))
            next_allowed = latest_at + timedelta(seconds=settings.min_seconds_between_outbound)
            if datetime.utcnow() < next_allowed:
                return False, f"Outbound pacing active. Wait until {next_allowed.isoformat(timespec='seconds')} UTC."
        except ValueError:
            pass

    return True, "Allowed."
