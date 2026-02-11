"""
MODE 1.2: Longtail Gap Finder
Identifies longtail keywords (5+ words) where competitors rank but you don't
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from collections import defaultdict
import re

from app.models.uploads import OrganicKeyword, Upload
from app.core.ai_engine import AIEngine, PromptTemplates


class LongtailGapFinder:
    """
    Finds longtail keyword opportunities by comparing your rankings vs competitors
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()
        self.min_word_count = 5  # Definition of "longtail"

    async def execute(self) -> Dict[str, Any]:
        """
        Execute longtail gap analysis
        """

        # Step 1: Get all your keywords
        your_keywords = await self._get_keywords(is_primary=True)
        your_keyword_set = set(kw['keyword'].lower() for kw in your_keywords)

        # Step 2: Get competitor keywords
        competitor_keywords = await self._get_keywords(is_primary=False)

        # Step 3: Filter for longtails (5+ words)
        competitor_longtails = [
            kw for kw in competitor_keywords
            if self._count_words(kw['keyword']) >= self.min_word_count
        ]

        # Step 4: Find gaps (competitor ranks, you don't)
        longtail_gaps = [
            kw for kw in competitor_longtails
            if kw['keyword'].lower() not in your_keyword_set
        ]

        # Step 5: Calculate total opportunity
        total_traffic_potential = sum(kw.get('traffic', 0) or 0 for kw in longtail_gaps)
        total_volume = sum(kw.get('volume', 0) or 0 for kw in longtail_gaps)

        # Step 6: Cluster by patterns
        patterns = self._identify_patterns(longtail_gaps)

        # Step 7: Sort by opportunity
        longtail_gaps.sort(key=lambda x: (x.get('volume', 0) or 0), reverse=True)

        # Step 8: Get AI insights
        ai_insight = await self._generate_ai_insight(
            longtail_gaps[:50],  # Top 50 for AI analysis
            patterns
        )

        return {
            "mode": "1.2_longtail_gap",
            "status": "completed",
            "summary": {
                "total_longtail_gaps": len(longtail_gaps),
                "total_traffic_potential": round(total_traffic_potential, 0),
                "total_search_volume": total_volume,
                "avg_word_count": round(sum(self._count_words(kw['keyword']) for kw in longtail_gaps) / len(longtail_gaps), 1) if longtail_gaps else 0,
            },
            "patterns": patterns,
            "top_opportunities": longtail_gaps[:20],
            "full_gaps": longtail_gaps,
            "ai_insight": ai_insight,
        }

    async def _get_keywords(self, is_primary: bool) -> List[Dict]:
        """
        Get organic keywords
        """
        query = (
            select(OrganicKeyword, Upload.source_domain)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.is_primary == is_primary)
            .where(Upload.processing_status == "completed")
            .where(OrganicKeyword.position.isnot(None))  # Must have ranking
            .where(OrganicKeyword.position <= 100)  # Top 100 only
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        keywords = []
        for row in rows:
            keyword_obj, domain = row
            keywords.append({
                "keyword": keyword_obj.keyword,
                "position": keyword_obj.position,
                "volume": keyword_obj.volume,
                "traffic": keyword_obj.traffic,
                "difficulty": keyword_obj.difficulty,
                "domain": domain,
            })

        return keywords

    def _count_words(self, keyword: str) -> int:
        """
        Count words in keyword
        """
        # Remove special characters, split by whitespace
        words = re.findall(r'\b\w+\b', keyword.lower())
        return len(words)

    def _identify_patterns(self, longtails: List[Dict]) -> List[Dict]:
        """
        Identify common patterns in longtail keywords
        e.g., "how to", "vs", "best", etc.
        """
        pattern_counts = defaultdict(lambda: {"count": 0, "traffic": 0, "keywords": []})

        patterns_to_check = [
            "how to",
            "what is",
            "why",
            "when",
            "where",
            "vs",
            "versus",
            "best",
            "top",
            "guide",
            "tutorial",
            "review",
            "comparison",
            "for beginners",
            "step by step",
        ]

        for kw in longtails:
            keyword_lower = kw['keyword'].lower()

            for pattern in patterns_to_check:
                if pattern in keyword_lower:
                    pattern_counts[pattern]["count"] += 1
                    pattern_counts[pattern]["traffic"] += kw.get('traffic', 0) or 0
                    pattern_counts[pattern]["keywords"].append(kw['keyword'])

        # Convert to list and sort by count
        patterns = [
            {
                "pattern": pattern,
                "count": data["count"],
                "traffic_potential": round(data["traffic"], 0),
                "example_keywords": data["keywords"][:5],
            }
            for pattern, data in pattern_counts.items()
        ]

        patterns.sort(key=lambda x: x['count'], reverse=True)

        return patterns[:10]  # Top 10 patterns

    async def _generate_ai_insight(
        self,
        longtail_gaps: List[Dict],
        patterns: List[Dict]
    ) -> Dict:
        """
        Generate AI strategic insight for longtail gaps
        """

        context = {
            "total_gaps": len(longtail_gaps),
            "patterns": patterns,
        }

        prompt = PromptTemplates.longtail_gap(longtail_gaps)

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="longtail_gap",
            context=context,
            use_complex_model=False  # Sonnet is fine for this
        )

        return ai_result
