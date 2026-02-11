"""
MODE 1.5: Intent Gap Matrix
Identifies blind spots in search intent coverage (informational, commercial, transactional)
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.uploads import OrganicKeyword, Upload
from app.core.ai_engine import AIEngine


class IntentGapAnalyzer:
    """
    Analyzes your intent coverage vs competitors

    Intent types:
    - Informational: "how to", "what is", "guide"
    - Commercial: "best", "top", "vs", "review"
    - Transactional: "buy", "price", "discount", "free trial"
    - Navigational: brand names, specific products
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self) -> Dict[str, Any]:
        """
        Execute intent gap analysis
        """

        # Step 1: Get your keywords with intent flags
        your_keywords = await self._get_keywords_with_intent(is_primary=True)

        # Step 2: Get competitor keywords with intent
        competitor_keywords = await self._get_keywords_with_intent(is_primary=False)

        if not your_keywords or not competitor_keywords:
            return {
                "error": "No keyword data found. Upload Organic Keywords report."
            }

        # Step 3: Calculate intent distribution
        your_intent_dist = self._calculate_intent_distribution(your_keywords)
        competitor_intent_dist = self._calculate_intent_distribution(competitor_keywords)

        # Step 4: Identify intent gaps
        intent_gaps = self._identify_intent_gaps(
            your_intent_dist,
            competitor_intent_dist,
            your_keywords,
            competitor_keywords
        )

        # Step 5: Generate AI strategic insight
        ai_insight = await self._generate_ai_insight(
            your_intent_dist,
            competitor_intent_dist,
            intent_gaps
        )

        return {
            "mode": "1.5_intent_gap",
            "status": "completed",
            "summary": {
                "your_intent_distribution": {
                    "informational": f"{your_intent_dist['informational']['percent']:.1f}%",
                    "commercial": f"{your_intent_dist['commercial']['percent']:.1f}%",
                    "transactional": f"{your_intent_dist['transactional']['percent']:.1f}%",
                },
                "competitor_intent_distribution": {
                    "informational": f"{competitor_intent_dist['informational']['percent']:.1f}%",
                    "commercial": f"{competitor_intent_dist['commercial']['percent']:.1f}%",
                    "transactional": f"{competitor_intent_dist['transactional']['percent']:.1f}%",
                },
                "biggest_gap": intent_gaps['biggest_gap'],
            },
            "your_intent_profile": your_intent_dist,
            "competitor_intent_profile": competitor_intent_dist,
            "intent_gaps": intent_gaps,
            "ai_insight": ai_insight,
        }

    async def _get_keywords_with_intent(self, is_primary: bool) -> List[Dict]:
        """
        Get keywords with intent classification
        """
        query = (
            select(OrganicKeyword, Upload.source_domain)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.is_primary == is_primary)
            .where(Upload.processing_status == "completed")
            .where(OrganicKeyword.keyword.isnot(None))
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        keywords = []
        for row in rows:
            kw_obj, domain = row
            keywords.append({
                "keyword": kw_obj.keyword,
                "position": kw_obj.position,
                "volume": kw_obj.volume or 0,
                "traffic": kw_obj.traffic or 0,
                "parent_topic": kw_obj.parent_topic,
                "informational": kw_obj.informational or False,
                "commercial": kw_obj.commercial or False,
                "transactional": kw_obj.transactional or False,
                "navigational": kw_obj.navigational or False,
                "domain": domain,
            })

        return keywords

    def _calculate_intent_distribution(self, keywords: List[Dict]) -> Dict:
        """
        Calculate distribution of intent types
        """
        total_keywords = len(keywords)
        total_volume = sum(k['volume'] for k in keywords)
        total_traffic = sum(k['traffic'] for k in keywords)

        # Group by intent
        intent_groups = {
            'informational': [],
            'commercial': [],
            'transactional': [],
            'navigational': [],
            'unclassified': [],
        }

        for kw in keywords:
            # Keyword can have multiple intents
            classified = False

            if kw['informational']:
                intent_groups['informational'].append(kw)
                classified = True

            if kw['commercial']:
                intent_groups['commercial'].append(kw)
                classified = True

            if kw['transactional']:
                intent_groups['transactional'].append(kw)
                classified = True

            if kw['navigational']:
                intent_groups['navigational'].append(kw)
                classified = True

            if not classified:
                intent_groups['unclassified'].append(kw)

        # Calculate metrics per intent
        distribution = {}
        for intent, kw_list in intent_groups.items():
            if not kw_list:
                distribution[intent] = {
                    'keyword_count': 0,
                    'percent': 0,
                    'total_volume': 0,
                    'total_traffic': 0,
                    'avg_position': 0,
                    'sample_keywords': [],
                }
            else:
                distribution[intent] = {
                    'keyword_count': len(kw_list),
                    'percent': round(len(kw_list) / total_keywords * 100, 1),
                    'total_volume': sum(k['volume'] for k in kw_list),
                    'total_traffic': round(sum(k['traffic'] for k in kw_list), 0),
                    'avg_position': round(sum(k['position'] for k in kw_list if k['position']) / len([k for k in kw_list if k['position']]), 1) if any(k['position'] for k in kw_list) else 0,
                    'sample_keywords': [k['keyword'] for k in kw_list[:10]],
                }

        return distribution

    def _identify_intent_gaps(
        self,
        your_dist: Dict,
        competitor_dist: Dict,
        your_keywords: List[Dict],
        competitor_keywords: List[Dict]
    ) -> Dict:
        """
        Find which intents you're weak in compared to competitors
        """
        gaps = {}

        # Compare each intent
        for intent in ['informational', 'commercial', 'transactional', 'navigational']:
            your_percent = your_dist[intent]['percent']
            comp_percent = competitor_dist[intent]['percent']

            gap_percent = comp_percent - your_percent

            # Get competitor keywords in this intent that you don't rank for
            comp_keywords_in_intent = [
                k for k in competitor_keywords
                if k.get(intent, False)
            ]

            your_keywords_set = set(k['keyword'].lower() for k in your_keywords)
            missing_keywords = [
                k for k in comp_keywords_in_intent
                if k['keyword'].lower() not in your_keywords_set
            ]

            # Sort by traffic potential
            missing_keywords.sort(key=lambda x: x['traffic'], reverse=True)

            gaps[intent] = {
                'gap_percent': round(gap_percent, 1),
                'gap_keyword_count': len(missing_keywords),
                'missing_traffic_potential': round(sum(k['traffic'] for k in missing_keywords), 0),
                'top_missing_keywords': [
                    {
                        'keyword': k['keyword'],
                        'volume': k['volume'],
                        'traffic': k['traffic'],
                        'competitor_position': k['position'],
                    }
                    for k in missing_keywords[:20]
                ],
            }

        # Identify biggest gap
        biggest_gap_intent = max(gaps.items(), key=lambda x: abs(x[1]['gap_percent']))

        return {
            **gaps,
            'biggest_gap': {
                'intent': biggest_gap_intent[0],
                'gap_percent': biggest_gap_intent[1]['gap_percent'],
                'missing_keywords': biggest_gap_intent[1]['gap_keyword_count'],
            }
        }

    async def _generate_ai_insight(
        self,
        your_dist: Dict,
        competitor_dist: Dict,
        gaps: Dict
    ) -> Dict:
        """
        Generate AI strategic insight on intent gaps
        """

        prompt = f"""
Analyze this search intent gap analysis:

YOUR INTENT DISTRIBUTION:
- Informational: {your_dist['informational']['percent']:.1f}% ({your_dist['informational']['keyword_count']} keywords, {your_dist['informational']['total_traffic']:.0f} traffic/mo)
- Commercial: {your_dist['commercial']['percent']:.1f}% ({your_dist['commercial']['keyword_count']} keywords, {your_dist['commercial']['total_traffic']:.0f} traffic/mo)
- Transactional: {your_dist['transactional']['percent']:.1f}% ({your_dist['transactional']['keyword_count']} keywords, {your_dist['transactional']['total_traffic']:.0f} traffic/mo)

COMPETITOR INTENT DISTRIBUTION:
- Informational: {competitor_dist['informational']['percent']:.1f}% ({competitor_dist['informational']['keyword_count']} keywords, {competitor_dist['informational']['total_traffic']:.0f} traffic/mo)
- Commercial: {competitor_dist['commercial']['percent']:.1f}% ({competitor_dist['commercial']['keyword_count']} keywords, {competitor_dist['commercial']['total_traffic']:.0f} traffic/mo)
- Transactional: {competitor_dist['transactional']['percent']:.1f}% ({competitor_dist['transactional']['keyword_count']} keywords, {competitor_dist['transactional']['total_traffic']:.0f} traffic/mo)

BIGGEST GAP: {gaps['biggest_gap']['intent'].upper()}
- Gap: {gaps['biggest_gap']['gap_percent']:.1f} percentage points
- Missing keywords: {gaps['biggest_gap']['missing_keywords']}

Provide:

1. INTENT STRATEGY DIAGNOSIS
   - What does your current intent distribution say about your content strategy?
   - Are you teaching but not selling? Or selling without educating?

2. COMMERCIAL IMPACT
   - Which intent gaps hurt revenue most?
   - What's the conversion potential of each intent type?

3. CONTENT STRATEGY REALIGNMENT
   - How to balance intent coverage?
   - Which intent to prioritize based on business goals?

4. SPECIFIC ACTIONS
   - Top 10 keywords to create content for
   - Content format for each intent type
   - How to transition users from informational → commercial → transactional

Be brutally honest about what the intent distribution reveals about content strategy.
        """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="intent_gap_analysis",
            use_complex_model=True
        )

        return ai_result
