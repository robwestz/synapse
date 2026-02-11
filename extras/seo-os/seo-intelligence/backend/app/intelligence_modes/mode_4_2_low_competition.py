"""
MODE 4.2: Low-Competition High-Volume Finder
Identifies keywords with high volume but low difficulty - "low-hanging fruit"
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.uploads import OrganicKeyword, Upload, SERPOverview
from app.core.ai_engine import AIEngine


class LowCompetitionFinder:
    """
    Finds keywords with volume >1000 AND difficulty <30
    AND weak top 10 results (all DR <50)
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(
        self,
        min_volume: int = 1000,
        max_difficulty: int = 30,
        max_competitor_dr: int = 50
    ) -> Dict[str, Any]:
        """
        Execute low-competition keyword finder
        """

        # Step 1: Get keywords matching volume + difficulty criteria
        candidate_keywords = await self._get_candidate_keywords(
            min_volume,
            max_difficulty
        )

        if not candidate_keywords:
            return {
                "error": f"No keywords found with volume >{min_volume} and difficulty <{max_difficulty}"
            }

        # Step 2: Check SERP data for each keyword to verify weakness
        verified_opportunities = []

        for kw in candidate_keywords:
            is_weak = await self._check_serp_weakness(
                kw['keyword'],
                max_competitor_dr
            )

            if is_weak:
                kw['verified_weak_serp'] = True
                kw['opportunity_score'] = self._calculate_opportunity_score(kw)
                verified_opportunities.append(kw)

        # Step 3: Sort by opportunity score
        verified_opportunities.sort(
            key=lambda x: x['opportunity_score'],
            reverse=True
        )

        # Step 4: Generate AI insights
        ai_insight = await self._generate_ai_insight(
            verified_opportunities[:20]
        )

        return {
            "mode": "4.2_low_competition_high_volume",
            "status": "completed",
            "summary": {
                "candidate_keywords": len(candidate_keywords),
                "verified_opportunities": len(verified_opportunities),
                "avg_volume": round(sum(k['volume'] for k in verified_opportunities) / len(verified_opportunities), 0) if verified_opportunities else 0,
                "avg_difficulty": round(sum(k['difficulty'] for k in verified_opportunities) / len(verified_opportunities), 1) if verified_opportunities else 0,
            },
            "top_opportunities": verified_opportunities[:20],
            "full_list": verified_opportunities,
            "ai_insight": ai_insight,
        }

    async def _get_candidate_keywords(
        self,
        min_volume: int,
        max_difficulty: int
    ) -> List[Dict]:
        """
        Get keywords from competitor data matching volume + difficulty
        """
        query = (
            select(OrganicKeyword, Upload.source_domain)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.is_primary == False)  # Competitor keywords
            .where(Upload.processing_status == "completed")
            .where(OrganicKeyword.volume.isnot(None))
            .where(OrganicKeyword.volume >= min_volume)
            .where(OrganicKeyword.difficulty.isnot(None))
            .where(OrganicKeyword.difficulty <= max_difficulty)
            .where(OrganicKeyword.position.isnot(None))
            .where(OrganicKeyword.position <= 100)
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        keywords = []
        for row in rows:
            kw_obj, domain = row
            keywords.append({
                "keyword": kw_obj.keyword,
                "volume": kw_obj.volume,
                "difficulty": kw_obj.difficulty,
                "position": kw_obj.position,
                "traffic": kw_obj.traffic,
                "url": kw_obj.url,
                "competitor_domain": domain,
                "parent_topic": kw_obj.parent_topic,
                "intent": {
                    "informational": kw_obj.informational,
                    "commercial": kw_obj.commercial,
                    "transactional": kw_obj.transactional,
                }
            })

        # Deduplicate by keyword (keep highest volume)
        keyword_map = {}
        for kw in keywords:
            key = kw['keyword'].lower()
            if key not in keyword_map or kw['volume'] > keyword_map[key]['volume']:
                keyword_map[key] = kw

        return list(keyword_map.values())

    async def _check_serp_weakness(
        self,
        keyword: str,
        max_dr: int
    ) -> bool:
        """
        Check if SERP is "weak" (all top 10 results have DR < max_dr)
        Requires SERP overview data
        """
        query = (
            select(SERPOverview)
            .join(Upload, SERPOverview.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.processing_status == "completed")
            .where(SERPOverview.keyword == keyword)
            .where(SERPOverview.position.isnot(None))
            .where(SERPOverview.position <= 10)  # Top 10 only
            .where(SERPOverview.result_type != 'people also ask')  # Exclude PAA
        )

        result = await self.session.execute(query)
        serp_results = result.scalars().all()

        if not serp_results:
            # No SERP data available, assume weak
            return True

        # Check if ALL top 10 results have DR < max_dr
        weak_serp = all(
            (r.domain_rating or 0) < max_dr
            for r in serp_results
        )

        return weak_serp

    def _calculate_opportunity_score(self, keyword: Dict) -> float:
        """
        Calculate opportunity score (0-100)

        High score = high volume + low difficulty + weak SERP
        """
        score = 0

        # Volume (max 40 points)
        volume = keyword.get('volume', 0)
        if volume >= 10000:
            score += 40
        elif volume >= 5000:
            score += 30
        elif volume >= 2000:
            score += 20
        else:
            score += 10

        # Difficulty (max 30 points)
        # Lower difficulty = higher score
        difficulty = keyword.get('difficulty', 30)
        if difficulty <= 10:
            score += 30
        elif difficulty <= 20:
            score += 20
        elif difficulty <= 30:
            score += 10

        # SERP weakness (max 20 points)
        if keyword.get('verified_weak_serp'):
            score += 20

        # Intent bonus (max 10 points)
        # Transactional/Commercial more valuable
        intent = keyword.get('intent', {})
        if intent.get('transactional'):
            score += 10
        elif intent.get('commercial'):
            score += 7
        elif intent.get('informational'):
            score += 3

        return score

    async def _generate_ai_insight(
        self,
        opportunities: List[Dict]
    ) -> Dict:
        """
        Generate AI insights for low-competition opportunities
        """

        prompt = f"""
Analyze these low-competition, high-volume keyword opportunities:

OPPORTUNITIES:
{self._format_opportunities_for_ai(opportunities)}

Provide:

1. TOP 5 IMMEDIATE WINS
   - Which keywords to target first
   - Why they're easy wins
   - Content angle for each

2. COMMON THEMES
   - What patterns emerge?
   - What niche/subtopic do these represent?

3. CONTENT STRATEGY
   - Should these be separate articles or consolidated?
   - What's the hub-and-spoke approach?

4. COMPETITIVE ANALYSIS
   - Why is the SERP weak?
   - What makes this an opportunity?

Be specific and actionable.
        """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="low_competition_finder",
            use_complex_model=False
        )

        return ai_result

    def _format_opportunities_for_ai(self, opportunities: List[Dict]) -> str:
        """
        Format opportunities for AI prompt
        """
        lines = []
        for i, opp in enumerate(opportunities[:10], 1):
            lines.append(
                f"{i}. \"{opp['keyword']}\" - "
                f"Vol: {opp['volume']}, "
                f"KD: {opp['difficulty']}, "
                f"Score: {opp['opportunity_score']:.0f}"
            )

        return "\n".join(lines)
