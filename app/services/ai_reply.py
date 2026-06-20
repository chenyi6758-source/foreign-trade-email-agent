from app.config import Settings


def _system_prompt() -> str:
    return (
        "You are a professional foreign trade sales assistant. "
        "Reply in the same language as the customer when possible. "
        "Be concise, helpful, and ask for missing RFQ details. "
        "Do not invent prices, certifications, lead time, stock, or shipping cost. "
        "Never promise compliance documents unless the user provided them in company context."
    )


def _extract_chat_text(response) -> str:
    content = response.choices[0].message.content
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(part.get("text", "") for part in content if isinstance(part, dict)).strip()
    return str(content).strip()


async def _chat_completion(messages: list[dict[str, str]], settings: Settings) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.effective_llm_api_key,
        base_url=settings.effective_llm_base_url,
        timeout=settings.llm_timeout_seconds,
    )
    response = await client.chat.completions.create(
        model=settings.effective_llm_model,
        messages=messages,
        temperature=settings.llm_temperature,
    )
    return _extract_chat_text(response)


def _fallback_reply(inbound_text: str, lead_name: str | None, settings: Settings) -> str:
    greeting = f"Hi {lead_name}," if lead_name else "Hi,"
    products = settings.company_products
    return (
        f"{greeting}\n\n"
        f"Thank you for contacting {settings.company_name}. We received your inquiry and can support "
        f"{products}.\n\n"
        "To prepare an accurate quotation, could you please share drawings/specifications, target quantity, "
        "destination country, and any required certifications or delivery date?\n\n"
        f"You can also reach us at {settings.sales_email}.\n\n"
        "Best regards,\n"
        f"{settings.company_name}"
    )


async def generate_auto_reply(inbound_text: str, lead_name: str | None, channel: str, settings: Settings) -> str:
    if not settings.effective_llm_api_key:
        return _fallback_reply(inbound_text, lead_name, settings)

    try:
        reply = await _chat_completion(
            [
                {
                    "role": "system",
                    "content": _system_prompt(),
                },
                {
                    "role": "user",
                    "content": (
                        f"Company: {settings.company_name}\n"
                        f"Products: {settings.company_products}\n"
                        f"Tone: {settings.company_tone}\n"
                        f"Channel: {channel}\n"
                        f"Customer name: {lead_name or 'unknown'}\n"
                        f"Customer message:\n{inbound_text}"
                    ),
                },
            ],
            settings,
        )
        return reply
    except Exception:
        return _fallback_reply(inbound_text, lead_name, settings)


async def generate_outreach_draft(
    recipient: str,
    product: str | None,
    pain_point: str | None,
    market: str | None,
    settings: Settings,
) -> tuple[str, str]:
    product_text = product or settings.company_products
    market_text = market or "your market"
    subject = f"Supplier option for {product_text}"

    body = (
        "Hi,\n\n"
        f"I am reaching out from {settings.company_name}. We help overseas buyers source {product_text} "
        f"for {market_text}.\n\n"
    )
    if pain_point:
        body += f"I noticed your team may be interested in {pain_point}. "
    body += (
        "If you are reviewing suppliers, we can share capability details, certificates, and a quotation "
        "after checking your specifications or drawings.\n\n"
        "Would it be useful if I send a short product sheet and sample reference?\n\n"
        "Best regards,\n"
        f"{settings.company_name}"
    )

    if settings.effective_llm_api_key:
        try:
            body = await _chat_completion(
                [
                    {
                        "role": "system",
                        "content": (
                            "Write compliant B2B cold outreach email drafts. "
                            "Keep them short, truthful, non-pushy, and easy to review. "
                            "Do not claim prior relationship unless provided."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Company: {settings.company_name}\n"
                            f"Products: {product_text}\n"
                            f"Market: {market_text}\n"
                            f"Recipient: {recipient}\n"
                            f"Pain point: {pain_point or 'unknown'}\n"
                            "Return only the email body, no markdown."
                        ),
                    },
                ],
                settings,
            )
        except Exception:
            pass

    return subject, body
