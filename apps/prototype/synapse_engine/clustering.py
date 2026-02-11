from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

from .entities import extract_entities_simple, entity_ids
from .intent import intent_distance
from .perspective import perspective_distance
from .utils import jaccard


PALETTE = [
    "#e53e3e",  # red
    "#ed8936",  # orange
    "#4299e1",  # blue
    "#68d391",  # green
    "#9f7aea",  # purple
    "#ecc94b",  # yellow
    "#38b2ac",  # teal
    "#f56565",  # coral
]


@dataclass
class Cluster:
    id: str
    label: str
    color: str
    node_ids: List[str]
    dominant_intent: str
    dominant_perspective: str
    hub_entities: List[str]


def _auto_k(n: int) -> int:
    # typical 3-8 clusters for 50 nodes
    return max(3, min(8, int(round(n / 10)) or 3))


def build_distance_matrix(
    node_phrases: List[str],
    node_intents: List[str],
    node_perspectives: List[str],
    X: np.ndarray,
    language: str,
    market: str,
    scoring_model: Dict[str, Any],
    perspective_model: Dict[str, Any],
    clustering_model: Dict[str, Any],
) -> np.ndarray:
    dims = clustering_model.get("clustering_model", {}).get("distance_dimensions", {})
    w_sem = float(dims.get("semantic_embedding", 0.30))
    w_int = float(dims.get("intent_distance", 0.25))
    w_per = float(dims.get("perspective_distance", 0.25))
    w_ent = float(dims.get("entity_overlap", 0.20))

    # cosine similarity between TF-IDF vectors for nodes (X includes seed at 0)
    # caller should pass X_nodes already aligned with node_phrases
    sim = cosine_similarity(X)
    n = sim.shape[0]

    # entity sets
    ents = [set(entity_ids(extract_entities_simple(p, language, market))) for p in node_phrases]

    D = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            d_sem = 1.0 - float(sim[i, j])
            d_int = intent_distance(node_intents[i], node_intents[j], scoring_model)
            d_per = perspective_distance(node_perspectives[i], node_perspectives[j], perspective_model)
            d_ent = 1.0 - jaccard(ents[i], ents[j])

            d = w_sem * d_sem + w_int * d_int + w_per * d_per + w_ent * d_ent
            D[i, j] = D[j, i] = float(d)

    # normalize to 0..1
    maxd = float(D.max()) if D.size else 1.0
    if maxd > 0:
        D = D / maxd
    return D


def _dominant(items: List[str]) -> str:
    counts: Dict[str, int] = {}
    for x in items:
        counts[x] = counts.get(x, 0) + 1
    return max(counts.items(), key=lambda kv: kv[1])[0] if counts else "informational"


def _label_cluster(d_intent: str, d_persp: str) -> str:
    # Minimal, language-specific label mapping (demo). Replace with M8 LLM labeler.
    if d_intent == "transactional" and d_persp == "provider":
        return "Ansöka / erbjudande"
    if d_intent == "commercial" and d_persp in {"advisor", "neutral"}:
        return "Jämföra / utvärdera"
    if d_persp == "regulator" or "regler" in d_intent:
        return "Regelverk"
    if d_persp == "seeker" and d_intent in {"howto", "informational"}:
        return "Planera / hantera"
    return f"{d_intent} · {d_persp}"


def cluster_nodes(
    node_ids: List[str],
    node_phrases: List[str],
    node_intents: List[str],
    node_perspectives: List[str],
    X_nodes: np.ndarray,
    language: str,
    market: str,
    scoring_model: Dict[str, Any],
    perspective_model: Dict[str, Any],
    clustering_model: Dict[str, Any],
) -> Tuple[List[str], List[Cluster]]:
    n = len(node_ids)
    spec = clustering_model.get("clustering_model", {})
    k_spec = spec.get("target_clusters", "auto")
    k = _auto_k(n) if k_spec == "auto" else int(k_spec)

    D = build_distance_matrix(
        node_phrases=node_phrases,
        node_intents=node_intents,
        node_perspectives=node_perspectives,
        X=X_nodes,
        language=language,
        market=market,
        scoring_model=scoring_model,
        perspective_model=perspective_model,
        clustering_model=clustering_model,
    )

    model = AgglomerativeClustering(
        n_clusters=k,
        metric="precomputed",
        linkage="average",
    )
    labels = model.fit_predict(D)

    # Map numeric labels to A,B,C...
    uniq = sorted(set(labels.tolist()))
    id_map = {lab: chr(ord("A") + i) for i, lab in enumerate(uniq)}
    cluster_ids = [id_map[x] for x in labels]

    clusters: List[Cluster] = []
    for cid in sorted(set(cluster_ids)):
        idxs = [i for i, c in enumerate(cluster_ids) if c == cid]
        intents = [node_intents[i] for i in idxs]
        persps = [node_perspectives[i] for i in idxs]
        d_int = _dominant(intents)
        d_per = _dominant(persps)

        # hub entities: most common token-ish entities
        ent_counts: Dict[str, int] = {}
        for i in idxs:
            ents = extract_entities_simple(node_phrases[i], language, market)
            for e in ents:
                if e.type in {"topic", "brand", "product", "regulation", "metric"}:
                    ent_counts[e.canonical] = ent_counts.get(e.canonical, 0) + 1
        hub = [k for k, _ in sorted(ent_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]]

        clusters.append(
            Cluster(
                id=cid,
                label=f"{cid}: {_label_cluster(d_int, d_per)}",
                color=PALETTE[(ord(cid) - ord("A")) % len(PALETTE)],
                node_ids=[node_ids[i] for i in idxs],
                dominant_intent=d_int,
                dominant_perspective=d_per,
                hub_entities=hub,
            )
        )

    return cluster_ids, clusters
