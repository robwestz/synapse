"""
MODE 1.3: Cluster Momentum Detector
Detects rising and falling clusters based on average position changes
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import defaultdict

from app.models.uploads import OrganicKeyword, Upload
from app.core.ai_engine import AIEngine


class ClusterMomentumDetector:
    """
    Identifies rising and falling clusters by analyzing average position changes
    across all keywords in each parent topic
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self) -> Dict[str, Any]:
        """
        Execute cluster momentum analysis
        """

        # Step 1: Get your keywords with position changes
        your_keywords = await self._get_keywords_with_changes(is_primary=True)

        # Step 2: Get competitor keywords with position changes
        competitor_keywords = await self._get_keywords_with_changes(is_primary=False)

        if not your_keywords and not competitor_keywords:
            return {
                "error": "No position change data found. Upload Organic Keywords report with historical data."
            }

        # Step 3: Calculate momentum per cluster for your site
        your_momentum = self._calculate_cluster_momentum(your_keywords)

        # Step 4: Calculate momentum per cluster for competitors
        competitor_momentum = self._calculate_cluster_momentum(competitor_keywords)

        # Step 5: Identify rising and falling clusters
        analysis = self._analyze_momentum(your_momentum, competitor_momentum)

        # Step 6: Generate AI strategic insight
        ai_insight = await self._generate_ai_insight(analysis)

        return {
            "mode": "1.3_cluster_momentum",
            "status": "completed",
            "summary": {
                "your_rising_clusters": len(analysis['your_rising']),
                "your_falling_clusters": len(analysis['your_falling']),
                "competitor_rising_clusters": len(analysis['competitor_rising']),
                "urgent_attention_needed": len(analysis['urgent_threats']),
            },
            "your_rising_clusters": analysis['your_rising'],
            "your_falling_clusters": analysis['your_falling'],
            "competitor_rising_clusters": analysis['competitor_rising'],
            "urgent_threats": analysis['urgent_threats'],
            "ai_insight": ai_insight,
        }

    async def _get_keywords_with_changes(self, is_primary: bool) -> List[Dict]:
        """
        Get keywords that have position change data
        """
        query = (
            select(OrganicKeyword, Upload.source_domain)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.is_primary == is_primary)
            .where(Upload.processing_status == "completed")
            .where(OrganicKeyword.position.isnot(None))
            .where(OrganicKeyword.position_change.isnot(None))
            .where(OrganicKeyword.parent_topic.isnot(None))
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        keywords = []
        for row in rows:
            kw_obj, domain = row
            keywords.append({
                "keyword": kw_obj.keyword,
                "parent_topic": kw_obj.parent_topic,
                "position": kw_obj.position,
                "previous_position": kw_obj.previous_position,
                "position_change": kw_obj.position_change,
                "volume": kw_obj.volume or 0,
                "domain": domain,
            })

        return keywords

    def _calculate_cluster_momentum(self, keywords: List[Dict]) -> Dict[str, Dict]:
        """
        Calculate momentum score for each cluster

        Momentum = average position change across all keywords
        Positive = rising (improving positions)
        Negative = falling (losing positions)
        """
        cluster_data = defaultdict(lambda: {
            'position_changes': [],
            'keywords': [],
            'total_volume': 0,
            'avg_position': [],
        })

        for kw in keywords:
            topic = kw['parent_topic']
            cluster_data[topic]['position_changes'].append(kw['position_change'])
            cluster_data[topic]['keywords'].append(kw['keyword'])
            cluster_data[topic]['total_volume'] += kw['volume']
            cluster_data[topic]['avg_position'].append(kw['position'])

        # Calculate momentum scores
        momentum = {}
        for topic, data in cluster_data.items():
            # Positive change = improving (moving UP in rankings = LOWER position numbers)
            # Position change from Ahrefs: negative = improvement
            avg_change = sum(data['position_changes']) / len(data['position_changes'])

            momentum[topic] = {
                'momentum_score': -avg_change,  # Invert: positive score = good
                'avg_position_change': avg_change,
                'keyword_count': len(data['keywords']),
                'total_volume': data['total_volume'],
                'avg_position': sum(data['avg_position']) / len(data['avg_position']),
                'sample_keywords': data['keywords'][:5],
            }

        return momentum

    def _analyze_momentum(
        self,
        your_momentum: Dict[str, Dict],
        competitor_momentum: Dict[str, Dict]
    ) -> Dict:
        """
        Compare your momentum vs competitors and identify opportunities/threats
        """

        # Rising: momentum score >= +5 (avg +5 position improvement)
        # Falling: momentum score <= -5 (avg -5 position loss)

        your_rising = []
        your_falling = []
        competitor_rising = []
        urgent_threats = []

        # Analyze your clusters
        for topic, data in your_momentum.items():
            cluster_info = {
                'parent_topic': topic,
                **data
            }

            if data['momentum_score'] >= 5:
                your_rising.append(cluster_info)
            elif data['momentum_score'] <= -5:
                your_falling.append(cluster_info)

                # Check if competitors are rising in the same cluster
                if topic in competitor_momentum:
                    comp_score = competitor_momentum[topic]['momentum_score']
                    if comp_score >= 5:
                        # URGENT: You're falling, they're rising
                        urgent_threats.append({
                            **cluster_info,
                            'competitor_momentum': comp_score,
                            'threat_level': 'CRITICAL',
                            'recommendation': 'Immediate content refresh needed',
                        })

        # Analyze competitor clusters
        for topic, data in competitor_momentum.items():
            if data['momentum_score'] >= 5:
                competitor_rising.append({
                    'parent_topic': topic,
                    **data
                })

        # Sort by momentum score
        your_rising.sort(key=lambda x: x['momentum_score'], reverse=True)
        your_falling.sort(key=lambda x: x['momentum_score'])
        competitor_rising.sort(key=lambda x: x['momentum_score'], reverse=True)
        urgent_threats.sort(key=lambda x: x['competitor_momentum'], reverse=True)

        return {
            'your_rising': your_rising[:20],
            'your_falling': your_falling[:20],
            'competitor_rising': competitor_rising[:20],
            'urgent_threats': urgent_threats[:10],
        }

    async def _generate_ai_insight(self, analysis: Dict) -> Dict:
        """
        Generate AI strategic recommendations based on momentum analysis
        """

        # Format data for AI
        rising_clusters = "\n".join([
            f"- {c['parent_topic']}: +{c['momentum_score']:.1f} avg improvement ({c['keyword_count']} keywords)"
            for c in analysis['your_rising'][:5]
        ]) if analysis['your_rising'] else "None"

        falling_clusters = "\n".join([
            f"- {c['parent_topic']}: {c['momentum_score']:.1f} avg decline ({c['keyword_count']} keywords)"
            for c in analysis['your_falling'][:5]
        ]) if analysis['your_falling'] else "None"

        threats = "\n".join([
            f"- {t['parent_topic']}: You're falling ({t['momentum_score']:.1f}), competitor rising (+{t['competitor_momentum']:.1f})"
            for t in analysis['urgent_threats'][:5]
        ]) if analysis['urgent_threats'] else "None"

        prompt = f"""
Analyze this cluster momentum data:

YOUR RISING CLUSTERS (Winning):
{rising_clusters}

YOUR FALLING CLUSTERS (Losing):
{falling_clusters}

URGENT THREATS (Competitor gaining while you lose):
{threats}

Provide:

1. MOMENTUM DIAGNOSIS
   - What's working? (why are some clusters rising?)
   - What's failing? (why are some clusters falling?)

2. URGENT ACTION PLAN
   - Which falling clusters to fix immediately?
   - Specific actions for top 3 threats

3. GROWTH STRATEGY
   - How to accelerate rising clusters?
   - Should you invest more in winners or fix losers?

4. COMPETITIVE RESPONSE
   - What are competitors doing right in rising clusters?
   - How to defend against their momentum?

Be specific and actionable. Focus on the WHY behind momentum.
        """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="cluster_momentum",
            use_complex_model=True  # Complex strategic analysis
        )

        return ai_result
