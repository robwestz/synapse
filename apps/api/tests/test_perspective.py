"""Tests for perspective classification (M5)."""
import pytest


@pytest.mark.parametrize("phrase,expected", [
    ("ansök om privatlån", "provider"),
    ("hur mycket kan jag låna", "seeker"),
    ("jämför räntor", "advisor"),
    ("konsumentkreditlagen", "regulator"),
    ("regler för lån", "regulator"),
])
def test_perspective_classification(phrase, expected, spec_pack):
    """Rule-based perspective matches expected label."""
    from synapse_engine.perspective import infer_perspective_rule_based

    label = infer_perspective_rule_based(phrase, spec_pack.perspective_model)
    assert label.perspective == expected, f"'{phrase}' → {label.perspective}, expected {expected}"


def test_perspective_confidence_cap_without_serp(spec_pack):
    """Without SERP evidence, confidence is capped at 0.55."""
    from synapse_engine.perspective import infer_perspective_rule_based

    label = infer_perspective_rule_based("ansök om privatlån", spec_pack.perspective_model, serp_present=False)
    assert label.confidence <= 0.55


def test_perspective_y_position(spec_pack):
    """Perspective positions map to expected Y-axis ranges."""
    from synapse_engine.perspective import perspective_y_position

    seeker_y = perspective_y_position("seeker", spec_pack.perspective_model)
    provider_y = perspective_y_position("provider", spec_pack.perspective_model)
    # They should be different (seeker at top, provider at bottom or vice versa)
    assert seeker_y != provider_y
