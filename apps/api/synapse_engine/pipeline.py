"""Synapse Engine — Pipeline Orchestrator (M0-M9).

Thin orchestrator that calls modular functions.
All logic lives in the individual module files.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models import SchemaValidator, load_base_pack
from .normalization import normalize_phrase
from .utils import stable_qid
from .intent import infer_intent_rule_based, intent_x_position
from .perspective import infer_perspective_rule_based
from .candidates import generate_candidates
from .scoring import build_tfidf_embeddings, score_candidates, mmr_select
from .clustering import cluster_nodes
from .synapses import build_edges_seed_to_nodes, build_intra_cluster_edges
from .visual import assign_positions, compute_cluster_centroids, legend, now_iso


def run_pipeline(
    seed_phrase: str,
    language: str = "sv",
    market: str = "SE",
    spec_root: Path | None = None,
    target: int | None = None,
    runtime: Optional[Any] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run the end-to-end pipeline and return (graph_artifact, related_queries)."""
    if spec_root is None:
        spec_root = Path(__file__).resolve().parent.parent / "spec"

    pack = load_base_pack(spec_root)

    # M0: normalize seed
    nseed = normalize_phrase(seed_phrase, pack.normalization_model)

    # Optional: seed SERP snapshot (ToS-safe via DataForSEO)
    serp_calls_used = 0
    seed_serp_snapshot: Optional[Dict[str, Any]] = None
    seed_serp_top_urls: List[str] = []

    if runtime is not None and runtime.providers.dataforseo is not None and runtime.budget.serp_calls_max > 0:
        try:
            from .serp import fetch_seed_serp

            seed_serp = fetch_seed_serp(
                runtime.providers.dataforseo,
                keyword=nseed.canonical,
                location_name=runtime.location_name,
                location_code=runtime.location_code,
                language_code=runtime.language_code,
                depth=runtime.budget.serp_depth,
            )
            serp_calls_used += 1
            seed_serp_snapshot = seed_serp.to_dict()
            seed_serp_top_urls = seed_serp.top_urls
        except Exception:
            seed_serp_snapshot = None
            seed_serp_top_urls = []

    seed_serp_present = bool(seed_serp_top_urls)

    # M4+M5 (rule pass): seed intent + perspective
    seed_int = infer_intent_rule_based(nseed.canonical, pack.intent_model, serp_present=seed_serp_present)
    seed_per = infer_perspective_rule_based(nseed.canonical, pack.perspective_model, serp_present=seed_serp_present)

    seed_id = stable_qid(nseed.canonical, language, market)
    seed = {
        "id": seed_id,
        "phrase": nseed.display,
        "intent": seed_int.intent,
        "perspective": seed_per.perspective,
    }

    # M3: candidate pool
    pool_target = 300
    if runtime is not None:
        pool_target = int(runtime.budget.candidate_pool_target)
    candidate_pool = generate_candidates(
        nseed.canonical,
        language,
        market,
        target_pool=pool_target,
        runtime=runtime,
        seed_serp_snapshot=seed_serp_snapshot,
    )

    def cap_for_provenance(prov: str) -> float:
        return 0.55 if prov == "llm_inferred" else 0.90

    candidates: List[Dict[str, Any]] = []
    for c in candidate_pool:
        nc = normalize_phrase(c.phrase, pack.normalization_model)
        prov = c.provenance
        ext_ev = prov != "llm_inferred"
        iid = infer_intent_rule_based(nc.canonical, pack.intent_model, serp_present=ext_ev)
        pid = infer_perspective_rule_based(nc.canonical, pack.perspective_model, serp_present=ext_ev)
        cid = stable_qid(nc.canonical, language, market)
        conf = min(iid.confidence, pid.confidence, cap_for_provenance(prov))
        candidates.append({
            "id": cid,
            "phrase": nc.canonical,
            "display": nc.display,
            "provenance": prov,
            "intent": iid.intent,
            "perspective": pid.perspective,
            "confidence": conf,
            "metrics": c.metrics or {},
            "serp_overlap": 0.0,
            "serp_shared_urls": [],
        })

    # Optional: SERP refinement
    if (
        runtime is not None
        and runtime.providers.dataforseo is not None
        and seed_serp_present
        and runtime.budget.serp_refine_top_n > 0
        and serp_calls_used < runtime.budget.serp_calls_max
    ):
        try:
            from .serp import fetch_seed_serp, serp_overlap as _serp_overlap

            scored0, _, _ = score_candidates(
                seed_phrase=nseed.canonical,
                seed_intent=seed["intent"],
                seed_perspective=seed["perspective"],
                candidates=candidates,
                language=language,
                market=market,
                scoring_model=pack.scoring_model,
                perspective_model=pack.perspective_model,
            )

            remaining = int(runtime.budget.serp_calls_max) - int(serp_calls_used)
            refine_n = max(0, min(int(runtime.budget.serp_refine_top_n), remaining))
            refine_ids = [sc.id for sc in sorted(scored0, key=lambda s: s.relevance_score, reverse=True)[:refine_n]]

            id_to_phrase = {c["id"]: c["phrase"] for c in candidates}
            id_to_idx = {c["id"]: i for i, c in enumerate(candidates)}

            for cid in refine_ids:
                if serp_calls_used >= runtime.budget.serp_calls_max:
                    break
                phrase = id_to_phrase.get(cid)
                if not phrase:
                    continue
                try:
                    cand_serp = fetch_seed_serp(
                        runtime.providers.dataforseo,
                        keyword=phrase,
                        location_name=runtime.location_name,
                        location_code=runtime.location_code,
                        language_code=runtime.language_code,
                        depth=runtime.budget.serp_depth,
                    )
                    serp_calls_used += 1

                    ov = _serp_overlap(seed_serp_top_urls, cand_serp.top_urls)
                    shared = [u for u in seed_serp_top_urls if u in set(cand_serp.top_urls)][:6]

                    idx = id_to_idx.get(cid)
                    if idx is None:
                        continue
                    candidates[idx]["serp_overlap"] = float(ov)
                    candidates[idx]["serp_shared_urls"] = shared
                except Exception:
                    continue
        except ImportError:
            pass

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

    # Map metrics + serp evidence onto selected nodes
    cand_by_id = {c["id"]: c for c in candidates}

    # Build node dicts
    nodes: List[Dict[str, Any]] = []
    for sc in selected_scored:
        meta = cand_by_id.get(sc.id, {})
        m = meta.get("metrics") or {}
        vol = m.get("search_volume")
        try:
            vol_f = float(vol) if vol is not None else None
        except Exception:
            vol_f = None

        size = float(6 + 18 * sc.relevance_score)
        if vol_f is not None and vol_f > 0:
            size = float(size + 4.0 * min(1.0, math.log10(1.0 + vol_f) / 5.0))
        nodes.append({
            "id": sc.id,
            "phrase": sc.phrase,
            "intent": sc.intent,
            "perspective": sc.perspective,
            "confidence": float(sc.confidence),
            "provenance": sc.provenance,
            "relevance_score": float(sc.relevance_score),
            "features": sc.features,
            "size": float(size),
            "search_volume": vol_f,
            "source_metrics": m,
            "serp_shared_urls": meta.get("serp_shared_urls", []),
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

    # Build cluster dicts
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
    edges = build_edges_seed_to_nodes(seed_xy, nodes_xy, evidence_cap=0.90)
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
                "search_volume": n.get("search_volume"),
                "source_metrics": n.get("source_metrics", {}),
                "serp_shared_urls": n.get("serp_shared_urls", []),
            },
        })

    # Validate against schemas
    sv = SchemaValidator(spec_root / "03_schemas")
    sv.validate(graph, "GraphArtifact.schema.json")
    sv.validate(related, "RelatedQueriesOutput.schema.json")

    return graph, related
