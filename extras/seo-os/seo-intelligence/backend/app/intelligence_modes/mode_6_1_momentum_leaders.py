"""
MODE 6.1: Momentum Leaders
Identifies competitors with strong ranking momentum (many improving positions)
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import defaultdict

from app.models.uploads import OrganicKeyword, Upload
from app.core.ai_engine import AIEngine


class MomentumLeadersAnalyzer:
    """
    Tracks competitive evolution by identifying who's gaining momentum

    Momentum = aggregate position improvements across keywords
    Leaders = competitors improving 100+ keywords
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self) -> Dict[str, Any]:
        """
        Execute momentum leaders analysis
        """

        # Step 1: Get all keywords with position changes by domain
        domain_momentum = await self._calculate_domain_momentum()

        if not domain_momentum:
            return {
                "error": "No position change data found. Upload Organic Keywords with historical data."
            }

        # Step 2: Rank domains by momentum
        momentum_leaders = self._rank_by_momentum(domain_momentum)

        # Step 3: Analyze what's working for leaders
        leader_strategies = await self._analyze_leader_strategies(momentum_leaders[:5])

        # Step 4: Generate AI insight
        ai_insight = await self._generate_ai_insight(momentum_leaders, leader_strategies)

        return {
            "mode": "6.1_momentum_leaders",
            "status": "completed",
            "summary": {
                "total_domains_analyzed": len(momentum_leaders),
                "top_momentum_leader": momentum_leaders[0]['domain'] if momentum_leaders else None,
                "keywords_improving_leader": momentum_leaders[0]['improving_keywords'] if momentum_leaders else 0,
            },
            "momentum_leaders": momentum_leaders[:20],
            "leader_strategies": leader_strategies,
            "ai_insight": ai_insight,
        }

    async def _calculate_domain_momentum(self) -> Dict[str, Dict]:
        """
        Calculate momentum metrics for each domain
        """
        query = (
            select(OrganicKeyword, Upload.source_domain, Upload.is_primary)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.processing_status == "completed")
            .where(OrganicKeyword.position_change.isnot(None))
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        # Group by domain
        domain_data = defaultdict(lambda: {
            'improving': [],
            'declining': [],
            'stable': [],
            'is_primary': False,
        })

        for row in rows:
            kw_obj, domain, is_primary = row
            change = kw_obj.position_change

            domain_data[domain]['is_primary'] = is_primary

            if change < -1:  # Improving (negative = moving up)
                domain_data[domain]['improving'].append({
                    'keyword': kw_obj.keyword,
                    'change': change,
                    'volume': kw_obj.volume or 0,
                    'current_position': kw_obj.position,
                })
            elif change > 1:  # Declining (positive = moving down)
                domain_data[domain]['declining'].append({
                    'keyword': kw_obj.keyword,
                    'change': change,
                    'volume': kw_obj.volume or 0,
                })
            else:  # Stable (±1 position)
                domain_data[domain]['stable'].append({
                    'keyword': kw_obj.keyword,
                })

        return dict(domain_data)

    def _rank_by_momentum(self, domain_data: Dict[str, Dict]) -> List[Dict]:
        """
        Rank domains by momentum score
        """
        rankings = []

        for domain, data in domain_data.items():
            improving_count = len(data['improving'])
            declining_count = len(data['declining'])
            stable_count = len(data['stable'])

            total_keywords = improving_count + declining_count + stable_count

            # Momentum score: net improvements
            momentum_score = improving_count - declining_count

            # Calculate average improvement magnitude
            if data['improving']:
                avg_improvement = sum(abs(k['change']) for k in data['improving']) / len(data['improving'])
            else:
                avg_improvement = 0

            # Total traffic impact from improvements
            traffic_impact = sum(k['volume'] for k in data['improving'])

            rankings.append({
                'domain': domain,
                'is_your_site': data['is_primary'],
                'improving_keywords': improving_count,
                'declining_keywords': declining_count,
                'stable_keywords': stable_count,
                'total_keywords': total_keywords,
                'net_momentum_score': momentum_score,
                'improving_percent': round(improving_count / total_keywords * 100, 1) if total_keywords > 0 else 0,
                'avg_improvement_magnitude': round(avg_improvement, 1),
                'traffic_impact': traffic_impact,
                'momentum_classification': self._classify_momentum(momentum_score, improving_count),
                'top_improvements': sorted(data['improving'], key=lambda x: abs(x['change']), reverse=True)[:10],
            })

        # Sort by momentum score
        rankings.sort(key=lambda x: x['net_momentum_score'], reverse=True)

        return rankings

    def _classify_momentum(self, net_score: int, improving_count: int) -> str:
        """
        Classify momentum level
        """
        if net_score >= 200 and improving_count >= 250:
            return "🚀 EXPLOSIVE GROWTH"
        elif net_score >= 100 and improving_count >= 150:
            return "📈 STRONG MOMENTUM"
        elif net_score >= 50:
            return "↗️ POSITIVE MOMENTUM"
        elif net_score >= 0:
            return "➡️ STABLE"
        elif net_score >= -50:
            return "↘️ SLIGHT DECLINE"
        else:
            return "📉 DECLINING"

    async def _analyze_leader_strategies(self, leaders: List[Dict]) -> List[Dict]:
        """
        Analyze what top momentum leaders are doing right
        """
        strategies = []

        for leader in leaders:
            # Analyze their top improvements
            top_improvements = leader['top_improvements']

            # Find patterns in their improvements
            common_topics = defaultdict(int)
            position_gains = []

            for imp in top_improvements:
                # Extract topic patterns (simplified - in real implementation would use parent_topic)
                position_gains.append(abs(imp['change']))

            avg_gain = sum(position_gains) / len(position_gains) if position_gains else 0

            strategies.append({
                'domain': leader['domain'],
                'total_improvements': leader['improving_keywords'],
                'avg_position_gain': round(avg_gain, 1),
                'strategy_hypothesis': self._hypothesize_strategy(leader, avg_gain),
            })

        return strategies

    def _hypothesize_strategy(self, leader: Dict, avg_gain: float) -> str:
        """
        Hypothesize what strategy the leader is using
        """
        improving = leader['improving_keywords']
        avg_magnitude = leader['avg_improvement_magnitude']

        if improving > 200 and avg_magnitude > 5:
            return "MAJOR SITE REFRESH - Likely updated large portions of content or fixed technical issues"
        elif improving > 100 and avg_magnitude > 3:
            return "CONTENT UPDATE CAMPAIGN - Systematically updating existing content"
        elif improving > 50 and avg_magnitude < 3:
            return "INCREMENTAL OPTIMIZATION - Small improvements across many pages"
        elif avg_magnitude > 7:
            return "NEW CONTENT STRATEGY - Publishing new high-quality content"
        else:
            return "UNKNOWN STRATEGY - Investigate further"

    async def _generate_ai_insight(
        self,
        leaders: List[Dict],
        strategies: List[Dict]
    ) -> Dict:
        """
        Generate AI strategic insight on momentum leaders
        """

        # Find your site's ranking
        your_ranking = next((i+1 for i, l in enumerate(leaders) if l['is_your_site']), None)
        your_data = next((l for l in leaders if l['is_your_site']), None)

        top_leader = leaders[0] if leaders else None

        leader_summary = "\n".join([
            f"{i+1}. {l['domain']}: {l['improving_keywords']} improving, {l['net_momentum_score']} net score ({l['momentum_classification']})"
            for i, l in enumerate(leaders[:10])
        ])

        strategy_summary = "\n".join([
            f"- {s['domain']}: {s['strategy_hypothesis']}"
            for s in strategies
        ])

        your_status = f"\nYOUR RANKING: #{your_ranking} - {your_data['improving_keywords']} improving, {your_data['net_momentum_score']} net" if your_data else "\nYOUR SITE: Not in rankings"

        prompt = f"""
Analyze this momentum leaders analysis:

TOP 10 MOMENTUM LEADERS:
{leader_summary}
{your_status}

STRATEGY HYPOTHESES:
{strategy_summary}

Provide:

1. COMPETITIVE MOMENTUM ANALYSIS
   - Who's winning the momentum race?
   - What strategies are working?

2. THREAT ASSESSMENT
   - Which leaders pose immediate threats?
   - What are they doing right?

3. STRATEGIC RESPONSE
   - How to match or exceed their momentum?
   - What to copy, what to avoid?

4. YOUR MOMENTUM PLAN
   - How to move up in momentum rankings?
   - What's the fastest path to positive momentum?

Be specific about what actions drive momentum and what to copy from leaders.
        """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="momentum_leaders",
            use_complex_model=True
        )

        return ai_result
