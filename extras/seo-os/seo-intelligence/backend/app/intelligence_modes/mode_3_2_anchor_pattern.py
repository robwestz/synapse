"""
MODE 3.2: Anchor Text Pattern Mining
Analyzes anchor text patterns in competitor backlinks to identify link building strategies
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import Counter
import re

from app.models.uploads import Backlink, Upload
from app.core.ai_engine import AIEngine


class AnchorPatternMiner:
    """
    Mines anchor text patterns from competitor backlinks

    Reveals:
    - What anchor text themes they use
    - Natural vs. optimized anchor distribution
    - Link building strategies based on anchor patterns
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self) -> Dict[str, Any]:
        """
        Execute anchor text pattern analysis
        """

        # Step 1: Get your backlinks
        your_backlinks = await self._get_backlinks(is_primary=True)

        # Step 2: Get competitor backlinks
        competitor_backlinks = await self._get_backlinks(is_primary=False)

        if not your_backlinks or not competitor_backlinks:
            return {
                "error": "No backlink data found. Upload Backlinks report."
            }

        # Step 3: Extract anchor patterns
        your_patterns = self._extract_anchor_patterns(your_backlinks)
        competitor_patterns = self._extract_anchor_patterns(competitor_backlinks)

        # Step 4: Compare patterns
        pattern_gaps = self._identify_pattern_gaps(your_patterns, competitor_patterns)

        # Step 5: Classify anchor types
        your_classification = self._classify_anchors(your_backlinks)
        competitor_classification = self._classify_anchors(competitor_backlinks)

        # Step 6: Generate AI insight
        ai_insight = await self._generate_ai_insight(
            your_patterns,
            competitor_patterns,
            pattern_gaps,
            your_classification,
            competitor_classification
        )

        return {
            "mode": "3.2_anchor_pattern_mining",
            "status": "completed",
            "summary": {
                "your_total_backlinks": len(your_backlinks),
                "competitor_total_backlinks": len(competitor_backlinks),
                "your_unique_anchors": len(your_patterns['unique_anchors']),
                "competitor_unique_anchors": len(competitor_patterns['unique_anchors']),
                "pattern_gaps": len(pattern_gaps),
            },
            "your_anchor_profile": your_patterns,
            "competitor_anchor_profile": competitor_patterns,
            "your_anchor_classification": your_classification,
            "competitor_anchor_classification": competitor_classification,
            "pattern_gaps": pattern_gaps,
            "ai_insight": ai_insight,
        }

    async def _get_backlinks(self, is_primary: bool) -> List[Dict]:
        """
        Get backlinks with anchor text
        """
        query = (
            select(Backlink, Upload.source_domain)
            .join(Upload, Backlink.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.is_primary == is_primary)
            .where(Upload.processing_status == "completed")
            .where(Backlink.anchor.isnot(None))
            .where(Backlink.anchor != "")
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        backlinks = []
        for row in rows:
            bl_obj, domain = row
            backlinks.append({
                "anchor": bl_obj.anchor,
                "referring_domain": bl_obj.referring_domain,
                "domain_rating": bl_obj.domain_rating or 0,
                "url_rating": bl_obj.url_rating or 0,
                "target_url": bl_obj.target_url,
                "lost": bl_obj.lost or False,
            })

        return backlinks

    def _extract_anchor_patterns(self, backlinks: List[Dict]) -> Dict:
        """
        Extract anchor text patterns and themes
        """
        anchor_counter = Counter()
        all_anchors = []

        for bl in backlinks:
            anchor = bl['anchor'].strip()
            if anchor and len(anchor) > 0:
                anchor_counter[anchor] += 1
                all_anchors.append(anchor)

        # Get top anchors
        top_anchors = [
            {
                'anchor': anchor,
                'count': count,
                'percent': round(count / len(backlinks) * 100, 2)
            }
            for anchor, count in anchor_counter.most_common(100)
        ]

        # Extract themes/patterns
        themes = self._extract_themes(all_anchors)

        return {
            'total_backlinks': len(backlinks),
            'unique_anchors': len(anchor_counter),
            'top_anchors': top_anchors,
            'anchor_diversity': round(len(anchor_counter) / len(backlinks), 3),
            'themes': themes,
        }

    def _extract_themes(self, anchors: List[str]) -> Dict:
        """
        Extract common themes from anchor texts
        """
        theme_patterns = {
            'brand': r'\b(brand|company|official|home)\b',
            'product': r'\b(tool|software|platform|app|service|product)\b',
            'action': r'\b(click|visit|check|read|learn|try|download|get)\b',
            'quality': r'\b(best|top|great|leading|premium|free)\b',
            'educational': r'\b(guide|tutorial|how to|tips|learn|course)\b',
            'commercial': r'\b(buy|price|discount|deal|sale|offer)\b',
            'naked_url': r'^https?://',
            'generic': r'^(here|click here|this|read more|website|link)$',
        }

        theme_counts = Counter()

        for anchor in anchors:
            anchor_lower = anchor.lower()

            for theme, pattern in theme_patterns.items():
                if re.search(pattern, anchor_lower, re.IGNORECASE):
                    theme_counts[theme] += 1

        total = len(anchors)
        theme_distribution = {
            theme: {
                'count': count,
                'percent': round(count / total * 100, 1)
            }
            for theme, count in theme_counts.items()
        }

        return theme_distribution

    def _classify_anchors(self, backlinks: List[Dict]) -> Dict:
        """
        Classify anchors into types:
        - Exact match: exact keyword
        - Partial match: contains keyword
        - Branded: contains brand name
        - Naked URL: raw URL
        - Generic: "click here", "read more"
        - Natural: long, descriptive anchors
        """
        classifications = {
            'exact_match': 0,
            'partial_match': 0,
            'branded': 0,
            'naked_url': 0,
            'generic': 0,
            'natural': 0,
        }

        for bl in backlinks:
            anchor = bl['anchor'].lower()

            # Naked URL
            if re.match(r'^https?://', anchor):
                classifications['naked_url'] += 1
            # Generic
            elif anchor in ['here', 'click here', 'this', 'read more', 'website', 'link', 'source']:
                classifications['generic'] += 1
            # Natural (long, sentence-like)
            elif len(anchor.split()) >= 5:
                classifications['natural'] += 1
            # Partial/exact/branded would require keyword/brand data
            # For now, classify short anchors as partial match
            elif len(anchor.split()) <= 4:
                classifications['partial_match'] += 1
            else:
                classifications['natural'] += 1

        total = len(backlinks)
        return {
            key: {
                'count': value,
                'percent': round(value / total * 100, 1) if total > 0 else 0
            }
            for key, value in classifications.items()
        }

    def _identify_pattern_gaps(
        self,
        your_patterns: Dict,
        competitor_patterns: Dict
    ) -> List[Dict]:
        """
        Find anchor themes/patterns competitors use that you don't
        """
        your_themes = set(your_patterns['themes'].keys())
        comp_themes = set(competitor_patterns['themes'].keys())

        # Themes competitors use more
        gaps = []

        for theme in comp_themes:
            your_percent = your_patterns['themes'].get(theme, {}).get('percent', 0)
            comp_percent = competitor_patterns['themes'].get(theme, {}).get('percent', 0)

            if comp_percent > your_percent + 5:  # At least 5% difference
                gaps.append({
                    'theme': theme,
                    'your_percent': your_percent,
                    'competitor_percent': comp_percent,
                    'gap': round(comp_percent - your_percent, 1),
                    'recommendation': self._get_theme_recommendation(theme, comp_percent),
                })

        gaps.sort(key=lambda x: x['gap'], reverse=True)
        return gaps

    def _get_theme_recommendation(self, theme: str, comp_percent: float) -> str:
        """
        Generate recommendation based on anchor theme gap
        """
        recommendations = {
            'product': "Build more product/tool pages that naturally attract 'product' anchors",
            'quality': "Create best-of/top lists to earn 'best' and 'top' anchor text",
            'educational': "Publish comprehensive guides to earn educational anchor text",
            'free': "Launch free tools/resources to attract 'free' anchors",
            'brand': "Increase brand awareness and authority for more branded links",
        }

        return recommendations.get(theme, f"Increase {theme}-themed anchor text through relevant content")

    async def _generate_ai_insight(
        self,
        your_patterns: Dict,
        competitor_patterns: Dict,
        gaps: List[Dict],
        your_classification: Dict,
        comp_classification: Dict
    ) -> Dict:
        """
        Generate AI strategic insight on anchor patterns
        """

        your_top_anchors = "\n".join([
            f"- \"{a['anchor']}\" ({a['percent']:.1f}%)"
            for a in your_patterns['top_anchors'][:10]
        ])

        comp_top_anchors = "\n".join([
            f"- \"{a['anchor']}\" ({a['percent']:.1f}%)"
            for a in competitor_patterns['top_anchors'][:10]
        ])

        pattern_gaps_text = "\n".join([
            f"- {g['theme'].upper()}: Competitor {g['competitor_percent']:.1f}%, You {g['your_percent']:.1f}% (Gap: {g['gap']:.1f}%)"
            for g in gaps[:5]
        ]) if gaps else "No significant gaps"

        prompt = f"""
Analyze this anchor text pattern analysis:

YOUR TOP ANCHORS:
{your_top_anchors}

COMPETITOR TOP ANCHORS:
{comp_top_anchors}

YOUR ANCHOR CLASSIFICATION:
- Natural: {your_classification['natural']['percent']:.1f}%
- Partial Match: {your_classification['partial_match']['percent']:.1f}%
- Naked URL: {your_classification['naked_url']['percent']:.1f}%
- Generic: {your_classification['generic']['percent']:.1f}%

COMPETITOR ANCHOR CLASSIFICATION:
- Natural: {comp_classification['natural']['percent']:.1f}%
- Partial Match: {comp_classification['partial_match']['percent']:.1f}%
- Naked URL: {comp_classification['naked_url']['percent']:.1f}%
- Generic: {comp_classification['generic']['percent']:.1f}%

THEME GAPS:
{pattern_gaps_text}

Provide:

1. ANCHOR STRATEGY ANALYSIS
   - What does your anchor distribution reveal about link building approach?
   - Natural vs. optimized - what's the risk?

2. COMPETITIVE ANCHOR STRATEGY
   - What anchor patterns are competitors using successfully?
   - What content types attract what anchor themes?

3. LINK BUILDING RECOMMENDATIONS
   - What anchor themes to pursue?
   - What content to create to attract those anchors?

4. RISK ASSESSMENT
   - Is anchor distribution natural enough?
   - Any over-optimization risks?

Be specific about what content to create to attract specific anchor patterns.
        """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="anchor_pattern_mining",
            use_complex_model=True
        )

        return ai_result
