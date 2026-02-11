"""
MODE 8.2: Content ROI Forecaster
Predicts revenue potential and ROI for ranking at different positions
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.uploads import OrganicKeyword, Upload, SERPOverview
from app.core.ai_engine import AIEngine


class ContentROIForecaster:
    """
    Forecasts content ROI based on:
    - Ranking position potential
    - Search volume
    - Expected CTR per position
    - User-provided conversion rate and AOV
    """

    # Industry-standard CTR by position (desktop, no SERP features)
    CTR_BY_POSITION = {
        1: 28.5,
        2: 15.7,
        3: 11.0,
        4: 8.0,
        5: 7.2,
        6: 5.1,
        7: 4.0,
        8: 3.2,
        9: 2.8,
        10: 2.5,
    }

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(
        self,
        keyword: Optional[str] = None,
        conversion_rate: float = 2.0,  # Default 2%
        avg_order_value: float = 100.0,  # Default $100
        content_cost: float = 500.0,  # Default $500 content cost
        link_building_cost: float = 1000.0,  # Default $1000 for links
    ) -> Dict[str, Any]:
        """
        Execute content ROI forecast

        Can forecast for:
        - Specific keyword
        - All high-opportunity keywords
        """

        if keyword:
            # Forecast for specific keyword
            forecast = await self._forecast_keyword(
                keyword,
                conversion_rate,
                avg_order_value,
                content_cost,
                link_building_cost
            )

            if not forecast:
                return {
                    "error": f"Keyword not found: {keyword}"
                }

            forecasts = [forecast]
        else:
            # Forecast for top opportunities
            forecasts = await self._forecast_top_opportunities(
                conversion_rate,
                avg_order_value,
                content_cost,
                link_building_cost
            )

        # Generate AI insight
        ai_insight = await self._generate_ai_insight(
            forecasts[:20],
            conversion_rate,
            avg_order_value
        )

        return {
            "mode": "8.2_content_roi_forecast",
            "status": "completed",
            "parameters": {
                "conversion_rate": f"{conversion_rate}%",
                "avg_order_value": f"${avg_order_value:.2f}",
                "content_cost": f"${content_cost:.2f}",
                "link_building_cost": f"${link_building_cost:.2f}",
            },
            "forecasts": forecasts[:50],
            "summary": {
                "total_forecasts": len(forecasts),
                "highest_roi": max(f['roi_percent'] for f in forecasts) if forecasts else 0,
                "total_potential_revenue": sum(f['annual_revenue_at_position_1'] for f in forecasts),
            },
            "ai_insight": ai_insight,
        }

    async def _forecast_keyword(
        self,
        keyword: str,
        conversion_rate: float,
        aov: float,
        content_cost: float,
        link_cost: float
    ) -> Optional[Dict]:
        """
        Forecast ROI for specific keyword
        """
        # Get keyword data from competitor or your data
        query = (
            select(OrganicKeyword, Upload.is_primary)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.processing_status == "completed")
            .where(OrganicKeyword.keyword == keyword)
            .limit(1)
        )

        result = await self.session.execute(query)
        row = result.fetchone()

        if not row:
            return None

        kw_obj, is_primary = row

        return self._calculate_roi_forecast(
            keyword=kw_obj.keyword,
            volume=kw_obj.volume or 0,
            current_position=kw_obj.position if is_primary else None,
            difficulty=kw_obj.difficulty or 50,
            conversion_rate=conversion_rate,
            aov=aov,
            content_cost=content_cost,
            link_cost=link_cost,
        )

    async def _forecast_top_opportunities(
        self,
        conversion_rate: float,
        aov: float,
        content_cost: float,
        link_cost: float
    ) -> List[Dict]:
        """
        Forecast ROI for top keyword opportunities
        """
        # Get competitor keywords with high volume
        query = (
            select(OrganicKeyword)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.is_primary == False)  # Competitor keywords
            .where(Upload.processing_status == "completed")
            .where(OrganicKeyword.volume.isnot(None))
            .where(OrganicKeyword.volume >= 500)  # Min 500 volume
            .order_by(OrganicKeyword.volume.desc())
            .limit(100)
        )

        result = await self.session.execute(query)
        keywords = result.scalars().all()

        forecasts = []
        for kw in keywords:
            forecast = self._calculate_roi_forecast(
                keyword=kw.keyword,
                volume=kw.volume or 0,
                current_position=None,
                difficulty=kw.difficulty or 50,
                conversion_rate=conversion_rate,
                aov=aov,
                content_cost=content_cost,
                link_cost=link_cost,
            )
            forecasts.append(forecast)

        # Sort by ROI
        forecasts.sort(key=lambda x: x['roi_percent'], reverse=True)

        return forecasts

    def _calculate_roi_forecast(
        self,
        keyword: str,
        volume: int,
        current_position: Optional[int],
        difficulty: int,
        conversion_rate: float,
        aov: float,
        content_cost: float,
        link_cost: float,
    ) -> Dict:
        """
        Calculate ROI forecast for different positions
        """
        monthly_volume = volume

        # Calculate revenue by position
        revenue_by_position = {}
        for position in range(1, 11):
            ctr = self.CTR_BY_POSITION.get(position, 2.0)
            monthly_clicks = monthly_volume * (ctr / 100)
            monthly_conversions = monthly_clicks * (conversion_rate / 100)
            monthly_revenue = monthly_conversions * aov
            annual_revenue = monthly_revenue * 12

            revenue_by_position[position] = {
                'position': position,
                'ctr_percent': ctr,
                'monthly_clicks': round(monthly_clicks, 0),
                'monthly_conversions': round(monthly_conversions, 2),
                'monthly_revenue': round(monthly_revenue, 2),
                'annual_revenue': round(annual_revenue, 2),
            }

        # Total investment
        total_investment = content_cost + link_cost

        # Calculate ROI for position #1
        position_1_annual_revenue = revenue_by_position[1]['annual_revenue']
        roi_dollars = position_1_annual_revenue - total_investment
        roi_percent = (roi_dollars / total_investment * 100) if total_investment > 0 else 0

        # Payback period (months)
        monthly_revenue_pos_1 = revenue_by_position[1]['monthly_revenue']
        payback_months = (total_investment / monthly_revenue_pos_1) if monthly_revenue_pos_1 > 0 else 999

        return {
            'keyword': keyword,
            'monthly_volume': monthly_volume,
            'current_position': current_position,
            'keyword_difficulty': difficulty,
            'investment': {
                'content_cost': content_cost,
                'link_building_cost': link_cost,
                'total_investment': total_investment,
            },
            'annual_revenue_at_position_1': position_1_annual_revenue,
            'roi_dollars': round(roi_dollars, 2),
            'roi_percent': round(roi_percent, 1),
            'payback_months': round(payback_months, 1),
            'revenue_forecast_by_position': revenue_by_position,
            'priority_score': self._calculate_priority_score(
                roi_percent,
                difficulty,
                payback_months
            ),
        }

    def _calculate_priority_score(
        self,
        roi_percent: float,
        difficulty: int,
        payback_months: float
    ) -> float:
        """
        Calculate priority score (0-100)

        Higher score = better opportunity
        """
        score = 0

        # ROI component (max 50 points)
        if roi_percent >= 500:
            score += 50
        elif roi_percent >= 300:
            score += 40
        elif roi_percent >= 200:
            score += 30
        elif roi_percent >= 100:
            score += 20
        elif roi_percent >= 50:
            score += 10

        # Difficulty component (max 30 points) - inverse
        if difficulty <= 20:
            score += 30
        elif difficulty <= 40:
            score += 20
        elif difficulty <= 60:
            score += 10

        # Payback period component (max 20 points)
        if payback_months <= 3:
            score += 20
        elif payback_months <= 6:
            score += 15
        elif payback_months <= 12:
            score += 10
        elif payback_months <= 24:
            score += 5

        return round(score, 1)

    async def _generate_ai_insight(
        self,
        forecasts: List[Dict],
        conversion_rate: float,
        aov: float
    ) -> Dict:
        """
        Generate AI strategic insight on content ROI
        """

        if not forecasts:
            prompt = "No keywords available for ROI forecasting."
        else:
            top_roi = "\n".join([
                f"- \"{f['keyword']}\": ${f['annual_revenue_at_position_1']:,.0f}/year at #1, ROI: {f['roi_percent']:.0f}%, Payback: {f['payback_months']:.1f} months"
                for f in forecasts[:10]
            ])

            prompt = f"""
Analyze this content ROI forecast:

ASSUMPTIONS:
- Conversion rate: {conversion_rate}%
- Average order value: ${aov:.2f}

TOP ROI OPPORTUNITIES:
{top_roi}

Provide:

1. INVESTMENT PRIORITIZATION
   - Which keywords to target first based on ROI?
   - How to allocate budget across opportunities?

2. REALISTIC EXPECTATIONS
   - Are these ROI projections achievable?
   - What factors could reduce actual ROI?

3. STRATEGIC RECOMMENDATIONS
   - Should you focus on high-ROI or fast-payback keywords?
   - How to sequence content creation for maximum cash flow?

4. OPTIMIZATION TACTICS
   - How to improve conversion rate for these keywords?
   - How to reduce content/link costs without sacrificing quality?

Be specific about which keywords to prioritize and why.
            """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="content_roi_forecast",
            use_complex_model=True
        )

        return ai_result
