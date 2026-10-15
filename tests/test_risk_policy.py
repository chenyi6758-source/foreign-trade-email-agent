from app.services.risk_policy import classify_inbound_message


def test_normal_inquiry_is_low_risk():
    risk = classify_inbound_message("Could you send your product catalogue?")

    assert risk.level == "low"
    assert not risk.requires_human_review
    assert risk.reasons == ()


def test_commercial_message_requires_review():
    risk = classify_inbound_message("Please send your price and MOQ for 500 pieces.")

    assert risk.level == "review"
    assert risk.requires_human_review
    assert "commercial_commitment" in risk.reasons


def test_legal_or_safety_message_is_high_risk():
    risk = classify_inbound_message("We need to discuss a product injury and possible lawsuit.")

    assert risk.level == "high"
    assert risk.requires_human_review
    assert "legal_or_safety_issue" in risk.reasons
