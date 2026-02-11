from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class PerspectiveLabel:
    perspective: str
    confidence: float
    evidence_used: List[str]


def infer_perspective_rule_based(phrase: str, perspective_model: Dict[str, Any], serp_present: bool = False) -> PerspectiveLabel:
    signals = perspective_model.get("perspective_model", {}).get("signals", {}) or {}
    p = phrase.lower()

    matches: List[Tuple[str, int, List[str]]] = []
    for pid, sig in signals.items():
        phrases = sig.get("phrases", []) or []
        hit = [s for s in phrases if s in p]
        if hit:
            matches.append((pid, len(hit), hit))

    if not matches:
        base = "neutral"
        conf = 0.45
        ev = ["no_signal_match"]
    else:
        matches.sort(key=lambda x: x[1], reverse=True)
        base = matches[0][0]
        conf = min(0.35 + 0.12 * matches[0][1], 0.75)
        ev = ["signal_match"]

    if not serp_present:
        conf = min(conf, 0.55)
        ev = list(set(ev + ["no_serp"]))

    return PerspectiveLabel(perspective=base, confidence=conf, evidence_used=ev)


def perspective_y_position(perspective: str, perspective_model: Dict[str, Any]) -> float:
    arr = perspective_model.get("perspective_model", {}).get("perspectives", []) or []
    for p in arr:
        if p.get("id") == perspective:
            return float(p.get("y_position", 0.5))
    return 0.5


def perspective_distance(a: str, b: str, perspective_model: Dict[str, Any]) -> float:
    mat = perspective_model.get("perspective_model", {}).get("distance_matrix", {}) or {}
    if a not in mat or b not in mat:
        return 0.5
    order = ["provider","seeker","advisor","regulator","neutral"]
    try:
        bi = order.index(b)
    except ValueError:
        return 0.5
    row = mat[a]
    if bi >= len(row):
        return 0.5
    return float(row[bi])


def perspective_alignment(seed_p: str, cand_p: str, perspective_model: Dict[str, Any]) -> float:
    d = perspective_distance(seed_p, cand_p, perspective_model)
    return max(0.0, min(1.0, 1.0 - d))
