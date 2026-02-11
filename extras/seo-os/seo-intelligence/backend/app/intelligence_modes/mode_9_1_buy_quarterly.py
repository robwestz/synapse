"""
MODE 9.1: "Buy Quarterly, Not Monthly" Calculator
Exposes how little SEO data actually changes month-to-month
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.models.uploads import OrganicKeyword, Upload
from app.core.ai_engine import AIEngine


class QuarterlyCalculator:
    """
    Calculates how much data stability exists to prove
    you don't need monthly Ahrefs subscription

    Exposes the "monthly subscription scam"
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self) -> Dict[str, Any]:
        """
        Calculate data stability and recommend subscription frequency
        """

        # Step 1: Get keywords with position changes
        keywords_with_changes = await self._get_keywords_with_changes()

        if not keywords_with_changes:
            return {
                "error": "No position change data found. Need historical data to calculate stability."
            }

        # Step 2: Calculate stability metrics
        stability_analysis = self._analyze_stability(keywords_with_changes)

        # Step 3: Calculate cost savings
        cost_analysis = self._calculate_cost_savings(stability_analysis)

        # Step 4: Generate AI insight
        ai_insight = await self._generate_ai_insight(stability_analysis, cost_analysis)

        return {
            "mode": "9.1_buy_quarterly_calculator",
            "status": "completed",
            "stability_analysis": stability_analysis,
            "cost_savings": cost_analysis,
            "recommendation": self._get_recommendation(stability_analysis),
            "ai_insight": ai_insight,
        }

    async def _get_keywords_with_changes(self) -> List[Dict]:
        """
        Get keywords with position change data
        """
        query = (
            select(OrganicKeyword)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.is_primary == True)
            .where(Upload.processing_status == "completed")
            .where(OrganicKeyword.position.isnot(None))
            .where(OrganicKeyword.position_change.isnot(None))
        )

        result = await self.session.execute(query)
        rows = result.scalars().all()

        keywords = []
        for kw in rows:
            keywords.append({
                "keyword": kw.keyword,
                "position": kw.position,
                "previous_position": kw.previous_position,
                "position_change": kw.position_change,
                "volume": kw.volume or 0,
            })

        return keywords

    def _analyze_stability(self, keywords: List[Dict]) -> Dict:
        """
        Analyze keyword position stability
        """
        total_keywords = len(keywords)

        # Classify by change magnitude
        no_change = [k for k in keywords if k['position_change'] == 0]
        minor_change = [k for k in keywords if abs(k['position_change']) <= 2 and k['position_change'] != 0]
        moderate_change = [k for k in keywords if 3 <= abs(k['position_change']) <= 5]
        major_change = [k for k in keywords if abs(k['position_change']) > 5]

        # Calculate percentages
        no_change_percent = len(no_change) / total_keywords * 100 if total_keywords > 0 else 0
        minor_change_percent = len(minor_change) / total_keywords * 100 if total_keywords > 0 else 0
        moderate_change_percent = len(moderate_change) / total_keywords * 100 if total_keywords > 0 else 0
        major_change_percent = len(major_change) / total_keywords * 100 if total_keywords > 0 else 0

        # Stable = no change + minor change
        stable_percent = no_change_percent + minor_change_percent

        return {
            'total_keywords': total_keywords,
            'no_change': {
                'count': len(no_change),
                'percent': round(no_change_percent, 1),
            },
            'minor_change_1_2_positions': {
                'count': len(minor_change),
                'percent': round(minor_change_percent, 1),
            },
            'moderate_change_3_5_positions': {
                'count': len(moderate_change),
                'percent': round(moderate_change_percent, 1),
            },
            'major_change_6_plus_positions': {
                'count': len(major_change),
                'percent': round(major_change_percent, 1),
            },
            'stable_keywords': {
                'count': len(no_change) + len(minor_change),
                'percent': round(stable_percent, 1),
            },
            'volatile_keywords': {
                'count': len(moderate_change) + len(major_change),
                'percent': round(100 - stable_percent, 1),
            },
        }

    def _calculate_cost_savings(self, stability: Dict) -> Dict:
        """
        Calculate how much money you save by buying quarterly vs monthly
        """
        # Ahrefs pricing
        MONTHLY_LITE = 129
        MONTHLY_STANDARD = 249
        MONTHLY_ADVANCED = 449
        MONTHLY_ENTERPRISE = 999

        stable_percent = stability['stable_keywords']['percent']

        # If >80% stable, quarterly is sufficient
        # If >90% stable, bi-annually is sufficient
        # If >95% stable, annually is sufficient

        if stable_percent >= 95:
            recommended_frequency = "ANNUALLY"
            months_between = 12
        elif stable_percent >= 90:
            recommended_frequency = "BI-ANNUALLY"
            months_between = 6
        elif stable_percent >= 80:
            recommended_frequency = "QUARTERLY"
            months_between = 3
        else:
            recommended_frequency = "BI-MONTHLY"
            months_between = 2

        # Calculate savings per tier
        savings = {}
        for tier_name, monthly_cost in [
            ("Lite ($129/mo)", MONTHLY_LITE),
            ("Standard ($249/mo)", MONTHLY_STANDARD),
            ("Advanced ($449/mo)", MONTHLY_ADVANCED),
            ("Enterprise ($999/mo)", MONTHLY_ENTERPRISE),
        ]:
            annual_cost_monthly = monthly_cost * 12
            annual_cost_recommended = monthly_cost * (12 / months_between)
            annual_savings = annual_cost_monthly - annual_cost_recommended

            savings[tier_name] = {
                'monthly_subscription_cost': f"${monthly_cost}/mo",
                'annual_cost_monthly': f"${annual_cost_monthly:,.0f}/year",
                'annual_cost_recommended': f"${annual_cost_recommended:,.0f}/year",
                'annual_savings': f"${annual_savings:,.0f}/year",
                'savings_percent': round(annual_savings / annual_cost_monthly * 100, 0),
            }

        return {
            'recommended_frequency': recommended_frequency,
            'months_between_downloads': months_between,
            'reason': f"{stable_percent:.1f}% of keywords stable or minimally changed",
            'savings_by_tier': savings,
        }

    def _get_recommendation(self, stability: Dict) -> Dict:
        """
        Generate specific recommendation
        """
        stable_percent = stability['stable_keywords']['percent']

        if stable_percent >= 95:
            return {
                'recommendation': "DOWNLOAD AHREFS DATA ONCE PER YEAR",
                'justification': f"{stable_percent:.1f}% of your keywords are stable. Monthly subscription is wasted money.",
                'action': "Cancel Ahrefs subscription. Download data annually. Use our platform for intelligence extraction.",
                'ahrefs_reaction': "😱 (They're fucked if everyone realizes this)",
            }
        elif stable_percent >= 90:
            return {
                'recommendation': "DOWNLOAD AHREFS DATA TWICE PER YEAR",
                'justification': f"{stable_percent:.1f}% stable. Bi-annual downloads are sufficient.",
                'action': "Cancel Ahrefs. Download every 6 months. Save thousands.",
                'ahrefs_reaction': "😨 (This destroys their MRR)",
            }
        elif stable_percent >= 80:
            return {
                'recommendation': "DOWNLOAD AHREFS DATA QUARTERLY",
                'justification': f"{stable_percent:.1f}% stable. Quarterly is enough.",
                'action': "Cancel Ahrefs monthly. Download quarterly. Save 75% of subscription cost.",
                'ahrefs_reaction': "😰 (Still hurts their revenue)",
            }
        else:
            return {
                'recommendation': "BI-MONTHLY DOWNLOADS SUFFICIENT",
                'justification': f"{stable_percent:.1f}% stable. More volatile than average.",
                'action': "Download every 2 months instead of monthly. Still saves 33%.",
                'ahrefs_reaction': "😅 (They're relieved but still losing money)",
            }

    async def _generate_ai_insight(
        self,
        stability: Dict,
        cost_analysis: Dict
    ) -> Dict:
        """
        Generate AI insight exposing the monthly subscription scam
        """

        prompt = f"""
Analyze this Ahrefs subscription waste analysis:

KEYWORD STABILITY:
- Stable (no change or ±1-2 positions): {stability['stable_keywords']['percent']:.1f}%
- Volatile (±3+ positions): {stability['volatile_keywords']['percent']:.1f}%

RECOMMENDATION: {cost_analysis['recommended_frequency']}
- Download every {cost_analysis['months_between_downloads']} months

COST SAVINGS (Enterprise tier example):
- Monthly subscription: $999/month = $11,988/year
- Recommended frequency: {cost_analysis['savings_by_tier']['Enterprise ($999/mo)']['annual_cost_recommended']}
- SAVINGS: {cost_analysis['savings_by_tier']['Enterprise ($999/mo)']['annual_savings']}/year

Provide:

1. THE AHREFS SCAM EXPOSED
   - Why do they push monthly subscriptions?
   - What are they hiding?
   - How much money are users wasting?

2. DATA STABILITY REALITY
   - Why is most SEO data stable month-to-month?
   - What actually changes frequently vs. rarely?

3. STRATEGIC RECOMMENDATION
   - How to maximize value from infrequent downloads?
   - What to monitor between downloads?
   - How to use our platform to extract max intelligence?

4. THE BRUTAL TRUTH
   - Who benefits from monthly subscriptions? (Ahrefs)
   - Who loses? (You)
   - What should everyone do? (Cancel and download quarterly)

Be brutally honest about Ahrefs' business model and how it exploits users.
        """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="quarterly_calculator",
            use_complex_model=True
        )

        return ai_result
