from __future__ import annotations

import datetime as dt
import hashlib
from typing import Any, Dict, List, Tuple

from .intent import intent_x_position, intent_distance
from .perspective import perspective_y_position, perspective_distance


def _jitter(seed: str, scale: float = 0.04) -> Tuple[float, float]:
    h = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    # use first 8 hex digits for reproducible random
    a = int(h[:8], 16) / 0xffffffff
    b = int(h[8:16], 16) / 0xffffffff
    dx = (a - 0.5) * 2 * scale
    dy = (b - 0.5) * 2 * scale
    return dx, dy


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def compute_anchor_distance(
    seed_intent: str,
    seed_perspective: str,
    node_intent: str,
    node_perspective: str,
    scoring_model: Dict[str, Any],
    perspective_model: Dict[str, Any],
) -> float:
    # Simple proxy: average intent + perspective distance
    dI = intent_distance(seed_intent, node_intent, scoring_model)
    dP = perspective_distance(seed_perspective, node_perspective, perspective_model)
    return 0.5 * dI + 0.5 * dP


def assign_positions(
    seed: Dict[str, Any],
    nodes: List[Dict[str, Any]],
    intent_model: Dict[str, Any],
    perspective_model: Dict[str, Any],
    scoring_model: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    # Seed position
    seed_x = intent_x_position(seed["intent"], intent_model)
    seed_y = perspective_y_position(seed["perspective"], perspective_model)
    seed_out = dict(seed)
    seed_out["x"] = clamp01(seed_x)
    seed_out["y"] = clamp01(seed_y)

    warn = float(scoring_model.get("scoring_model", {}).get("thresholds", {}).get("warn_distance_anchor", 0.35))

    out_nodes: List[Dict[str, Any]] = []
    for n in nodes:
        base_x = intent_x_position(n["intent"], intent_model)
        base_y = perspective_y_position(n["perspective"], perspective_model)
        dx, dy = _jitter(n["id"])
        x = clamp01(base_x + dx)
        y = clamp01(base_y + dy)

        flags = list(n.get("flags", []) or [])
        dist = compute_anchor_distance(seed_out["intent"], seed_out["perspective"], n["intent"], n["perspective"], scoring_model, perspective_model)
        if dist >= warn:
            if "⚠ wrong_cluster_for_anchor" not in flags:
                flags.append("⚠ wrong_cluster_for_anchor")

        nn = dict(n)
        nn["x"], nn["y"] = x, y
        nn["flags"] = flags

        out_nodes.append(nn)

    return seed_out, out_nodes


def compute_cluster_centroids(
    clusters: List[Dict[str, Any]],
    nodes: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    by_id = {n["id"]: n for n in nodes}
    out = []
    for c in clusters:
        xs = []
        ys = []
        for nid in c.get("node_ids", []):
            n = by_id.get(nid)
            if not n:
                continue
            xs.append(float(n["x"]))
            ys.append(float(n["y"]))
        if xs and ys:
            centroid = {"x": sum(xs) / len(xs), "y": sum(ys) / len(ys)}
        else:
            centroid = {"x": 0.5, "y": 0.5}
        cc = dict(c)
        cc["centroid"] = centroid
        out.append(cc)
    return out


def legend() -> Dict[str, Any]:
    return {
        "intent_axis": "informational -> transactional",
        "perspective_axis": "seeker -> provider",
        "strength_buckets": [
            {"min": 0.0, "max": 0.49, "label": "weak"},
            {"min": 0.5, "max": 0.69, "label": "medium"},
            {"min": 0.7, "max": 1.0, "label": "strong"},
        ],
    }


def now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
