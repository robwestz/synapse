"""
MODE 7.1: Comprehensive Competitor Profile
Synthesizes ALL uploaded reports into complete competitor intelligence profile
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.uploads import (
    OrganicKeyword,
    Backlink,
    ReferringDomain,
    SERPOverview,
    Upload
)
from app.core.ai_engine import AIEngine


class ComprehensiveCompetitorProfiler:
    """
    Builds complete competitor profile from all available data sources

    Synthesizes:
    - Content strategy (from organic keywords)
    - Link acquisition patterns (from backlinks)
    - SERP dominance (from SERP overview)
    - Growth trajectory (from position changes)
    - Internal linking structure (if available)
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self, competitor_domain: str) -> Dict[str, Any]:
        """
        Build comprehensive profile for specific competitor
        """

        # Step 1: Get all upload IDs for this competitor
        competitor_uploads = await self._get_competitor_uploads(competitor_domain)

        if not competitor_uploads:
            return {
                "error": f"No data found for competitor: {competitor_domain}"
            }

        # Step 2: Analyze content strategy
        content_strategy = await self._analyze_content_strategy(competitor_uploads)

        # Step 3: Analyze link acquisition
        link_strategy = await self._analyze_link_strategy(competitor_uploads)

        # Step 4: Analyze SERP presence
        serp_dominance = await self._analyze_serp_dominance(competitor_uploads)

        # Step 5: Analyze growth trajectory
        growth_trajectory = await self._analyze_growth(competitor_uploads)

        # Step 6: Generate strategic synthesis
        strategic_profile = {
            'competitor_domain': competitor_domain,
            'content_strategy': content_strategy,
            'link_acquisition_strategy': link_strategy,
            'serp_dominance': serp_dominance,
            'growth_trajectory': growth_trajectory,
            'overall_strength_score': self._calculate_strength_score(
                content_strategy,
                link_strategy,
                serp_dominance,
                growth_trajectory
            ),
        }

        # Step 7: Generate AI strategic insight
        ai_insight = await self._generate_ai_insight(strategic_profile)

        return {
            "mode": "7.1_competitor_profile",
            "status": "completed",
            "competitor_domain": competitor_domain,
            "profile": strategic_profile,
            "ai_insight": ai_insight,
        }

    async def _get_competitor_uploads(self, domain: str) -> List[str]:
        """
        Get all upload IDs for this competitor
        """
        query = (
            select(Upload.id, Upload.report_type)
            .where(Upload.user_id == self.user_id)
            .where(Upload.source_domain == domain)
            .where(Upload.is_primary == False)
            .where(Upload.processing_status == "completed")
        )

        result = await self.session.execute(query)
        uploads = result.fetchall()

        return [str(row[0]) for row in uploads]

    async def _analyze_content_strategy(self, upload_ids: List[str]) -> Dict:
        """
        Analyze content strategy from organic keywords
        """
        query = (
            select(
                func.count(OrganicKeyword.id).label('total_keywords'),
                func.count(func.distinct(OrganicKeyword.parent_topic)).label('total_topics'),
                func.avg(OrganicKeyword.position).label('avg_position'),
                func.sum(OrganicKeyword.traffic).label('total_traffic'),
                func.sum(OrganicKeyword.volume).label('total_volume'),
            )
            .where(OrganicKeyword.upload_id.in_(upload_ids))
        )

        result = await self.session.execute(query)
        stats = result.fetchone()

        # Get top topics
        topic_query = (
            select(
                OrganicKeyword.parent_topic,
                func.count(OrganicKeyword.id).label('keyword_count'),
                func.sum(OrganicKeyword.traffic).label('traffic'),
            )
            .where(OrganicKeyword.upload_id.in_(upload_ids))
            .where(OrganicKeyword.parent_topic.isnot(None))
            .group_by(OrganicKeyword.parent_topic)
            .order_by(func.count(OrganicKeyword.id).desc())
            .limit(20)
        )

        topic_result = await self.session.execute(topic_query)
        topics = topic_result.fetchall()

        # Calculate content depth (keywords per topic)
        content_depth = stats.total_keywords / stats.total_topics if stats.total_topics > 0 else 0

        return {
            'total_ranking_keywords': stats.total_keywords or 0,
            'total_parent_topics': stats.total_topics or 0,
            'avg_ranking_position': round(stats.avg_position or 0, 1),
            'total_monthly_traffic': round(stats.total_traffic or 0, 0),
            'total_search_volume': stats.total_volume or 0,
            'content_depth_per_topic': round(content_depth, 1),
            'primary_topics': [
                {
                    'topic': t[0],
                    'keyword_count': t[1],
                    'traffic': round(t[2] or 0, 0),
                }
                for t in topics
            ],
            'content_strategy_type': self._classify_content_strategy(content_depth),
        }

    def _classify_content_strategy(self, depth: float) -> str:
        """
        Classify content strategy based on depth
        """
        if depth > 100:
            return "COMPREHENSIVE COVERAGE"
        elif depth > 50:
            return "DEEP TOPIC COVERAGE"
        elif depth > 20:
            return "MODERATE COVERAGE"
        else:
            return "BROAD BUT SHALLOW"

    async def _analyze_link_strategy(self, upload_ids: List[str]) -> Dict:
        """
        Analyze backlink acquisition strategy
        """
        # Referring domains stats
        domain_query = (
            select(
                func.count(ReferringDomain.id).label('total_domains'),
                func.avg(ReferringDomain.domain_rating).label('avg_dr'),
                func.sum(ReferringDomain.dofollow_linked_domains).label('total_dofollow'),
            )
            .where(ReferringDomain.upload_id.in_(upload_ids))
        )

        domain_result = await self.session.execute(domain_query)
        domain_stats = domain_result.fetchone()

        # Backlink stats
        backlink_query = (
            select(
                func.count(Backlink.id).label('total_backlinks'),
            )
            .where(Backlink.upload_id.in_(upload_ids))
        )

        backlink_result = await self.session.execute(backlink_query)
        backlink_stats = backlink_result.fetchone()

        # Top referring domains by DR
        top_domains_query = (
            select(
                ReferringDomain.referring_domain,
                ReferringDomain.domain_rating,
                ReferringDomain.dofollow_linked_domains,
            )
            .where(ReferringDomain.upload_id.in_(upload_ids))
            .where(ReferringDomain.domain_rating.isnot(None))
            .order_by(ReferringDomain.domain_rating.desc())
            .limit(20)
        )

        top_domains_result = await self.session.execute(top_domains_query)
        top_domains = top_domains_result.fetchall()

        return {
            'total_referring_domains': domain_stats.total_domains or 0,
            'total_backlinks': backlink_stats.total_backlinks or 0,
            'avg_domain_rating': round(domain_stats.avg_dr or 0, 1),
            'link_quality_score': self._calculate_link_quality(domain_stats.avg_dr),
            'top_referring_domains': [
                {
                    'domain': d[0],
                    'dr': d[1],
                    'dofollow_links': d[2] or 0,
                }
                for d in top_domains
            ],
        }

    def _calculate_link_quality(self, avg_dr: float) -> str:
        """
        Classify link quality based on average DR
        """
        if avg_dr >= 60:
            return "PREMIUM LINKS"
        elif avg_dr >= 40:
            return "QUALITY LINKS"
        elif avg_dr >= 20:
            return "MODERATE LINKS"
        else:
            return "LOW QUALITY LINKS"

    async def _analyze_serp_dominance(self, upload_ids: List[str]) -> Dict:
        """
        Analyze SERP feature presence and dominance
        """
        query = (
            select(
                func.count(SERPOverview.id).label('total_serp_results'),
                func.count(SERPOverview.id).filter(SERPOverview.position <= 3).label('top_3_positions'),
                func.count(SERPOverview.id).filter(SERPOverview.result_type == 'people also ask').label('paa_presence'),
            )
            .where(SERPOverview.upload_id.in_(upload_ids))
        )

        result = await self.session.execute(query)
        stats = result.fetchone()

        top_3_percent = (stats.top_3_positions / stats.total_serp_results * 100) if stats.total_serp_results > 0 else 0

        return {
            'total_serp_results': stats.total_serp_results or 0,
            'top_3_positions': stats.top_3_positions or 0,
            'top_3_percent': round(top_3_percent, 1),
            'paa_presence': stats.paa_presence or 0,
            'serp_strength': self._classify_serp_strength(top_3_percent),
        }

    def _classify_serp_strength(self, top_3_percent: float) -> str:
        """
        Classify SERP strength
        """
        if top_3_percent >= 50:
            return "DOMINANT"
        elif top_3_percent >= 30:
            return "STRONG"
        elif top_3_percent >= 15:
            return "MODERATE"
        else:
            return "WEAK"

    async def _analyze_growth(self, upload_ids: List[str]) -> Dict:
        """
        Analyze growth trajectory from position changes
        """
        query = (
            select(
                func.count(OrganicKeyword.id).filter(OrganicKeyword.position_change > 0).label('improving'),
                func.count(OrganicKeyword.id).filter(OrganicKeyword.position_change < 0).label('declining'),
                func.avg(OrganicKeyword.position_change).label('avg_change'),
            )
            .where(OrganicKeyword.upload_id.in_(upload_ids))
            .where(OrganicKeyword.position_change.isnot(None))
        )

        result = await self.session.execute(query)
        stats = result.fetchone()

        total = (stats.improving or 0) + (stats.declining or 0)
        improving_percent = (stats.improving / total * 100) if total > 0 else 0

        return {
            'keywords_improving': stats.improving or 0,
            'keywords_declining': stats.declining or 0,
            'avg_position_change': round(stats.avg_change or 0, 2),
            'improving_percent': round(improving_percent, 1),
            'trajectory': self._classify_trajectory(improving_percent),
        }

    def _classify_trajectory(self, improving_percent: float) -> str:
        """
        Classify growth trajectory
        """
        if improving_percent >= 60:
            return "STRONG GROWTH"
        elif improving_percent >= 45:
            return "MODERATE GROWTH"
        elif improving_percent >= 35:
            return "STABLE"
        else:
            return "DECLINING"

    def _calculate_strength_score(
        self,
        content: Dict,
        links: Dict,
        serp: Dict,
        growth: Dict
    ) -> Dict:
        """
        Calculate overall competitor strength score (0-100)
        """
        # Content strength (0-25)
        content_score = min((content['total_ranking_keywords'] / 1000) * 25, 25)

        # Link strength (0-25)
        link_score = min((links['avg_domain_rating'] / 70) * 25, 25)

        # SERP strength (0-25)
        serp_score = min((serp['top_3_percent'] / 50) * 25, 25)

        # Growth strength (0-25)
        growth_score = min((growth['improving_percent'] / 60) * 25, 25)

        overall = content_score + link_score + serp_score + growth_score

        return {
            'overall_score': round(overall, 1),
            'content_score': round(content_score, 1),
            'link_score': round(link_score, 1),
            'serp_score': round(serp_score, 1),
            'growth_score': round(growth_score, 1),
            'threat_level': self._classify_threat(overall),
        }

    def _classify_threat(self, score: float) -> str:
        """
        Classify competitive threat level
        """
        if score >= 80:
            return "EXTREME THREAT"
        elif score >= 60:
            return "HIGH THREAT"
        elif score >= 40:
            return "MODERATE THREAT"
        elif score >= 20:
            return "LOW THREAT"
        else:
            return "MINIMAL THREAT"

    async def _generate_ai_insight(self, profile: Dict) -> Dict:
        """
        Generate comprehensive strategic analysis
        """

        prompt = f"""
Analyze this comprehensive competitor profile:

COMPETITOR: {profile['competitor_domain']}

OVERALL STRENGTH: {profile['overall_strength_score']['overall_score']}/100 ({profile['overall_strength_score']['threat_level']})

CONTENT STRATEGY:
- {profile['content_strategy']['total_ranking_keywords']:,} ranking keywords
- {profile['content_strategy']['total_parent_topics']} parent topics
- {profile['content_strategy']['content_depth_per_topic']:.1f} keywords per topic
- Strategy type: {profile['content_strategy']['content_strategy_type']}

LINK STRATEGY:
- {profile['link_acquisition_strategy']['total_referring_domains']:,} referring domains
- Avg DR: {profile['link_acquisition_strategy']['avg_domain_rating']:.1f}
- Quality: {profile['link_acquisition_strategy']['link_quality_score']}

SERP DOMINANCE:
- {profile['serp_dominance']['top_3_percent']:.1f}% top 3 positions
- Strength: {profile['serp_dominance']['serp_strength']}

GROWTH TRAJECTORY:
- {profile['growth_trajectory']['improving_percent']:.1f}% keywords improving
- Trajectory: {profile['growth_trajectory']['trajectory']}

Provide:

1. COMPETITIVE THREAT ASSESSMENT
   - How dangerous is this competitor?
   - What are their biggest strengths?
   - What are their vulnerabilities?

2. STRATEGIC PATTERN ANALYSIS
   - What's their content playbook?
   - What's their link building approach?
   - What makes them successful?

3. ATTACK STRATEGY
   - Where to compete directly?
   - Where to avoid competition?
   - What weaknesses to exploit?

4. DEFENSIVE STRATEGY
   - What are they doing that you should replicate?
   - How to protect against their growth?

Be brutally honest about threat level and strategic recommendations.
        """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="comprehensive_competitor_profile",
            use_complex_model=True  # Complex multi-dimensional analysis
        )

        return ai_result
