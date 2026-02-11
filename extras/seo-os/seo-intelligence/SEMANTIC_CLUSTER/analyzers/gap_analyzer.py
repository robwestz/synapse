"""
Gap Analyzer - Identifies entity and cluster gaps vs competitors.
"""

from __future__ import annotations
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import date

sys.path.insert(0, str(__file__).rsplit("analyzers", 1)[0].rstrip("/\\"))

from core.canonical_types import (
    Intent, ClusterRole, TaskArchetype,
    EntityGap, EntityGapSummary, IntentGap, ClusterGap, GapAction,
    AttributedKeyword
)


@dataclass
class RankData:
    keyword_id: str
    keyword: str
    domain: str
    position: Optional[int]
    volume: Optional[int] = None
    url: Optional[str] = None


class GapAnalyzer:
    """Analyzes gaps between mine and competitor visibility."""
    
    def __init__(
        self,
        mine_domain: str,
        competitor_domains: List[str],
        attributed_keywords: List[AttributedKeyword],
        rank_data: List[RankData]
    ):
        self.mine_domain = mine_domain
        self.competitor_domains = competitor_domains
        self.attributed = {kw.keyword_id: kw for kw in attributed_keywords}
        
        self.rank_index: Dict[str, Dict[str, RankData]] = defaultdict(dict)
        for rd in rank_data:
            self.rank_index[rd.keyword_id][rd.domain] = rd
    
    def get_entity_gaps(self, entity_id: Optional[str] = None) -> List[EntityGap]:
        """Get gaps for all entities or a specific entity."""
        entity_keywords: Dict[str, List[AttributedKeyword]] = defaultdict(list)
        for kw in self.attributed.values():
            eid = kw.attribution.primary_entity_id
            if entity_id is None or eid == entity_id:
                entity_keywords[eid].append(kw)
        
        gaps = []
        for eid, keywords in entity_keywords.items():
            gap = self._analyze_entity_gap(eid, keywords)
            if gap.summary.gap_keywords > 0:
                gaps.append(gap)
        
        gaps.sort(key=lambda g: g.summary.priority_score, reverse=True)
        return gaps
    
    def _analyze_entity_gap(self, entity_id: str, keywords: List[AttributedKeyword]) -> EntityGap:
        """Analyze gap for a single entity."""
        mine_top20 = 0
        competitor_top20 = 0
        gap_keywords = 0
        total_volume_gap = 0
        
        intent_gaps: Dict[Intent, int] = defaultdict(int)
        cluster_gaps: Dict[str, int] = defaultdict(int)
        
        for kw in keywords:
            kw_id = kw.keyword_id
            ranks = self.rank_index.get(kw_id, {})
            
            mine_rank = ranks.get(self.mine_domain)
            mine_in_top20 = mine_rank and mine_rank.position and mine_rank.position <= 20
            
            competitor_in_top20 = any(
                ranks.get(cd) and ranks[cd].position and ranks[cd].position <= 20
                for cd in self.competitor_domains
            )
            
            if mine_in_top20:
                mine_top20 += 1
            
            if competitor_in_top20:
                competitor_top20 += 1
                
                if not mine_in_top20:
                    gap_keywords += 1
                    intent_gaps[kw.attribution.intent] += 1
                    cluster_gaps[kw.attribution.cluster_id] += 1
                    
                    for cd in self.competitor_domains:
                        rd = ranks.get(cd)
                        if rd and rd.volume:
                            total_volume_gap += rd.volume
                            break
        
        avg_kd = 50
        serp_homogeneity = 0.6
        priority = total_volume_gap * (1 / (1 + avg_kd/100)) * serp_homogeneity
        
        intent_gap_list = [
            IntentGap(intent=intent, gap_keywords=count, priority_score=count * 10)
            for intent, count in intent_gaps.items()
        ]
        
        cluster_gap_list = [
            ClusterGap(
                cluster_id=cid, 
                cluster_label=cid,
                gap_keywords=count,
                priority_score=count * 10,
                role=ClusterRole.SUPPORT
            )
            for cid, count in cluster_gaps.items()
        ]
        
        actions = []
        if gap_keywords > 0 and cluster_gaps:
            top_cluster = max(cluster_gaps, key=cluster_gaps.get)
            actions.append(GapAction(
                action_type="create_page",
                cluster_id=top_cluster,
                recommended_archetype=TaskArchetype.GUIDE,
                why=f"High gap ({cluster_gaps[top_cluster]} keywords) in this cluster"
            ))
        
        entity_name = entity_id.replace("e_", "").capitalize()
        
        return EntityGap(
            entity_id=entity_id,
            entity_name=entity_name,
            snapshot_date=str(date.today()),
            mine_domain=self.mine_domain,
            competitors=self.competitor_domains,
            summary=EntityGapSummary(
                mine_top20=mine_top20,
                competitor_top20=competitor_top20,
                gap_keywords=gap_keywords,
                priority_score=priority
            ),
            by_intent=intent_gap_list,
            by_cluster=cluster_gap_list,
            top_actions=actions
        )


def get_entity_gaps(
    mine_domain: str,
    competitor_domains: List[str],
    attributed_keywords: List[AttributedKeyword],
    rank_data: List[RankData],
    entity_id: Optional[str] = None
) -> List[EntityGap]:
    """Convenience function to get entity gaps."""
    analyzer = GapAnalyzer(mine_domain, competitor_domains, attributed_keywords, rank_data)
    return analyzer.get_entity_gaps(entity_id)
