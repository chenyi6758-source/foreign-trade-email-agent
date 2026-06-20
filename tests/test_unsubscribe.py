from app.config import Settings
from app.services.compliance import append_unsubscribe
from app.services.unsubscribe import create_unsubscribe_token, unsubscribe_url, verify_unsubscribe_token


def test_unsubscribe_token_and_footer():
    settings = Settings(
        app_base_url="https://example.com",
        unsubscribe_secret="unit-test-secret",
        unsubscribe_text="Reply STOP to opt out.",
    )

    token = create_unsubscribe_token("buyer@example.com", settings)
    assert verify_unsubscribe_token("buyer@example.com", token, settings)
    assert not verify_unsubscribe_token("other@example.com", token, settings)

    url = unsubscribe_url("buyer@example.com", settings)
    assert url.startswith("https://example.com/unsubscribe?")
    assert "token=" in url

    body = append_unsubscribe("Hello", settings, "buyer@example.com")
    assert "Reply STOP" in body
    assert "Unsubscribe:" in body
