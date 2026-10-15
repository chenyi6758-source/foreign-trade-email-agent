"""Deterministic safety gates for inbound AI replies.

The LLM prompt asks the model not to invent commercial or compliance details,
but a prompt alone cannot decide whether an outbound message should be sent
automatically.  This module provides a small, explainable gate for messages
that should remain drafts until a human reviews them.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MessageRisk:
    """Risk assessment attached to an inbound message."""

    level: str
    reasons: tuple[str, ...]

    @property
    def requires_human_review(self) -> bool:
        return self.level != "low"


_REVIEW_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "commercial_commitment",
        (
            "price",
            "pricing",
            "quotation",
            "quote",
            "报价",
            "价格",
            "discount",
            "折扣",
            "lead time",
            "delivery date",
            "交期",
            "交货",
            "moq",
        ),
    ),
    (
        "compliance_or_contract",
        (
            "certificate",
            "certification",
            "compliance",
            "contract",
            "agreement",
            "法律",
            "合同",
            "认证",
            "ce certificate",
            "rohs",
        ),
    ),
    (
        "payment_or_dispute",
        (
            "payment",
            "bank account",
            "wire transfer",
            "refund",
            "chargeback",
            "complaint",
            "dispute",
            "付款",
            "银行账户",
            "退款",
            "投诉",
        ),
    ),
)

_HIGH_RISK_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "legal_or_safety_issue",
        (
            "lawsuit",
            "lawyer",
            "legal action",
            "injury",
            "accident",
            "recall",
            "诉讼",
            "律师",
            "受伤",
            "事故",
            "召回",
        ),
    ),
)


def classify_inbound_message(text: str, subject: str = "") -> MessageRisk:
    """Classify an inbound message with transparent keyword rules.

    This is deliberately conservative and deterministic.  A ``review`` result
    keeps the generated response as a draft when automatic sending is enabled;
    a ``high`` result is reserved for legal, safety, recall, or similar issues.
    The classifier is a safety gate, not a replacement for human review.
    """
    combined = f"{subject}\n{text}".casefold()
    review_reasons = tuple(
        reason for reason, markers in _REVIEW_MARKERS if any(marker in combined for marker in markers)
    )
    high_reasons = tuple(
        reason for reason, markers in _HIGH_RISK_MARKERS if any(marker in combined for marker in markers)
    )
    if high_reasons:
        return MessageRisk("high", high_reasons + review_reasons)
    if review_reasons:
        return MessageRisk("review", review_reasons)
    return MessageRisk("low", ())
