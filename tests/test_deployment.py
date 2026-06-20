import sqlite3

from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import ensure_database, get_db
from app.services.auth import create_session_token


def test_health_endpoint_reports_database_status(tmp_path, monkeypatch):
    db_path = tmp_path / "health.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["checks"]["database"] is True
    assert payload["status"] in {"ok", "degraded"}
    assert any("ADMIN_PASSWORD" in warning for warning in payload["warnings"])


def test_csv_export_requires_auth_and_returns_rows(tmp_path, monkeypatch):
    db_path = tmp_path / "export.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret-password")
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    get_settings.cache_clear()
    ensure_database()

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO leads(channel, name, email, score)
            VALUES ('email', 'Buyer', 'buyer@example.com', 80)
            """
        )

    from app.main import app

    settings = get_settings()
    with TestClient(app) as client:
        blocked = client.get("/api/export/leads.csv")
        assert blocked.status_code == 401

        client.cookies.set(settings.session_cookie_name, create_session_token("admin", settings))
        response = client.get("/api/export/leads.csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "buyer@example.com" in response.text


def test_sqlite_backup_creates_readable_copy(tmp_path, monkeypatch):
    db_path = tmp_path / "source.db"
    backup_dir = tmp_path / "backups"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    ensure_database()

    with get_db() as conn:
        conn.execute("INSERT INTO audit_logs(action, entity_type, detail) VALUES ('test', 'backup', 'ok')")

    from scripts.backup_sqlite import backup_database

    backup_path = backup_database(backup_dir)

    assert backup_path.exists()
    with sqlite3.connect(backup_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0] == 1
