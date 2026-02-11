"""
Dominance Lens - Shows what #1 domain ranks for in same cluster family.
"""

from __future__ import annotations
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict

sys.path.insert(0, str(__file__).rsplit("analyzers", 1)[0].rstrip("/\\"))

from core.canonical_types import AttributedKeyword


@dataclass
class DominanceEntry:
    keyword: str
    keyword_id: str
    cluster_id: str
    cluster_label: str
    position_1_domain: str
    position_1_url: Optional[str]
    my_position: Optional[int]
    volume: Optional[int]
    is_underperforming: bool


@dataclass
class DominanceLensResult:
    focus_keyword: str
    focus_entity_id: str
    dominant_domain: str
    dominant_footprint: int
    my_footprint: int
    underperforming_keywords: List[DominanceEntry]
    opportunity_score: float


class DominanceLens:
    """Analyzes what the #1 domain ranks for."""
    
    def __init__(
        self,
        mine_domain: str,
        attributed_keywords: List[AttributedKeyword],
        rank_data: List
    ):
        self.mine_domain = mine_domain
        self.attributed = {kw.keyword_id: kw for kw in attributed_keywords}
        
        self.rank_index: Dict[str, Dict[str, any]] = defaultdict(dict)
        for rd in rank_data:
            self.rank_index[rd.keyword_id][rd.domain] = rd
    
    def analyze(
        self,
        focus_keyword: str,
        include_cluster_siblings: bool = True,
        max_results: int = 50
    ) -> DominanceLensResult:
        """Analyze dominance for a focus keyword."""
        
        focus_attr = None
        for kw in self.attributed.values():
            if kw.keyword.lower() == focus_keyword.lower():
                focus_attr = kw
                break
        
        if not focus_attr:
            return DominanceLensResult(
                focus_keyword=focus_keyword,
                focus_entity_id="",
                dominant_domain="",
                dominant_footprint=0,
                my_footprint=0,
                underperforming_keywords=[],
                opportunity_score=0.0
            )
        
        entity_id = focus_attr.attribution.primary_entity_id
        cluster_id = focus_attr.attribution.cluster_id
        
        related_keywords = []
        for kw in self.attributed.values():
            if kw.attribution.primary_entity_id == entity_id:
                if not include_cluster_siblings or kw.attribution.cluster_id == cluster_id:
                    related_keywords.append(kw)
        
        domain_counts: Dict[str, int] = defaultdict(int)
        for kw in related_keywords:
            ranks = self.rank_index.get(kw.keyword_id, {})
            for domain, rd in ranks.items():
                if hasattr(rd, 'position') and rd.position == 1:
                    domain_counts[domain] += 1
        
        dominant_domain = max(domain_counts, key=domain_counts.get) if domain_counts else ""
        dominant_footprint = domain_counts.get(dominant_domain, 0)
        my_footprint = domain_counts.get(self.mine_domain, 0)
        
        underperforming = []
        for kw in related_keywords:
            ranks = self.rank_index.get(kw.keyword_id, {})
            
            pos1_domain = ""
            pos1_url = None
            for domain, rd in ranks.items():
                if hasattr(rd, 'position') and rd.position == 1:
                    pos1_domain = domain
                    pos1_url = getattr(rd, 'url', None)
                    break
            
            my_rd = ranks.get(self.mine_domain)
            my_pos = my_rd.position if my_rd and hasattr(my_rd, 'position') else None
            volume = my_rd.volume if my_rd and hasattr(my_rd, 'volume') else None
            
            is_underperforming = (
                pos1_domain == dominant_domain and
                (my_pos is None or my_pos > 3)
            )
            
            if is_underperforming:
                underperforming.append(DominanceEntry(
                    keyword=kw.keyword,
                    keyword_id=kw.keyword_id,
                    cluster_id=kw.attribution.cluster_id,
                    cluster_label=kw.attribution.cluster_label,
                    position_1_domain=pos1_domain,
                    position_1_url=pos1_url,
                    my_position=my_pos,
                    volume=volume,
                    is_underperforming=True
                ))
        
        underperforming.sort(key=lambda x: x.volume or 0, reverse=True)
        underperforming = underperforming[:max_results]
        
        total_volume = sum(u.volume or 0 for u in underperforming)
        opportunity_score = total_volume * (dominant_footprint / max(my_footprint, 1))
        
        return DominanceLensResult(
            focus_keyword=focus_keyword,
            focus_entity_id=entity_id,
            dominant_domain=dominant_domain,
            dominant_footprint=dominant_footprint,
            my_footprint=my_footprint,
            underperforming_keywords=underperforming,
            opportunity_score=opportunity_score
        )


def get_dominance_lens(
    focus_keyword: str,
    mine_domain: str,
    attributed_keywords: List[AttributedKeyword],
    rank_data: List,
    include_cluster_siblings: bool = True,
    max_results: int = 50
) -> DominanceLensResult:
    """Convenience function for dominance lens analysis."""
    lens = DominanceLens(mine_domain, attributed_keywords, rank_data)
    return lens.analyze(focus_keyword, include_cluster_siblings, max_results)
