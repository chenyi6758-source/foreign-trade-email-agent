import pytest

from app.config import Settings
from app.services.ai_reply import generate_auto_reply


@pytest.mark.asyncio
async def test_fallback_reply_without_openai_key():
    settings = Settings(openai_api_key="", company_name="ACME Export", company_products="valves")
    reply = await generate_auto_reply("Need price", "Alice", "email", settings)
    assert "Alice" in reply
    assert "ACME Export" in reply
    assert "drawings" in reply.lower() or "specifications" in reply.lower()
