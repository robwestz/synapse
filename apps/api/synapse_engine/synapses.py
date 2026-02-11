from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

from .intent import intent_distance
from .perspective import perspective_distance


def _choose_types(
    from_intent: str,
    to_intent: str,
    from_persp: str,
    to_persp: str,
    phrase: str,
    features: Dict[str, float],
) -> List[str]:
    types: List[str] = []
    if features.get("serp_overlap", 0.0) >= 0.15:
        types.append("serp_overlap")
    if features.get("entity_overlap", 0.0) >= 0.35:
        types.append("shared_entity")
    # comparative
    if " vs " in f" {phrase.lower()} ":
        types.append("comparative")
    # heuristic task chain
    if any(x in phrase.lower() for x in ["hur", "räkna", "beräkna", "steg för steg"]):
        types.append("task_chain")

    if from_intent != to_intent:
        types.append("intent_shift")
    if from_persp != to_persp:
        types.append("perspective_shift")

    # bridge when both shift significantly
    if (from_intent != to_intent) and (from_persp != to_persp):
        types.append("bridge")

    # keep 1..3 most informative
    # priority order
    priority = ["serp_overlap", "shared_entity", "facet_transform", "task_chain", "comparative", "problem_solution", "intent_shift", "perspective_shift", "bridge"]
    uniq = []
    for t in priority:
        if t in types and t not in uniq:
            uniq.append(t)
    return uniq[:3] if uniq else ["shared_entity"]


def _bridge_statement(from_phrase: str, to_phrase: str, types: List[str], from_intent: str, to_intent: str, from_persp: str, to_persp: str) -> str:
    # Non-SEO friendly, 1 sentence.
    if "comparative" in types:
        return "Detta är en jämförelsevariant av samma ämne, där användaren vill välja mellan alternativ."
    if "task_chain" in types and from_intent in {"transactional", "commercial"}:
        return "Detta är ett närliggande steg i beslutsprocessen som ofta kommer före eller efter huvudfrågan."
    if "bridge" in types:
        return "Det delar grundämnet men handlar om en annan uppgift/roll, vilket gör kopplingen svagare för ankartext."
    if "intent_shift" in types:
        return "Det handlar om samma ämne men med en annan typ av mål (t.ex. lära sig vs agera)."
    return "Direkt relaterat inom samma ämne och tolkning."


def build_synapse_card(
    from_id: str,
    to_id: str,
    from_phrase: str,
    to_phrase: str,
    from_intent: str,
    to_intent: str,
    from_perspective: str,
    to_perspective: str,
    strength: float,
    confidence: float,
    features: Dict[str, float],
    serp_shared_urls: Optional[List[str]] = None,
    evidence_sources: List[str] | None = None,
) -> Dict[str, Any]:
    types = _choose_types(from_intent, to_intent, from_perspective, to_perspective, to_phrase, features)

    card: Dict[str, Any] = {
        "from_id": from_id,
        "to_id": to_id,
        "strength": float(max(0.0, min(1.0, strength))),
        "types": types,
        "direction": "bidirectional",
        "intent_shift": f"{from_intent}->{to_intent}" if from_intent != to_intent else "",
        "perspective_shift": f"{from_perspective}->{to_perspective}" if from_perspective != to_perspective else "",
        "confidence": float(max(0.0, min(1.0, confidence))),
        "bridge_statement": _bridge_statement(from_phrase, to_phrase, types, from_intent, to_intent, from_perspective, to_perspective),
        "evidence": [],
    }

    # Evidence entries (keep small)
    ev = []
    ev.append({
        "source": "embeddings",
        "kind": "tfidf_cosine",
        "summary": f"Textlikhet (proxy) = {features.get('embedding_similarity', 0.0):.2f}",
        "confidence": float(min(0.90, confidence)),
        "value": features.get("embedding_similarity", 0.0),
    })
    ev.append({
        "source": "llm_inferred",
        "kind": "entity_overlap",
        "summary": f"Entitetsöverlapp (proxy) = {features.get('entity_overlap', 0.0):.2f}",
        "confidence": float(min(0.90, confidence)),
        "value": features.get("entity_overlap", 0.0),
    })

    if features.get("serp_overlap", 0.0) > 0.0:
        shared = serp_shared_urls or []
        ev.append({
            "source": "serp_top_urls",
            "kind": "serp_overlap",
            "summary": f"SERP-överlapp (Jaccard) = {features.get('serp_overlap', 0.0):.2f} (delade URL:er: {len(shared)})",
            "confidence": float(min(0.90, confidence)),
            "value": {
                "overlap": float(features.get("serp_overlap", 0.0)),
                "shared_urls_sample": shared,
            },
        })

    card["evidence"] = ev
    return card


