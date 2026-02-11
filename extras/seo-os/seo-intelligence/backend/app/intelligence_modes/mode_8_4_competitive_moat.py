"""
MODE 8.4: Competitive Moat Strength Score
Calculates how difficult it is to compete with a specific competitor
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.uploads import (
    OrganicKeyword,
    ReferringDomain,
    Upload
)
from app.core.ai_engine import AIEngine
import math


class CompetitiveMoatAnalyzer:
    """
    Calculates competitive moat strength (0-100 score)

    Factors:
    - Brand strength (branded search volume)
    - Backlink profile (quality + quantity)
    - Content comprehensiveness (keywords per topic)
    - Domain age
    - SERP feature presence
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self, competitor_domain: str) -> Dict[str, Any]:
        """
        Calculate moat strength for a specific competitor
        """

        # Step 1: Get competitor's upload IDs
        competitor_uploads = await self._get_competitor_uploads(competitor_domain)

        if not competitor_uploads:
            return {
                "error": f"No data found for competitor: {competitor_domain}"
            }

        # Step 2: Calculate moat components
        moat_scores = {}

        # Brand strength (30%)
        brand_score = await self._calculate_brand_strength(competitor_uploads)
        moat_scores['brand_strength'] = brand_score

        # Backlink quality (25%)
        backlink_score = await self._calculate_backlink_quality(competitor_uploads)
        moat_scores['backlink_quality'] = backlink_score

        # Content comprehensiveness (20%)
        content_score = await self._calculate_content_comprehensiveness(competitor_uploads)
        moat_scores['content_comprehensiveness'] = content_score

        # Domain authority (15%)
        authority_score = await self._calculate_domain_authority(competitor_uploads)
        moat_scores['domain_authority'] = authority_score

        # SERP dominance (10%)
        serp_score = await self._calculate_serp_dominance(competitor_uploads)
        moat_scores['serp_dominance'] = serp_score

        # Step 3: Calculate overall moat score
        overall_moat = (
            brand_score * 0.30 +
            backlink_score * 0.25 +
            content_score * 0.20 +
            authority_score * 0.15 +
            serp_score * 0.10
        )

        # Step 4: Determine difficulty level
        difficulty = self._classify_difficulty(overall_moat)

        # Step 5: Generate AI strategic recommendation
        ai_insight = await self._generate_ai_insight(
            competitor_domain,
            overall_moat,
            moat_scores,
            difficulty
        )

        return {
            "mode": "8.4_competitive_moat",
            "status": "completed",
            "competitor_domain": competitor_domain,
            "overall_moat_score": round(overall_moat, 1),
            "difficulty_level": difficulty,
            "moat_components": {
                "brand_strength": round(brand_score, 1),
                "backlink_quality": round(backlink_score, 1),
                "content_comprehensiveness": round(content_score, 1),
                "domain_authority": round(authority_score, 1),
                "serp_dominance": round(serp_score, 1),
            },
            "ai_insight": ai_insight,
        }

    async def _get_competitor_uploads(self, domain: str) -> List[str]:
        """
        Get upload IDs for competitor
        """
        query = (
            select(Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.source_domain == domain)
            .where(Upload.is_primary == False)
            .where(Upload.processing_status == "completed")
        )

        result = await self.session.execute(query)
        upload_ids = [str(row[0]) for row in result.fetchall()]

        return upload_ids

    async def _calculate_brand_strength(self, upload_ids: List[str]) -> float:
        """
        Calculate brand strength based on branded vs non-branded traffic

        Score 0-100:
        - High branded traffic (>60%) = strong brand = high moat
        """
        query = (
            select(
                func.sum(OrganicKeyword.traffic).filter(OrganicKeyword.branded == True).label('branded'),
                func.sum(OrganicKeyword.traffic).filter(OrganicKeyword.branded == False).label('non_branded'),
            )
            .where(OrganicKeyword.upload_id.in_(upload_ids))
            .where(OrganicKeyword.traffic.isnot(None))
        )

        result = await self.session.execute(query)
        row = result.fetchone()

        branded = row.branded or 0
        non_branded = row.non_branded or 0
        total = branded + non_branded

        if total == 0:
            return 0

        branded_percent = (branded / total) * 100

        # Score: >80% branded = 100, <20% branded = 0
        if branded_percent >= 80:
            score = 100
        elif branded_percent >= 60:
            score = 75
        elif branded_percent >= 40:
            score = 50
        elif branded_percent >= 20:
            score = 25
        else:
            score = 0

        return score

    async def _calculate_backlink_quality(self, upload_ids: List[str]) -> float:
        """
        Calculate backlink quality

        Score based on:
        - Average DR of referring domains
        - Total referring domains
        """
        query = (
            select(
                func.avg(ReferringDomain.domain_rating).label('avg_dr'),
                func.count(ReferringDomain.id).label('total_domains'),
            )
            .where(ReferringDomain.upload_id.in_(upload_ids))
            .where(ReferringDomain.domain_rating.isnot(None))
        )

        result = await self.session.execute(query)
        row = result.fetchone()

        avg_dr = row.avg_dr or 0
        total_domains = row.total_domains or 0

        # DR component (60 points)
        dr_score = min((avg_dr / 70) * 60, 60)  # Max at DR 70

        # Volume component (40 points)
        # Log scale: 100 domains = 20 points, 1000 = 30, 10000 = 40
        if total_domains > 0:
            volume_score = min(math.log10(total_domains) * 13.3, 40)
        else:
            volume_score = 0

        return dr_score + volume_score

    async def _calculate_content_comprehensiveness(self, upload_ids: List[str]) -> float:
        """
        Calculate content comprehensiveness

        Score based on:
        - Keywords per parent topic (depth)
        - Total parent topics covered (breadth)
        """
        query = (
            select(
                OrganicKeyword.parent_topic,
                func.count(OrganicKeyword.id).label('keyword_count')
            )
            .where(OrganicKeyword.upload_id.in_(upload_ids))
            .where(OrganicKeyword.parent_topic.isnot(None))
            .group_by(OrganicKeyword.parent_topic)
        )

        result = await self.session.execute(query)
        topics = result.fetchall()

        if not topics:
            return 0

        # Average keywords per topic
        avg_keywords_per_topic = sum(t.keyword_count for t in topics) / len(topics)

        # Total topics
        total_topics = len(topics)

        # Depth score (60 points)
        # 100+ keywords per topic = 60 points
        depth_score = min((avg_keywords_per_topic / 100) * 60, 60)

        # Breadth score (40 points)
        # 50+ topics = 40 points
        breadth_score = min((total_topics / 50) * 40, 40)

        return depth_score + breadth_score

    async def _calculate_domain_authority(self, upload_ids: List[str]) -> float:
        """
        Calculate domain authority

        Score based on average DR from referring domains
        """
        query = (
            select(func.avg(ReferringDomain.domain_rating))
            .where(ReferringDomain.upload_id.in_(upload_ids))
            .where(ReferringDomain.domain_rating.isnot(None))
        )

        result = await self.session.execute(query)
        avg_dr = result.scalar() or 0

        # DR 70+ = 100 points
        score = min((avg_dr / 70) * 100, 100)

        return score

    async def _calculate_serp_dominance(self, upload_ids: List[str]) -> float:
        """
        Calculate SERP dominance

        Score based on:
        - % of keywords in top 3
        - Presence of SERP features
        """
        query = (
            select(
                func.count(OrganicKeyword.id).filter(OrganicKeyword.position <= 3).label('top_3'),
                func.count(OrganicKeyword.id).label('total'),
            )
            .where(OrganicKeyword.upload_id.in_(upload_ids))
            .where(OrganicKeyword.position.isnot(None))
        )

        result = await self.session.execute(query)
        row = result.fetchone()

        top_3 = row.top_3 or 0
        total = row.total or 0

        if total == 0:
            return 0

        top_3_percent = (top_3 / total) * 100

        # Score: >50% top 3 = 100, <10% = 0
        score = min((top_3_percent / 50) * 100, 100)

        return score

    def _classify_difficulty(self, moat_score: float) -> Dict[str, str]:
        """
        Classify difficulty based on moat score
        """
        if moat_score >= 80:
            return {
                "level": "EXTREMELY HARD",
                "recommendation": "AVOID - Target adjacent keywords or different market",
                "timeline": "3-5 years minimum",
                "estimated_cost": "$500K - $2M+",
            }
        elif moat_score >= 60:
            return {
                "level": "VERY HARD",
                "recommendation": "Consider carefully - High investment required",
                "timeline": "2-3 years",
                "estimated_cost": "$200K - $500K",
            }
        elif moat_score >= 40:
            return {
                "level": "MODERATE",
                "recommendation": "Viable with focused strategy",
                "timeline": "1-2 years",
                "estimated_cost": "$50K - $200K",
            }
        elif moat_score >= 20:
            return {
                "level": "RELATIVELY EASY",
                "recommendation": "Good opportunity - Execute well",
                "timeline": "6-12 months",
                "estimated_cost": "$20K - $50K",
            }
        else:
            return {
                "level": "VERY EASY",
                "recommendation": "GO FOR IT - Low barriers",
                "timeline": "3-6 months",
                "estimated_cost": "$5K - $20K",
            }

    async def _generate_ai_insight(
        self,
        domain: str,
        moat_score: float,
        components: Dict[str, float],
        difficulty: Dict[str, str]
    ) -> Dict:
        """
        Generate AI strategic recommendation
        """

        prompt = f"""
Analyze this competitive moat assessment:

COMPETITOR: {domain}
OVERALL MOAT SCORE: {moat_score:.1f}/100

MOAT BREAKDOWN:
- Brand Strength: {components['brand_strength']:.1f}/100
- Backlink Quality: {components['backlink_quality']:.1f}/100
- Content Comprehensiveness: {components['content_comprehensiveness']:.1f}/100
- Domain Authority: {components['domain_authority']:.1f}/100
- SERP Dominance: {components['serp_dominance']:.1f}/100

DIFFICULTY: {difficulty['level']}
TIMELINE: {difficulty['timeline']}
ESTIMATED COST: {difficulty['estimated_cost']}

Provide:

1. STRATEGIC ASSESSMENT
   - Is this competitor worth competing against directly?
   - What are their vulnerabilities?

2. ATTACK STRATEGY (if viable)
   - Which component to attack first?
   - Specific tactics

3. ALTERNATIVE APPROACH
   - If too strong, what adjacent opportunities exist?
   - How to avoid direct competition?

4. RESOURCE ALLOCATION
   - Where to invest?
   - What NOT to waste money on?

Be brutally honest. If they're too strong, say so clearly.
        """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="competitive_moat",
            use_complex_model=True  # Complex strategic analysis
        )

        return ai_result
