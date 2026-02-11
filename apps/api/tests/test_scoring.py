"""Tests for scoring and MMR selection (M7)."""
import pytest


def _make_test_candidates(spec_pack, n=30):
    """Generate a small candidate pool for testing."""
    from synapse_engine.normalization import normalize_phrase
    from synapse_engine.intent import infer_intent_rule_based
    from synapse_engine.perspective import infer_perspective_rule_based
    from synapse_engine.candidates import generate_candidates
    from synapse_engine.utils import stable_qid

    seed = "privatlån upp till 800 000"
    language, market = "sv", "SE"
    pool = generate_candidates(seed, language, market, target_pool=n)

    candidates = []
    for c in pool:
        nc = normalize_phrase(c.phrase, spec_pack.normalization_model)
        iid = infer_intent_rule_based(nc.canonical, spec_pack.intent_model)
        pid = infer_perspective_rule_based(nc.canonical, spec_pack.perspective_model)
        cid = stable_qid(nc.canonical, language, market)
        candidates.append({
            "id": cid,
            "phrase": nc.canonical,
            "provenance": c.provenance,
            "intent": iid.intent,
            "perspective": pid.perspective,
            "confidence": min(iid.confidence, pid.confidence),
            "serp_overlap": 0.0,
        })
    return seed, candidates


def test_score_candidates_returns_correct_count(spec_pack):
    """score_candidates returns one ScoredCandidate per input candidate."""
    from synapse_engine.scoring import score_candidates

    seed, candidates = _make_test_candidates(spec_pack, n=20)
    scored, X, sims = score_candidates(
        seed_phrase=seed,
        seed_intent="transactional",
        seed_perspective="provider",
        candidates=candidates,
        language="sv",
        market="SE",
        scoring_model=spec_pack.scoring_model,
        perspective_model=spec_pack.perspective_model,
    )
    assert len(scored) == 20


def test_mmr_select_returns_exact_k(spec_pack):
    """MMR selection returns exactly k items."""
    from synapse_engine.scoring import score_candidates, mmr_select, build_tfidf_embeddings

    seed, candidates = _make_test_candidates(spec_pack, n=50)
    scored, X, sims = score_candidates(
        seed_phrase=seed,
        seed_intent="transactional",
        seed_perspective="provider",
        candidates=candidates,
        language="sv",
        market="SE",
        scoring_model=spec_pack.scoring_model,
        perspective_model=spec_pack.perspective_model,
    )

    k = 15
    selected = mmr_select(scored, X, k=k, mmr_lambda=0.75, constraints={"max_same_intent": 10, "max_same_perspective": 8})
    assert len(selected) == k


def test_relevance_scores_in_range(spec_pack):
    """All relevance scores are in [0, 1]."""
    from synapse_engine.scoring import score_candidates

    seed, candidates = _make_test_candidates(spec_pack, n=20)
    scored, _, _ = score_candidates(
        seed_phrase=seed,
        seed_intent="transactional",
        seed_perspective="provider",
        candidates=candidates,
        language="sv",
        market="SE",
        scoring_model=spec_pack.scoring_model,
        perspective_model=spec_pack.perspective_model,
    )
    for sc in scored:
        assert 0.0 <= sc.relevance_score <= 1.0, f"Score {sc.relevance_score} out of range"
