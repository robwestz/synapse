from __future__ import annotations

import hashlib
import re
from typing import Iterable, List


def slugify(text: str) -> str:
    """ASCII-ish slug for stable IDs.

    This is intentionally simple and deterministic.
    """
    t = text.strip().lower()
    # Replace swedish chars (basic)
    t = t.replace("å", "a").replace("ä", "a").replace("ö", "o")
    t = re.sub(r"[^a-z0-9]+", "_", t)
    t = re.sub(r"_+", "_", t).strip("_")
    return t or "x"


def stable_qid(phrase: str, language: str, market: str) -> str:
    """Stable query ID as q.<hash>.

    Keep it short for UI, but stable across runs.
    """
    h = hashlib.sha1(f"{language}:{market}:{phrase}".encode("utf-8")).hexdigest()[:10]
    return f"q.{h}"


def stable_eid(entity_type: str, canonical: str) -> str:
    return f"e.{entity_type}.{slugify(canonical)}"


def tokenize_simple(text: str) -> List[str]:
    # Keep Swedish letters, digits
    tokens = re.findall(r"[a-zA-ZåäöÅÄÖ0-9]+", text.lower())
    return tokens


SW_STOP = {
    # tiny stop set (expand per pack)
    "och","att","det","som","en","ett","i","på","for","för","av","till","med","utan",
    "hur","vad","är","kan","jag","vi","ni","du","min","mitt","mina","vår","vårt","våra",
    "bäst","bästa","billigast","jämför","jämförelse","vs","upp",
}


def content_tokens(text: str) -> List[str]:
    return [t for t in tokenize_simple(text) if t not in SW_STOP and len(t) > 1]


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)