def build_edges_seed_to_nodes(
    seed: Dict[str, Any],
    nodes: List[Dict[str, Any]],
    evidence_cap: float = 0.55,
) -> List[Dict[str, Any]]:
    edges: List[Dict[str, Any]] = []
    for n in nodes:
        strength = float(n.get("relevance_score", 0.0))
        conf = float(min(evidence_cap, n.get("confidence", evidence_cap)))
        card = build_synapse_card(
            from_id=seed["id"],
            to_id=n["id"],
            from_phrase=seed["phrase"],
            to_phrase=n["phrase"],
            from_intent=seed["intent"],
            to_intent=n["intent"],
            from_perspective=seed["perspective"],
            to_perspective=n["perspective"],
            strength=strength,
            confidence=conf,
            features=n.get("features", {}),
            serp_shared_urls=n.get("serp_shared_urls") or None,
        )
        edges.append({
            "from": seed["id"],
            "to": n["id"],
            "strength": float(max(0.0, min(1.0, strength))),
            "types": card["types"],
            "synapse_card": card,
        })
    return edges


def build_intra_cluster_edges(
    nodes: List[Dict[str, Any]],
    min_strength: float = 0.40,
) -> List[Dict[str, Any]]:
    """Lightweight intra-cluster edges: connect each node to its nearest neighbor in same cluster."""
    # Group by cluster
    by_cluster: Dict[str, List[Dict[str, Any]]] = {}
    for n in nodes:
        by_cluster.setdefault(n.get("cluster_id", "?"), []).append(n)

    edges: List[Dict[str, Any]] = []

    for cid, arr in by_cluster.items():
        if len(arr) < 2:
            continue
        # For each node, connect to the node with max embedding similarity in cluster
        for a in arr:
            best = None
            best_sim = -1.0
            for b in arr:
                if a["id"] == b["id"]:
                    continue
                sim = float(min(a.get("features", {}).get("embedding_similarity", 0.0), b.get("features", {}).get("embedding_similarity", 0.0)))
                if sim > best_sim:
                    best_sim = sim
                    best = b
            if best is None:
                continue
            strength = float(max(0.0, min(1.0, 0.5 * (a.get("relevance_score", 0.0) + best.get("relevance_score", 0.0)))))
            if strength < min_strength:
                continue

            card = build_synapse_card(
                from_id=a["id"],
                to_id=best["id"],
                from_phrase=a["phrase"],
                to_phrase=best["phrase"],
                from_intent=a["intent"],
                to_intent=best["intent"],
                from_perspective=a["perspective"],
                to_perspective=best["perspective"],
                strength=strength,
                confidence=float(min(0.90, a.get("confidence", 0.55), best.get("confidence", 0.55))),
                features={
                    "embedding_similarity": best_sim,
                    "entity_overlap": 0.0,
                    "intent_compatibility": 1.0,
                    "perspective_alignment": 1.0,
                    "serp_overlap": 0.0,
                },
            )
            edges.append({
                "from": a["id"],
                "to": best["id"],
                "strength": float(max(0.0, min(1.0, strength))),
                "types": card["types"],
                "synapse_card": card,
            })

    # Dedup undirected edges
    seen = set()
    uniq = []
    for e in edges:
        key = tuple(sorted([e["from"], e["to"]]))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(e)
    return uniq
