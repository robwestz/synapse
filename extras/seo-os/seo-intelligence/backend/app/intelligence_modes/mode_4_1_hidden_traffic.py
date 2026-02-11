"""
MODE 4.1: Hidden Traffic Clusters
Identifies parent topics where competitors dominate but you have minimal presence
Calculates traffic potential if you achieved similar coverage
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import defaultdict

from app.models.uploads import OrganicKeyword, Upload
from app.core.ai_engine import AIEngine


class HiddenTrafficClusters:
    """
    Finds clusters where:
    - Competitor ranks for 80%+ of keywords
    - You rank for <20% of keywords
    - High traffic potential exists

    These are "hidden" traffic opportunities - entire topics you're missing
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self) -> Dict[str, Any]:
        """
        Execute hidden traffic cluster analysis
        """

        # Step 1: Get all keywords by topic
        all_keywords_by_topic = await self._get_keywords_by_topic()

        if not all_keywords_by_topic:
            return {
                "error": "No keyword data found. Upload Organic Keywords reports."
            }

        # Step 2: Calculate coverage and traffic per topic
        cluster_analysis = self._analyze_clusters(all_keywords_by_topic)

        # Step 3: Identify hidden opportunities
        hidden_opportunities = self._find_hidden_opportunities(cluster_analysis)

        # Step 4: Calculate traffic potential
        opportunities_with_potential = self._calculate_traffic_potential(hidden_opportunities)

        # Step 5: Generate AI insight
        ai_insight = await self._generate_ai_insight(opportunities_with_potential[:20])

        return {
            "mode": "4.1_hidden_traffic_clusters",
            "status": "completed",
            "summary": {
                "total_clusters_analyzed": len(cluster_analysis),
                "hidden_opportunities": len(opportunities_with_potential),
                "total_traffic_potential": sum(o['traffic_potential'] for o in opportunities_with_potential),
                "avg_opportunity_size": round(sum(o['traffic_potential'] for o in opportunities_with_potential) / len(opportunities_with_potential), 0) if opportunities_with_potential else 0,
            },
            "hidden_opportunities": opportunities_with_potential[:50],
            "all_clusters": cluster_analysis[:100],
            "ai_insight": ai_insight,
        }

    async def _get_keywords_by_topic(self) -> Dict[str, Dict]:
        """
        Get all keywords grouped by parent topic
        """
        query = (
            select(OrganicKeyword, Upload.is_primary, Upload.source_domain)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.processing_status == "completed")
            .where(OrganicKeyword.parent_topic.isnot(None))
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        # Group by topic
        topics = defaultdict(lambda: {
            'all_keywords': [],
            'your_keywords': [],
            'competitor_keywords': [],
        })

        for row in rows:
            kw_obj, is_primary, domain = row

            keyword_data = {
                'keyword': kw_obj.keyword,
                'position': kw_obj.position,
                'volume': kw_obj.volume or 0,
                'traffic': kw_obj.traffic or 0,
                'domain': domain,
            }

            topic = kw_obj.parent_topic
            topics[topic]['all_keywords'].append(keyword_data)

            if is_primary:
                topics[topic]['your_keywords'].append(keyword_data)
            else:
                topics[topic]['competitor_keywords'].append(keyword_data)

        return dict(topics)

    def _analyze_clusters(self, topics: Dict[str, Dict]) -> List[Dict]:
        """
        Analyze each cluster for coverage and traffic
        """
        analysis = []

        for topic_name, data in topics.items():
            total_keywords = len(data['all_keywords'])
            your_count = len(data['your_keywords'])
            competitor_count = len(data['competitor_keywords'])

            if total_keywords == 0:
                continue

            your_coverage = (your_count / total_keywords) * 100
            competitor_coverage = (competitor_count / total_keywords) * 100

            # Traffic calculations
            your_traffic = sum(k['traffic'] for k in data['your_keywords'])
            competitor_traffic = sum(k['traffic'] for k in data['competitor_keywords'])
            total_volume = sum(k['volume'] for k in data['all_keywords'])

            analysis.append({
                'parent_topic': topic_name,
                'total_keywords': total_keywords,
                'your_keywords': your_count,
                'competitor_keywords': competitor_count,
                'your_coverage_percent': round(your_coverage, 1),
                'competitor_coverage_percent': round(competitor_coverage, 1),
                'coverage_gap': round(competitor_coverage - your_coverage, 1),
                'your_current_traffic': round(your_traffic, 0),
                'competitor_traffic': round(competitor_traffic, 0),
                'total_search_volume': total_volume,
            })

        # Sort by coverage gap
        analysis.sort(key=lambda x: x['coverage_gap'], reverse=True)

        return analysis

    def _find_hidden_opportunities(self, clusters: List[Dict]) -> List[Dict]:
        """
        Find clusters that are "hidden opportunities"

        Criteria:
        - Competitor coverage >= 60%
        - Your coverage <= 20%
        - Total search volume >= 5000
        """
        opportunities = []

        for cluster in clusters:
            if (cluster['competitor_coverage_percent'] >= 60 and
                cluster['your_coverage_percent'] <= 20 and
                cluster['total_search_volume'] >= 5000):

                opportunities.append(cluster)

        return opportunities

    def _calculate_traffic_potential(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Calculate traffic potential if you achieve similar coverage as competitors
        """
        enhanced_opportunities = []

        for opp in opportunities:
            # Current state
            current_traffic = opp['your_current_traffic']

            # Potential if you match competitor coverage
            # Assume: if you go from X% to Y% coverage, traffic scales proportionally
            current_coverage = opp['your_coverage_percent']
            target_coverage = opp['competitor_coverage_percent']

            if current_coverage > 0:
                traffic_multiplier = target_coverage / current_coverage
            else:
                # If no current coverage, estimate based on competitor traffic
                traffic_multiplier = float('inf')
                potential_traffic = opp['competitor_traffic']

            if traffic_multiplier != float('inf'):
                potential_traffic = current_traffic * traffic_multiplier

            traffic_gain = potential_traffic - current_traffic

            # Calculate opportunity score
            opportunity_score = self._calculate_opportunity_score(
                traffic_gain,
                opp['coverage_gap'],
                opp['total_keywords']
            )

            enhanced_opportunities.append({
                **opp,
                'current_traffic': current_traffic,
                'potential_traffic': round(potential_traffic, 0),
                'traffic_potential': round(traffic_gain, 0),
                'traffic_multiplier': round(traffic_multiplier, 1) if traffic_multiplier != float('inf') else 999,
                'opportunity_score': opportunity_score,
                'effort_estimate': self._estimate_effort(opp['total_keywords'], opp['your_keywords']),
            })

        # Sort by opportunity score
        enhanced_opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)

        return enhanced_opportunities

    def _calculate_opportunity_score(
        self,
        traffic_gain: float,
        coverage_gap: float,
        total_keywords: int
    ) -> float:
        """
        Calculate opportunity score (0-100)

        Higher score = better opportunity
        """
        score = 0

        # Traffic potential component (max 50 points)
        if traffic_gain >= 10000:
            score += 50
        elif traffic_gain >= 5000:
            score += 40
        elif traffic_gain >= 2000:
            score += 30
        elif traffic_gain >= 1000:
            score += 20
        else:
            score += 10

        # Coverage gap component (max 30 points)
        if coverage_gap >= 80:
            score += 30
        elif coverage_gap >= 60:
            score += 25
        elif coverage_gap >= 40:
            score += 20
        else:
            score += 10

        # Keyword count component (max 20 points)
        # More keywords = more established cluster = better opportunity
        if total_keywords >= 200:
            score += 20
        elif total_keywords >= 100:
            score += 15
        elif total_keywords >= 50:
            score += 10
        else:
            score += 5

        return round(score, 1)

    def _estimate_effort(self, total_keywords: int, your_current: int) -> Dict:
        """
        Estimate effort to achieve competitor-level coverage
        """
        missing_keywords = total_keywords - your_current

        # Estimate articles needed (assume each article targets 10-20 keywords)
        articles_needed = int(missing_keywords / 15)

        # Estimate time (assume 1 article per week)
        weeks_needed = articles_needed

        return {
            'missing_keywords': missing_keywords,
            'articles_needed': articles_needed,
            'estimated_weeks': weeks_needed,
            'effort_level': self._classify_effort(articles_needed),
        }

    def _classify_effort(self, articles: int) -> str:
        """
        Classify effort level
        """
        if articles <= 5:
            return "LOW EFFORT"
        elif articles <= 15:
            return "MODERATE EFFORT"
        elif articles <= 30:
            return "HIGH EFFORT"
        else:
            return "VERY HIGH EFFORT"

    async def _generate_ai_insight(self, opportunities: List[Dict]) -> Dict:
        """
        Generate AI strategic insight
        """

        if not opportunities:
            prompt = "No hidden traffic clusters found. You have good topic coverage."
        else:
            top_opportunities = "\n".join([
                f"- {o['parent_topic']}: +{o['traffic_potential']:,.0f} traffic potential ({o['coverage_gap']:.0f}% gap, {o['articles_needed']} articles needed)"
                for o in opportunities[:10]
            ])

            prompt = f"""
Analyze these hidden traffic cluster opportunities:

TOP OPPORTUNITIES:
{top_opportunities}

These are entire topics where competitors dominate and you're nearly absent.

Provide:

1. STRATEGIC PRIORITY RANKING
   - Which clusters to target first?
   - Why these over others?

2. CONTENT STRATEGY
   - Hub-and-spoke vs. comprehensive guide approach?
   - How many articles per cluster?
   - Sequencing strategy?

3. RESOURCE ALLOCATION
   - How to allocate budget across clusters?
   - Quick wins vs. long-term plays?

4. EXECUTION ROADMAP
   - Month 1-3: Which clusters?
   - Month 4-6: What's next?
   - Year 1 goal: Total traffic gain?

Be specific about which topics to attack and in what order.
            """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="hidden_traffic_clusters",
            use_complex_model=True
        )

        return ai_result
