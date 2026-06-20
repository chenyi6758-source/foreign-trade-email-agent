from app.config import Settings
from app.services.auth import create_session_token, verify_credentials, verify_session_token


def test_credentials_and_session_token_round_trip():
    settings = Settings(
        admin_username="admin",
        admin_password="secret-password",
        session_secret="test-secret",
    )

    assert verify_credentials("admin", "secret-password", settings)
    assert not verify_credentials("admin", "wrong", settings)

    token = create_session_token("admin", settings)
    assert verify_session_token(token, settings) == "admin"
    assert verify_session_token(token, Settings(admin_username="admin", session_secret="other")) is None
