from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import re



@dataclass
class IntentLabel:
    intent: str
    confidence: float
    evidence_used: List[str]
    secondary: List[str]


def _signals_for_intents(intent_model: Dict[str, Any]) -> Dict[str, List[str]]:
    return {
        iid: (rule.get("signals", []) or [])
        for iid, rule in (intent_model.get("intent_model", {}).get("modifier_rules", {}) or {}).items()
    }


def infer_intent_rule_based(phrase: str, intent_model: Dict[str, Any], serp_present: bool = False) -> IntentLabel:
    """Cheap phase-1 intent inference using modifier signals.

    Returns an intent label + up to 2 secondary intents.

    If serp_present is False, caps confidence to 0.55 as per pack guidance.
    """
    signals = _signals_for_intents(intent_model)
    p = phrase.lower()

    # Heuristic: offer-like phrasing with a large amount often behaves as transactional.
    # Example: "privatlån upp till 800 000" (provider offer)
    if ("upp till" in p or "ränta från" in p or "ansök" in p or "ansok" in p) and re.search(r"\d{3,}", p):
        base_intent = "transactional"
        conf = 0.70 if serp_present else 0.55
        ev = ["heuristic_offer"]
        secondary = ["commercial"]
        if not serp_present:
            ev.append("no_serp")
        return IntentLabel(intent=base_intent, confidence=min(conf, 0.55) if not serp_present else conf, evidence_used=ev, secondary=secondary)

    matches: List[Tuple[str, int, List[str]]] = []
    for iid, sigs in signals.items():
        hit = [s for s in sigs if s in p]
        if hit:
            matches.append((iid, len(hit), hit))

    if not matches:
        # Default guess: informational
        base_intent = "informational"
        conf = 0.45
        ev = ["no_modifier_match"]
        secondary: List[str] = []
    else:
        matches.sort(key=lambda x: x[1], reverse=True)
        base_intent = matches[0][0]
        # crude confidence: more hits => higher, but still capped without SERP
        conf = min(0.35 + 0.12 * matches[0][1], 0.75)
        ev = ["modifier_match"]
        secondary = [m[0] for m in matches[1:3]]

    if not serp_present:
        conf = min(conf, 0.55)
        ev = list(set(ev + ["no_serp"]))

    return IntentLabel(intent=base_intent, confidence=conf, evidence_used=ev, secondary=secondary)


def intent_x_position(intent: str, intent_model: Dict[str, Any]) -> float:
    intents = intent_model.get("intent_model", {}).get("intents", []) or []
    for it in intents:
        if it.get("id") == intent:
            return float(it.get("x_position", 0.5))
    return 0.5


def intent_distance(a: str, b: str, scoring_model: Dict[str, Any]) -> float:
    mat = scoring_model.get("scoring_model", {}).get("intent_distance_matrix", {}) or {}
    if a not in mat or b not in mat:
        # conservative
        return 0.5
    order = ["informational","howto","commercial","transactional","navigational","local","freshness"]
    try:
        bi = order.index(b)
    except ValueError:
        return 0.5
    row = mat[a]
    if bi >= len(row):
        return 0.5
    return float(row[bi])


def intent_compatibility(seed_intent: str, cand_intent: str, scoring_model: Dict[str, Any]) -> float:
    d = intent_distance(seed_intent, cand_intent, scoring_model)
    return max(0.0, min(1.0, 1.0 - d))
