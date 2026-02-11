# Minimal scoring + MMR selection reference
# NOTE: This is a reference, not a full pipeline. It expects you to supply:
# - candidate features (entity_overlap, serp_overlap, embedding_sim, intent_distance, perspective_distance)

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple
import math

@dataclass
class Candidate:
    id: str
    phrase: str
    features: Dict[str, float]  # entity_overlap, serp_overlap, embedding_similarity, intent_compatibility, perspective_alignment
    base_score: float = 0.0

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def score_candidate(c: Candidate, weights: Dict[str, float]) -> float:
    s = 0.0
    for k, w in weights.items():
        s += w * float(c.features.get(k, 0.0))
    c.base_score = clamp01(s)
    return c.base_score

def cosine_sim(vec_a: List[float], vec_b: List[float]) -> float:
    # If you already have embeddings, use them. This helper is optional.
    dot = sum(a*b for a,b in zip(vec_a, vec_b))
    na = math.sqrt(sum(a*a for a in vec_a))
    nb = math.sqrt(sum(b*b for b in vec_b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na*nb)

def mmr_select(candidates: List[Candidate], k: int, lam: float, sim_fn) -> List[Candidate]:
    """Maximal Marginal Relevance selection.
    sim_fn: function(cand_a, cand_b)-> similarity (0..1)
    """
    selected: List[Candidate] = []
    pool = candidates[:]
    pool.sort(key=lambda x: x.base_score, reverse=True)

    if not pool:
        return selected

    # start with best
    selected.append(pool.pop(0))

    while pool and len(selected) < k:
        best_idx = None
        best_val = -1e9
        for i, c in enumerate(pool):
            redundancy = max((sim_fn(c, s) for s in selected), default=0.0)
            val = lam * c.base_score - (1.0 - lam) * redundancy
            if val > best_val:
                best_val = val
                best_idx = i
        selected.append(pool.pop(best_idx))
    return selected

if __name__ == "__main__":
    weights = {
        "entity_overlap": 0.25,
        "serp_overlap": 0.25,
        "embedding_similarity": 0.20,
        "intent_compatibility": 0.15,
        "perspective_alignment": 0.15,
    }
    # Example usage is intentionally omitted — this file is meant to be imported.
