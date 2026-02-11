"""
MODE 1.1: Parent Topic Coverage Map
Identifies which parent topics are dominated by competitors vs you
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import defaultdict

from app.models.uploads import OrganicKeyword, Upload
from app.core.ai_engine import AIEngine, PromptTemplates


class ClusterDominanceAnalyzer:
    """
    Analyzes parent topic coverage to find cluster dominance gaps
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self) -> Dict[str, Any]:
        """
        Execute cluster dominance analysis
        """

        # Step 1: Get your organic keywords
        your_keywords = await self._get_organic_keywords(is_primary=True)

        if not your_keywords:
            return {
                "error": "No primary site data found. Upload your Organic Keywords first."
            }

        # Step 2: Get competitor organic keywords
        competitor_keywords = await self._get_organic_keywords(is_primary=False)

        if not competitor_keywords:
            return {
                "error": "No competitor data found. Upload competitor Organic Keywords."
            }

        # Step 3: Group by parent topic
        your_clusters = self._group_by_parent_topic(your_keywords)
        competitor_clusters = self._group_by_parent_topic(competitor_keywords)

        # Step 4: Calculate coverage for each cluster
        analysis = await self._calculate_cluster_coverage(
            your_clusters,
            competitor_clusters
        )

        # Step 5: Sort by opportunity score
        analysis.sort(key=lambda x: x['opportunity_score'], reverse=True)

        # Step 6: Get AI insights for top opportunities
        top_opportunities = analysis[:5]
        ai_insight = await self._generate_ai_insight(
            your_clusters,
            competitor_clusters,
            top_opportunities
        )

        # Step 7: Build result
        return {
            "mode": "1.1_cluster_dominance",
            "status": "completed",
            "summary": {
                "total_clusters_analyzed": len(analysis),
                "clusters_you_dominate": len([a for a in analysis if a['your_coverage'] > 60]),
                "clusters_competitor_dominates": len([a for a in analysis if a['competitor_coverage'] > 60]),
                "highest_opportunity": top_opportunities[0]['parent_topic'] if top_opportunities else None,
            },
            "top_opportunities": top_opportunities,
            "full_analysis": analysis,
            "ai_insight": ai_insight,
        }

    async def _get_organic_keywords(self, is_primary: bool) -> List[Dict]:
        """
        Get organic keywords from database
        """
        query = (
            select(OrganicKeyword, Upload.source_domain)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.is_primary == is_primary)
            .where(Upload.processing_status == "completed")
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        keywords = []
        for row in rows:
            keyword_obj, domain = row
            keywords.append({
                "keyword": keyword_obj.keyword,
                "parent_topic": keyword_obj.parent_topic,
                "volume": keyword_obj.volume,
                "position": keyword_obj.position,
                "traffic": keyword_obj.traffic,
                "domain": domain,
            })

        return keywords

    def _group_by_parent_topic(self, keywords: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group keywords by parent topic
        """
        clusters = defaultdict(list)

        for kw in keywords:
            parent_topic = kw.get('parent_topic', 'Unknown')
            if parent_topic and parent_topic != 'Unknown':
                clusters[parent_topic].append(kw)

        return dict(clusters)

    async def _calculate_cluster_coverage(
        self,
        your_clusters: Dict,
        competitor_clusters: Dict
    ) -> List[Dict]:
        """
        Calculate coverage percentage for each parent topic
        """
        analysis = []

        # Get all unique parent topics
        all_topics = set(your_clusters.keys()) | set(competitor_clusters.keys())

        for topic in all_topics:
            your_keywords = your_clusters.get(topic, [])
            competitor_keywords = competitor_clusters.get(topic, [])

            your_count = len(your_keywords)
            competitor_count = len(competitor_keywords)
            total_keywords = your_count + competitor_count

            # Calculate coverage
            your_coverage = (your_count / total_keywords * 100) if total_keywords > 0 else 0
            competitor_coverage = (competitor_count / total_keywords * 100) if total_keywords > 0 else 0

            # Calculate total traffic potential
            your_traffic = sum(kw.get('traffic', 0) or 0 for kw in your_keywords)
            competitor_traffic = sum(kw.get('traffic', 0) or 0 for kw in competitor_keywords)

            # Calculate opportunity score
            # High opportunity = competitor dominates, you don't
            opportunity_score = self._calculate_opportunity_score(
                your_coverage,
                competitor_coverage,
                competitor_traffic
            )

            analysis.append({
                "parent_topic": topic,
                "your_keywords_count": your_count,
                "competitor_keywords_count": competitor_count,
                "total_keywords": total_keywords,
                "your_coverage_percent": round(your_coverage, 1),
                "competitor_coverage_percent": round(competitor_coverage, 1),
                "your_traffic_current": round(your_traffic, 0),
                "competitor_traffic": round(competitor_traffic, 0),
                "traffic_potential_multiplier": round(competitor_traffic / your_traffic, 1) if your_traffic > 0 else 0,
                "opportunity_score": round(opportunity_score, 2),
            })

        return analysis

    def _calculate_opportunity_score(
        self,
        your_coverage: float,
        competitor_coverage: float,
        competitor_traffic: float
    ) -> float:
        """
        Calculate opportunity score (0-100)

        High score means:
        - Competitor has high coverage (>60%)
        - You have low coverage (<20%)
        - High traffic potential
        """
        score = 0

        # Coverage gap (max 50 points)
        coverage_gap = competitor_coverage - your_coverage
        if coverage_gap > 60:
            score += 50
        elif coverage_gap > 40:
            score += 35
        elif coverage_gap > 20:
            score += 20

        # Traffic potential (max 30 points)
        if competitor_traffic > 10000:
            score += 30
        elif competitor_traffic > 5000:
            score += 20
        elif competitor_traffic > 1000:
            score += 10

        # Your current position (max 20 points)
        # Bonus if you already have SOME presence (easier to expand)
        if 5 < your_coverage < 30:
            score += 20
        elif your_coverage < 5:
            score += 10

        return score

    async def _generate_ai_insight(
        self,
        your_clusters: Dict,
        competitor_clusters: Dict,
        top_opportunities: List[Dict]
    ) -> Dict:
        """
        Generate AI-powered strategic insight
        """

        # Build context for AI
        context = {
            "your_total_clusters": len(your_clusters),
            "competitor_total_clusters": len(competitor_clusters),
            "top_opportunities": top_opportunities,
        }

        # Generate prompt
        prompt = PromptTemplates.cluster_dominance(
            your_clusters={k: len(v) for k, v in list(your_clusters.items())[:20]},
            competitor_clusters={k: len(v) for k, v in list(competitor_clusters.items())[:20]}
        )

        # Call AI
        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="cluster_dominance",
            context=context,
            use_complex_model=True  # Use Opus for strategic analysis
        )

        return ai_result
