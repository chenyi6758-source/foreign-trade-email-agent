from app.services.leads import score_lead


def test_score_lead_detects_buying_intent():
    score, tags = score_lead("Please send quotation, MOQ, and sample price for our distributor team.")
    assert score >= 60
    assert "quotation" in tags
    assert "moq" in tags
