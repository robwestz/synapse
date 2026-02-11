from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .utils import content_tokens

from .runtime import Runtime
from .providers.dataforseo import parse_keyword_suggestions
from .providers.ahrefs import parse_matching_terms


@dataclass
class Candidate:
    phrase: str
    provenance: str
    rationale: str
    metrics: Optional[Dict[str, Any]] = None


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


def generate_candidates(
    seed_phrase: str,
    language: str,
    market: str,
    target_pool: int = 300,
    runtime: Optional[Runtime] = None,
    seed_serp_snapshot: Optional[Dict[str, Any]] = None,
) -> List[Candidate]:
    """Generate a candidate pool.

    - Offline mode (runtime=None): deterministic template expansion.
    - Online mode: uses configured providers (DataForSEO/Ahrefs) and enriches with
      SERP-derived PAA/related queries when available.

    We *still* add a small template expansion to guarantee diversity + reach the
    desired pool size with a predictable budget.
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

    # -------------------------
    # Provider-backed candidates
    # -------------------------
    if runtime is not None:
        # DataForSEO Labs (keyword suggestions = long-tail candidates + metrics)
        if runtime.providers.dataforseo is not None:
            try:
                resp = runtime.providers.dataforseo.keyword_suggestions(
                    seed=seed_phrase,
                    location_name=runtime.location_name,
                    location_code=runtime.location_code,
                    language_code=runtime.language_code,
                    limit=runtime.budget.keyword_suggestions_limit,
                    include_seed_keyword=False,
                )
                for row in parse_keyword_suggestions(resp):
                    kw = row.get("keyword")
                    if not kw:
                        continue
                    candidates.append(
                        Candidate(
                            phrase=str(kw),
                            provenance="ads_api",
                            rationale="DataForSEO Labs: keyword_suggestions",
                            metrics=row,
                        )
                    )
            except Exception:
                # Provider failures should never kill the run.
                pass

            try:
                resp = runtime.providers.dataforseo.related_keywords(
                    seed=seed_phrase,
                    location_name=runtime.location_name,
                    location_code=runtime.location_code,
                    language_code=runtime.language_code,
                    limit=runtime.budget.related_keywords_limit,
                    include_seed_keyword=False,
                )
                for row in parse_keyword_suggestions(resp):
                    kw = row.get("keyword")
                    if not kw:
                        continue
                    candidates.append(
                        Candidate(
                            phrase=str(kw),
                            provenance="serp_related",
                            rationale="DataForSEO Labs: related_keywords (SERP-related)",
                            metrics=row,
                        )
                    )
            except Exception:
                pass

        # Ahrefs (matching terms)
        if runtime.providers.ahrefs is not None:
            try:
                resp = runtime.providers.ahrefs.keywords_matching_terms([seed_phrase], limit=1000)
                for row in parse_matching_terms(resp):
                    kw = row.get("keyword")
                    if not kw:
                        continue
                    candidates.append(
                        Candidate(
                            phrase=str(kw),
                            provenance="ads_api",
                            rationale="Ahrefs v3: keywords_matching_terms",
                            metrics=row,
                        )
                    )
            except Exception:
                pass

        # Seed SERP expansion (PAA + related searches)
        if seed_serp_snapshot:
            for q in seed_serp_snapshot.get("paa", []) or []:
                candidates.append(Candidate(phrase=str(q), provenance="serp_paa", rationale="Seed SERP: People Also Ask"))
            for q in seed_serp_snapshot.get("related", []) or []:
                candidates.append(Candidate(phrase=str(q), provenance="serp_related", rationale="Seed SERP: Related searches"))

    # -------------------------
    # Offline-friendly backfill
    # -------------------------
    if runtime is None:
        # In fully offline mode: keep the existing behaviour (pure template pool)
        for tpl in provider_templates:
            candidates.append(Candidate(phrase=fmt(tpl), provenance="llm_inferred", rationale="Template expansion (provider/transactional)."))
        for tpl in advisor_templates:
            candidates.append(Candidate(phrase=fmt(tpl), provenance="llm_inferred", rationale="Template expansion (advisor/commercial)."))
        for tpl in seeker_templates:
            candidates.append(Candidate(phrase=fmt(tpl), provenance="llm_inferred", rationale="Template expansion (seeker/informational)."))
        for tpl in regulator_templates:
            candidates.append(Candidate(phrase=fmt(tpl), provenance="llm_inferred", rationale="Template expansion (regulator/informational)."))
    else:
        # In online mode: still add a small, controlled template expansion for diversity.
        for tpl in advisor_templates[:4]:
            candidates.append(Candidate(phrase=fmt(tpl), provenance="llm_inferred", rationale="Template backfill (diversity)."))
        for tpl in seeker_templates[:4]:
            candidates.append(Candidate(phrase=fmt(tpl), provenance="llm_inferred", rationale="Template backfill (diversity)."))

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
        deduped.append(Candidate(phrase=k, provenance=c.provenance, rationale=c.rationale, metrics=c.metrics))

    # If we still have too few, pad with "hur" questions around topic
    while len(deduped) < target_pool:
        idx = len(deduped) + 1
        deduped.append(Candidate(phrase=f"hur fungerar {topic} {idx}", provenance="llm_inferred", rationale="Padding to reach pool size."))

    return deduped[:target_pool]
