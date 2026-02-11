from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass
class NormalizedPhrase:
    raw: str
    canonical: str
    display: str


def normalize_numbers(text: str, strip_separators: bool) -> Tuple[str, str]:
    """Return (display_text, canonical_text) preserving a display version with separators."""
    display = text
    canonical = text

    # Normalize spaces in numbers like "800 000" -> "800000" in canonical
    if strip_separators:
        canonical = re.sub(r"(\d)[\s.,](?=\d{3}(\D|$))", r"\1", canonical)

    return display, canonical


def normalize_phrase(phrase: str, normalization_model: Dict[str, Any]) -> NormalizedPhrase:
    rules = normalization_model.get("normalization_model", {}).get("rules", {})
    t = phrase

    if rules.get("lowercase", False):
        t = t.lower()

    if rules.get("collapse_whitespace", False):
        t = re.sub(r"\s+", " ", t).strip()

    # Variant maps
    for vm in normalization_model.get("normalization_model", {}).get("variant_maps", []) or []:
        matches = vm.get("match", [])
        repl = vm.get("replace_with", "")
        for m in matches:
            # whole-word replacement
            t = re.sub(rf"\b{re.escape(m)}\b", repl, t)

    disp, canon = normalize_numbers(t, bool(rules.get("normalize_numbers", {}).get("strip_separators", False)))

    return NormalizedPhrase(raw=phrase, canonical=canon, display=disp)
