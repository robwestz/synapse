from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .providers.dataforseo import DataForSEOClient, parse_serp_snapshot
from .utils import jaccard


@dataclass
class SerpSnapshot:
    keyword: str
    top_urls: List[str]
    features: List[str]
    paa_questions: List[str]
    related_searches: List[str]
    raw: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyword": self.keyword,
            "top_urls": self.top_urls,
            "features": self.features,
            "paa": self.paa_questions,
            "related": self.related_searches,
        }


def fetch_seed_serp(
    dfs: DataForSEOClient,
    keyword: str,
    *,
    location_name: Optional[str] = None,
    location_code: Optional[int] = None,
    language_code: Optional[str] = None,
    depth: int = 10,
) -> SerpSnapshot:
    payload = dfs.serp_live_advanced(
        keyword=keyword,
        location_name=location_name,
        location_code=location_code,
        language_code=language_code,
        depth=depth,
    )
    snap = parse_serp_snapshot(payload)
    return SerpSnapshot(
        keyword=keyword,
        top_urls=list(snap.get("top_urls", []) or []),
        features=list(snap.get("features", []) or []),
        paa_questions=list(snap.get("paa", []) or []),
        related_searches=list(snap.get("related", []) or []),
        raw=snap,
    )


def serp_overlap(seed_top_urls: List[str], cand_top_urls: List[str]) -> float:
    return float(jaccard(seed_top_urls, cand_top_urls))
