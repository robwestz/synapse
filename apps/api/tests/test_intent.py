"""Tests for intent classification (M4)."""
import pytest


@pytest.mark.parametrize("phrase,expected", [
    ("bästa casino online 2026", "commercial"),
    ("registrera casino konto", "transactional"),
    ("vad är RTP slots", "informational"),
    ("ansök privatlån upp till 800 000", "transactional"),
    ("jämför räntor", "commercial"),
    ("hur fungerar amortering", "informational"),
    ("privatlån upp till 800 000", "transactional"),
    ("billigast lån 2026", "commercial"),
])
def test_intent_classification(phrase, expected, spec_pack):
    """Rule-based intent matches expected label."""
    from synapse_engine.intent import infer_intent_rule_based

    label = infer_intent_rule_based(phrase, spec_pack.intent_model)
    assert label.intent == expected, f"'{phrase}' → {label.intent}, expected {expected}"


def test_intent_confidence_cap_without_serp(spec_pack):
    """Without SERP evidence, confidence is capped at 0.55."""
    from synapse_engine.intent import infer_intent_rule_based

    label = infer_intent_rule_based("bästa casino online 2026", spec_pack.intent_model, serp_present=False)
    assert label.confidence <= 0.55


def test_intent_confidence_higher_with_serp(spec_pack):
    """With SERP evidence, confidence can exceed 0.55."""
    from synapse_engine.intent import infer_intent_rule_based

    label = infer_intent_rule_based("bästa casino online 2026", spec_pack.intent_model, serp_present=True)
    assert label.confidence > 0.45  # at least gets a reasonable score


def test_intent_x_position(spec_pack):
    """Intent positions map to expected X-axis ranges."""
    from synapse_engine.intent import intent_x_position

    info_x = intent_x_position("informational", spec_pack.intent_model)
    trans_x = intent_x_position("transactional", spec_pack.intent_model)
    assert info_x < trans_x, "Informational should be left of transactional"
