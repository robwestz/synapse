from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List

from .utils import stable_eid, tokenize_simple


ACTION_WORDS = {
    "ansok","ansök","ansokan","ansökan","registrera","kop","köp","boka","bestall","beställ","teckna","prenumerera",
    "jamfor","jämför","jamforelse","jämförelse","betala","amortera","rakna","räkna","berakna","beräkna",
}

ATTRIBUTE_WORDS = {
    "bast","bäst","basta","bästa","billigast","snabbt","lag","låg","utan",
}

REGULATION_WORDS = {
    "lag","lagen","regler","krav","forordning","förordning","tillsyn","konsumentskydd","villkor",
    "konsumentkreditlagen",
}


@dataclass
class Entity:
    id: str
    surface: str
    canonical: str
    type: str
    kg_id: str | None
    role: str
    confidence: float


def extract_entities_simple(phrase: str, language: str, market: str) -> List[Entity]:
    """Heuristic entity resolver.

    Replace with KG lookup / NER for production.
    """
    tokens = tokenize_simple(phrase)

    entities: List[Entity] = []
    for t in tokens:
        # Amount
        if re.fullmatch(r"\d+", t):
            canonical = t
            etype = "amount"
            role = "modifier"
            conf = 0.55
        elif t in ACTION_WORDS:
            canonical = t
            etype = "action"
            role = "action"
            conf = 0.55
        elif t in REGULATION_WORDS:
            canonical = t
            etype = "regulation"
            role = "modifier"
            conf = 0.55
        elif t in ATTRIBUTE_WORDS:
            canonical = t
            etype = "attribute"
            role = "modifier"
            conf = 0.50
        else:
            canonical = t
            etype = "topic"
            role = "subject"
            conf = 0.50

        eid = stable_eid(etype, canonical)
        entities.append(Entity(id=eid, surface=t, canonical=canonical, type=etype, kg_id=None, role=role, confidence=conf))

    # simple de-dup by id
    uniq: Dict[str, Entity] = {}
    for e in entities:
        if e.id not in uniq or e.confidence > uniq[e.id].confidence:
            uniq[e.id] = e
    return list(uniq.values())


def entity_ids(entities: List[Entity]) -> List[str]:
    return [e.id for e in entities]
