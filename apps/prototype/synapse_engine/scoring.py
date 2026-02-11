from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Callable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .entities import extract_entities_simple, entity_ids
from .intent import intent_compatibility
from .perspective import perspective_alignment
from .utils import jaccard


@dataclass
class ScoredCandidate:
    id: str
    phrase: str
    provenance: str
    intent: str
    perspective: str
    confidence: float
    features: Dict[str, float]
    relevance_score: float


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def build_tfidf_embeddings(texts: List[str]) -> np.ndarray:
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    X = vec.fit_transform(texts)
    return X


def score_candidates(
    seed_phrase: str,
    seed_intent: str,
    seed_perspective: str,
    candidates: List[Dict[str, Any]],
    language: str,
    market: str,
    scoring_model: Dict[str, Any],
    perspective_model: Dict[str, Any],
) -> Tuple[List[ScoredCandidate], np.ndarray, np.ndarray]:
    """Compute feature components and relevance scores.

    Returns:
      scored list (aligned with candidates order),
      tfidf matrix for [seed + candidates],
      cosine similarity vector sim(seed, candidate).
    """

    weights = scoring_model.get("scoring_model", {}).get("relevance_score", {}).get("components", {})
    w = {k: float(v.get("weight", 0.0)) for k, v in weights.items()}

    # TF-IDF embedding similarity
    texts = [seed_phrase] + [c["phrase"] for c in candidates]
    X = build_tfidf_embeddings(texts)
    sims = cosine_similarity(X[0:1], X[1:]).flatten()

    seed_entities = entity_ids(extract_entities_simple(seed_phrase, language, market))

    scored: List[ScoredCandidate] = []

    for idx, c in enumerate(candidates):
        phrase = c["phrase"]
        intent = c["intent"]
        perspective = c["perspective"]
        conf = float(c.get("confidence", 0.55))

        cand_entities = entity_ids(extract_entities_simple(phrase, language, market))

        f_entity_overlap = jaccard(seed_entities, cand_entities)
        f_serp_overlap = float(c.get("serp_overlap", 0.0))  # 0 in offline runs
        f_embedding_similarity = float(sims[idx])
        f_intent_compatibility = intent_compatibility(seed_intent, intent, scoring_model)
        f_perspective_alignment = perspective_alignment(seed_perspective, perspective, perspective_model)

        feats = {
            "entity_overlap": clamp01(f_entity_overlap),
            "serp_overlap": clamp01(f_serp_overlap),
            "embedding_similarity": clamp01(f_embedding_similarity),
            "intent_compatibility": clamp01(f_intent_compatibility),
            "perspective_alignment": clamp01(f_perspective_alignment),
        }

        rel = 0.0
        for k, wk in w.items():
            rel += wk * float(feats.get(k, 0.0))
        rel = clamp01(rel)

        scored.append(
            ScoredCandidate(
                id=c["id"],
                phrase=phrase,
                provenance=c.get("provenance", "llm_inferred"),
                intent=intent,
                perspective=perspective,
                confidence=conf,
                features=feats,
                relevance_score=rel,
            )
        )

    return scored, X, sims


def mmr_select(
    scored: List[ScoredCandidate],
    X: np.ndarray,
    k: int,
    mmr_lambda: float,
    constraints: Dict[str, Any],
) -> List[ScoredCandidate]:
    """MMR selection with simple diversity constraints.

    Uses cosine similarity on TF-IDF vectors as the redundancy measure.
    """

    max_same_intent = int(constraints.get("max_same_intent", 15))
    max_same_perspective = int(constraints.get("max_same_perspective", 12))
    max_near_duplicate = int(constraints.get("max_near_duplicate", 3))

    # Near-dup threshold (not in spec; pragmatic)
    near_dup_sim = float(constraints.get("near_duplicate_similarity", 0.92))

    # Sort by base relevance score
    pool_idx = list(range(len(scored)))
    pool_idx.sort(key=lambda i: scored[i].relevance_score, reverse=True)

    selected: List[int] = []
    intent_counts: Dict[str, int] = {}
    persp_counts: Dict[str, int] = {}
    near_dup_count = 0

    def can_add(i: int) -> bool:
        nonlocal near_dup_count
        c = scored[i]
        if intent_counts.get(c.intent, 0) >= max_same_intent:
            return False
        if persp_counts.get(c.perspective, 0) >= max_same_perspective:
            return False
        # near-dup guard
        if selected:
            sims = cosine_similarity(X[i+1:i+2], X[[j+1 for j in selected]]).flatten()
            if sims.size and float(sims.max()) >= near_dup_sim:
                if near_dup_count >= max_near_duplicate:
                    return False
        return True

    # Start with best that satisfies constraints
    for i in pool_idx:
        if can_add(i):
            selected.append(i)
            c = scored[i]
            intent_counts[c.intent] = intent_counts.get(c.intent, 0) + 1
            persp_counts[c.perspective] = persp_counts.get(c.perspective, 0) + 1
            break

    # MMR loop
    remaining = [i for i in pool_idx if i not in selected]

    while remaining and len(selected) < k:
        best_i = None
        best_val = -1e9

        for i in remaining:
            if not can_add(i):
                continue
            # redundancy to selected
            if not selected:
                redundancy = 0.0
            else:
                sims = cosine_similarity(X[i+1:i+2], X[[j+1 for j in selected]]).flatten()
                redundancy = float(sims.max()) if sims.size else 0.0

            val = mmr_lambda * scored[i].relevance_score - (1.0 - mmr_lambda) * redundancy
            if val > best_val:
                best_val = val
                best_i = i

        if best_i is None:
            # if nothing satisfies constraints, relax near-dup only
            for i in list(remaining):
                c = scored[i]
                if intent_counts.get(c.intent, 0) >= max_same_intent:
                    continue
                if persp_counts.get(c.perspective, 0) >= max_same_perspective:
                    continue
                best_i = i
                break

        if best_i is None:
            break

        selected.append(best_i)
        remaining.remove(best_i)

        c = scored[best_i]
        intent_counts[c.intent] = intent_counts.get(c.intent, 0) + 1
        persp_counts[c.perspective] = persp_counts.get(c.perspective, 0) + 1

    return [scored[i] for i in selected][:k]
