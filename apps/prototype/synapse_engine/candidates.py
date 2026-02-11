from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from .utils import content_tokens


@dataclass
class Candidate:
    phrase: str
    provenance: str
    rationale: str


def _extract_amount(seed_phrase: str) -> Optional[str]:
    """Extract an amount-ish number from the seed (best-effort).

    Returns a display-like string (keeps spaces) if present.
    """
    # Match numbers with optional thousand separators
    m = re.findall(r"\d{1,3}(?:[\s.,]\d{3})+|\d+", seed_phrase)
    if not m:
        return None
    # pick the longest
    m.sort(key=len, reverse=True)
    return m[0]


def _extract_topic(seed_phrase: str) -> str:
    toks = content_tokens(seed_phrase)
    # drop pure numbers
    toks = [t for t in toks if not re.fullmatch(r"\d+", t)]
    if not toks:
        return seed_phrase.strip().lower()
    # keep at most 2 tokens to avoid long templates
    return " ".join(toks[:2])


def generate_candidates(seed_phrase: str, language: str, market: str, target_pool: int = 300) -> List[Candidate]:
    """Generate a tier-3 (LLM-like) candidate pool using templates.

    This is intentionally deterministic and offline-friendly.
    Replace with Ads/GSC/SERP connectors + LLM facet expansion for production.
    """
    topic = _extract_topic(seed_phrase)
    amount = _extract_amount(seed_phrase)

    year = "2026"  # keep deterministic; caller can override

    provider_templates = [
        "ansök {topic} online",
        "ansök om {topic}",
        "{topic} utan uc",
        "snabbt {topic}{amount}",
        "låna{amount} utan säkerhet",
        "{topic} låg ränta",
        "{topic} med betalningsanmärkning",
        "{topic} direkt utbetalning",
        "{topic} utan bankid",
        "{topic} ränta från",
    ]

    advisor_templates = [
        "jämför {topic}",
        "{topic} jämförelse ränta",
        "bästa {topic} {year}",
        "billigast {topic} {year}",
        "{topic} recension",
        "{topic} omdöme",
        "topplista {topic}",
        "bästa ränta {topic}",
        "alternativ till {topic}",
    ]

    seeker_templates = [
        "hur mycket kan jag låna",
        "räkna ut månadskostnad lån",
        "vad kostar lån per månad",
        "betala av {topic}{amount}",
        "amortera {topic} snabbare",
        "{topic} avbetalningsplan",
        "kvar att leva på efter lån",
        "samla lån och krediter",
        "budget med lån{amount}",
        "ångerrätt {topic} 14 dagar",
    ]

    regulator_templates = [
        "konsumentkreditlagen {topic}",
        "räntetak {topic} sverige",
        "finansinspektionen {topic}",
        "kreditprövning {topic} krav",
        "effektiv ränta {topic}",
        "regler för {topic}",
        "villkor {topic}",
    ]

    # small brand list (demo)
    brand_pairs = [("sbab", "nordea"), ("ica banken", "seb"), ("handelsbanken", "swedbank")]
    advisor_templates += [f"{b1} vs {b2} {topic}" for b1, b2 in brand_pairs]

    def fmt(tpl: str) -> str:
        a = f" {amount}" if (amount and "{amount}" in tpl) else ""
        return tpl.format(topic=topic, amount=a, year=year)

    candidates: List[Candidate] = []

    for tpl in provider_templates:
        candidates.append(Candidate(phrase=fmt(tpl), provenance="llm_inferred", rationale="Template expansion (provider/transactional)."))
    for tpl in advisor_templates:
        candidates.append(Candidate(phrase=fmt(tpl), provenance="llm_inferred", rationale="Template expansion (advisor/commercial)."))
    for tpl in seeker_templates:
        candidates.append(Candidate(phrase=fmt(tpl), provenance="llm_inferred", rationale="Template expansion (seeker/informational)."))
    for tpl in regulator_templates:
        candidates.append(Candidate(phrase=fmt(tpl), provenance="llm_inferred", rationale="Template expansion (regulator/informational)."))

    # Generate some additional variations by adding common modifiers
    modifiers = ["bästa", "billigast", "snabbt", "utan uc", "med låg ränta", "utan säkerhet"]
    bases = [f"{topic}", f"{topic} ränta", f"{topic} regler"]
    if amount:
        bases.append(f"{topic} {amount}")

    for m in modifiers:
        for b in bases:
            candidates.append(Candidate(phrase=f"{m} {b}", provenance="llm_inferred", rationale="Modifier recombination."))

    # Dedup (case-insensitive)
    seen = set()
    deduped: List[Candidate] = []
    for c in candidates:
        k = re.sub(r"\s+", " ", c.phrase.strip().lower())
        if not k or k == seed_phrase.strip().lower():
            continue
        if k in seen:
            continue
        seen.add(k)
        deduped.append(Candidate(phrase=k, provenance=c.provenance, rationale=c.rationale))

    # If we still have too few, pad with "hur" questions around topic
    while len(deduped) < target_pool:
        idx = len(deduped) + 1
        deduped.append(Candidate(phrase=f"hur fungerar {topic} {idx}", provenance="llm_inferred", rationale="Padding to reach pool size."))

    return deduped[:target_pool]
