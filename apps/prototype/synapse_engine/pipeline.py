from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from .config import load_base_pack, SpecPack
from .normalization import normalize_phrase
from .utils import stable_qid
from .intent import infer_intent_rule_based
from .perspective import infer_perspective_rule_based
from .candidates import generate_candidates
from .scoring import score_candidates, mmr_select, build_tfidf_embeddings
from .clustering import cluster_nodes
from .synapses import build_edges_seed_to_nodes, build_intra_cluster_edges
from .visual import assign_positions, compute_cluster_centroids, legend, now_iso
from .validators import SchemaValidator


def run_pipeline(
    seed_phrase: str,
    language: str = "sv",
    market: str = "SE",
    spec_root: Path | None = None,
    target: int | None = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run the end-to-end pipeline and return (graph_artifact, related_queries)."""
    if spec_root is None:
        spec_root = Path(__file__).resolve().parent.parent / "spec"

    pack = load_base_pack(spec_root)

    # M0: normalize seed
    nseed = normalize_phrase(seed_phrase, pack.normalization_model)

    # M4+M5 (rule pass): seed intent + perspective
    seed_int = infer_intent_rule_based(nseed.canonical, pack.intent_model, serp_present=False)
    seed_per = infer_perspective_rule_based(nseed.canonical, pack.perspective_model, serp_present=False)

    seed_id = stable_qid(nseed.canonical, language, market)
    seed = {
        "id": seed_id,
        "phrase": nseed.display,
        "intent": seed_int.intent,
        "perspective": seed_per.perspective,
    }

    # M3: candidate pool
    candidate_pool = generate_candidates(nseed.canonical, language, market, target_pool=300)

    candidates: List[Dict[str, Any]] = []
    for c in candidate_pool:
        nc = normalize_phrase(c.phrase, pack.normalization_model)
        iid = infer_intent_rule_based(nc.canonical, pack.intent_model, serp_present=False)
        pid = infer_perspective_rule_based(nc.canonical, pack.perspective_model, serp_present=False)
        cid = stable_qid(nc.canonical, language, market)
        conf = min(iid.confidence, pid.confidence, 0.55)
        candidates.append({
            "id": cid,
            "phrase": nc.canonical,
            "display": nc.display,
            "provenance": c.provenance,
            "intent": iid.intent,
            "perspective": pid.perspective,
            "confidence": conf,
        })

    # M7: scoring
    scored, X_all, _sims = score_candidates(
        seed_phrase=nseed.canonical,
        seed_intent=seed["intent"],
        seed_perspective=seed["perspective"],
        candidates=candidates,
        language=language,
        market=market,
        scoring_model=pack.scoring_model,
        perspective_model=pack.perspective_model,
    )

    sel_spec = pack.scoring_model.get("scoring_model", {}).get("mmr_selection", {})
    k = int(target or sel_spec.get("target", 50))
    lam = float(sel_spec.get("mmr_lambda", 0.75))
    constraints = dict(sel_spec.get("constraints", {}) or {})

    selected_scored = mmr_select(scored, X_all, k=k, mmr_lambda=lam, constraints=constraints)

    # Build node dicts
    nodes: List[Dict[str, Any]] = []
    for sc in selected_scored:
        nodes.append({
            "id": sc.id,
            "phrase": sc.phrase,
            "intent": sc.intent,
            "perspective": sc.perspective,
            "confidence": float(min(0.55, sc.confidence)),
            "provenance": sc.provenance,
            "relevance_score": float(sc.relevance_score),
            "features": sc.features,
            "size": float(6 + 18 * sc.relevance_score),
            "flags": [],
        })

    # M8: clustering
    node_ids = [n["id"] for n in nodes]
    node_phrases = [n["phrase"] for n in nodes]
    node_intents = [n["intent"] for n in nodes]
    node_persps = [n["perspective"] for n in nodes]

    X_nodes = build_tfidf_embeddings(node_phrases)

    cluster_ids, clusters_obj = cluster_nodes(
        node_ids=node_ids,
        node_phrases=node_phrases,
        node_intents=node_intents,
        node_perspectives=node_persps,
        X_nodes=X_nodes,
        language=language,
        market=market,
        scoring_model=pack.scoring_model,
        perspective_model=pack.perspective_model,
        clustering_model=pack.clustering_model,
    )

    # Attach cluster IDs
    for n, cid in zip(nodes, cluster_ids):
        n["cluster_id"] = cid

    # Build cluster dicts (centroids assigned after positions)
    clusters: List[Dict[str, Any]] = []
    for c in clusters_obj:
        clusters.append({
            "id": c.id,
            "label": c.label,
            "color": c.color,
            "node_ids": c.node_ids,
            "dominant_intent": c.dominant_intent,
            "dominant_perspective": c.dominant_perspective,
            "hub_entities": c.hub_entities,
            "centroid": {"x": 0.5, "y": 0.5},
        })

    # M9: assign positions and anchor flags
    seed_xy, nodes_xy = assign_positions(seed, nodes, pack.intent_model, pack.perspective_model, pack.scoring_model)
    clusters_xy = compute_cluster_centroids(clusters, nodes_xy)

    # M6: synapses
    edges = build_edges_seed_to_nodes(seed_xy, nodes_xy, evidence_cap=0.55)
    edges += build_intra_cluster_edges(nodes_xy, min_strength=float(pack.scoring_model.get("scoring_model", {}).get("thresholds", {}).get("edge_display_min_strength", 0.40)))

    # GraphArtifact
    graph = {
        "meta": {
            "version": "1.0.0",
            "generated_at": now_iso(),
            "language": language,
            "market": market,
        },
        "seed": {
            "id": seed_xy["id"],
            "phrase": seed_xy["phrase"],
            "x": float(seed_xy["x"]),
            "y": float(seed_xy["y"]),
            "intent": seed_xy["intent"],
            "perspective": seed_xy["perspective"],
        },
        "nodes": [
            {
                "id": n["id"],
                "phrase": n["phrase"],
                "x": float(n["x"]),
                "y": float(n["y"]),
                "cluster_id": n.get("cluster_id", "?"),
                "intent": n["intent"],
                "perspective": n["perspective"],
                "confidence": float(n["confidence"]),
                "provenance": n["provenance"],
                "size": float(n["size"]),
                "flags": n.get("flags", []),
            }
            for n in nodes_xy
        ],
        "edges": edges,
        "clusters": clusters_xy,
        "legend": legend(),
        "warnings": [],
    }

    # RelatedQueriesOutput
    related = {
        "meta": {
            "generated_at": now_iso(),
            "language": language,
            "market": market,
            "target_count": k,
            "candidate_pool_size": len(candidates),
        },
        "seed": {
            "phrase": seed_xy["phrase"],
            "id": seed_xy["id"],
            "dominant_intent": seed_xy["intent"],
            "perspective": seed_xy["perspective"],
        },
        "selected": [],
    }

    # map from seed->node synapse for convenience
    syn_by_to = {e["to"]: e["synapse_card"] for e in edges if e["from"] == seed_xy["id"]}

    for rank, n in enumerate(sorted(nodes_xy, key=lambda x: x.get("relevance_score", 0.0), reverse=True), start=1):
        related["selected"].append({
            "id": n["id"],
            "phrase": n["phrase"],
            "rank": rank,
            "provenance": n["provenance"],
            "relevance_score": float(n.get("relevance_score", 0.0)),
            "intent": n["intent"],
            "perspective": n["perspective"],
            "cluster_id": n.get("cluster_id"),
            "synapse_to_seed": syn_by_to.get(n["id"]),
            "metrics": {
                "features": n.get("features", {}),
            },
        })

    # Validate against schemas
    sv = SchemaValidator(spec_root / "03_schemas")
    sv.validate(graph, "GraphArtifact.schema.json")
    sv.validate(related, "RelatedQueriesOutput.schema.json")

    return graph, related
