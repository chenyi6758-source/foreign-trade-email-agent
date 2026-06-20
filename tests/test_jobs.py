import asyncio

import pytest

from app.config import get_settings
from app.db import ensure_database, get_db
from app.services.jobs import create_job, enqueue_due_follow_up_jobs, fail_job, get_job, retry_job, run_due_jobs


@pytest.fixture()
def temp_database(tmp_path, monkeypatch):
    db_path = tmp_path / "jobs.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("SMTP_HOST", "")
    get_settings.cache_clear()
    ensure_database()
    return db_path


def test_job_queue_processes_due_job(temp_database):
    job = create_job("follow_up_reminder", {"lead_id": 123})

    async def fake_processor(claimed):
        return {"seen": claimed["payload"]["lead_id"]}

    result = asyncio.run(run_due_jobs(limit=1, processor=fake_processor))

    assert result["count"] == 1
    saved = get_job(job["id"])
    assert saved["status"] == "completed"
    assert saved["attempts"] == 1


def test_failed_job_can_be_retried(temp_database):
    job = create_job("follow_up_reminder", {"lead_id": 456})
    fail_job(job["id"], "temporary failure")

    queued = retry_job(job["id"])

    assert queued["status"] == "queued"
    assert queued["last_error"] == ""


def test_follow_up_scheduler_avoids_duplicate_jobs(temp_database):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO leads(channel, name, email, next_follow_up_at, notes)
            VALUES ('email', 'Buyer', 'buyer@example.com', '2000-01-01 09:00:00', 'Send quotation')
            """
        )

    first = enqueue_due_follow_up_jobs()
    second = enqueue_due_follow_up_jobs()

    assert len(first) == 1
    assert len(second) == 0
