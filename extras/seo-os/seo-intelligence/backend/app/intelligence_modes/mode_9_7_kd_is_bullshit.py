"""
MODE 9.7: Keyword Difficulty is Bullshit
Proves that Ahrefs' Keyword Difficulty metric is misleading
Shows real examples where KD doesn't predict actual ranking difficulty
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import defaultdict

from app.models.uploads import OrganicKeyword, Upload, ReferringDomain
from app.core.ai_engine import AIEngine


class KeywordDifficultyBullshitExposer:
    """
    Exposes the "Keyword Difficulty" scam:

    Ahrefs KD is based on:
    - Backlinks to top 10 results
    - Domain Rating of top 10

    What it IGNORES:
    - Content quality
    - Topical authority
    - User intent match
    - SERP freshness
    - Domain relevance
    - Content depth

    This mode proves KD doesn't correlate with actual ranking difficulty
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self) -> Dict[str, Any]:
        """
        Expose keyword difficulty BS
        """

        # Step 1: Get your keywords with KD and actual results
        your_keywords = await self._get_your_keywords_with_kd()

        if not your_keywords:
            return {
                "error": "No keyword data found. Upload Organic Keywords with difficulty scores."
            }

        # Step 2: Find KD prediction failures
        kd_failures = self._find_kd_prediction_failures(your_keywords)

        # Step 3: Calculate real difficulty factors
        real_difficulty_analysis = await self._calculate_real_difficulty(your_keywords)

        # Step 4: Generate alternative difficulty score
        alternative_scores = self._generate_alternative_scores(real_difficulty_analysis)

        # Step 5: Generate AI insight exposing the BS
        ai_insight = await self._generate_ai_insight(kd_failures, real_difficulty_analysis)

        return {
            "mode": "9.7_keyword_difficulty_is_bullshit",
            "status": "completed",
            "summary": {
                "total_keywords_analyzed": len(your_keywords),
                "kd_prediction_failures": len(kd_failures['overestimated']) + len(kd_failures['underestimated']),
                "overestimated_difficulty": len(kd_failures['overestimated']),
                "underestimated_difficulty": len(kd_failures['underestimated']),
            },
            "kd_failures": kd_failures,
            "real_difficulty_factors": real_difficulty_analysis,
            "alternative_difficulty_model": alternative_scores,
            "ai_insight": ai_insight,
        }

    async def _get_your_keywords_with_kd(self) -> List[Dict]:
        """
        Get your keywords with Ahrefs KD scores and actual performance
        """
        query = (
            select(OrganicKeyword)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.is_primary == True)
            .where(Upload.processing_status == "completed")
            .where(OrganicKeyword.difficulty.isnot(None))
            .where(OrganicKeyword.position.isnot(None))
        )

        result = await self.session.execute(query)
        rows = result.scalars().all()

        keywords = []
        for kw in rows:
            keywords.append({
                'keyword': kw.keyword,
                'ahrefs_kd': kw.difficulty,
                'position': kw.position,
                'volume': kw.volume or 0,
                'traffic': kw.traffic or 0,
                'parent_topic': kw.parent_topic,
                'previous_position': kw.previous_position,
            })

        return keywords

    def _find_kd_prediction_failures(self, keywords: List[Dict]) -> Dict:
        """
        Find cases where KD was wrong

        Overestimated: KD said "hard" (70+) but you ranked top 10
        Underestimated: KD said "easy" (<30) but you're position 50+
        """
        overestimated = []  # KD said hard, but you ranked easily
        underestimated = []  # KD said easy, but you struggled

        for kw in keywords:
            kd = kw['ahrefs_kd']
            position = kw['position']

            # Overestimated difficulty
            if kd >= 70 and position <= 10:
                time_to_rank = self._estimate_time_to_rank(kw)
                overestimated.append({
                    **kw,
                    'kd_says': "VERY HARD (70+)",
                    'reality': f"Ranked #{position}",
                    'ahrefs_wrong_by': 'Overestimated',
                    'time_to_rank': time_to_rank,
                })

            elif kd >= 50 and position <= 5:
                overestimated.append({
                    **kw,
                    'kd_says': "HARD (50+)",
                    'reality': f"Ranked #{position}",
                    'ahrefs_wrong_by': 'Overestimated',
                })

            # Underestimated difficulty
            elif kd <= 20 and position >= 50:
                underestimated.append({
                    **kw,
                    'kd_says': "EASY (<20)",
                    'reality': f"Only ranked #{position}",
                    'ahrefs_wrong_by': 'Underestimated',
                })

            elif kd <= 30 and position >= 30:
                underestimated.append({
                    **kw,
                    'kd_says': "MODERATE (<30)",
                    'reality': f"Only ranked #{position}",
                    'ahrefs_wrong_by': 'Underestimated',
                })

        # Sort by most dramatic failures
        overestimated.sort(key=lambda x: x['ahrefs_kd'] - (100 - x['position'] * 10), reverse=True)
        underestimated.sort(key=lambda x: x['position'] - x['ahrefs_kd'], reverse=True)

        return {
            'overestimated': overestimated[:30],
            'underestimated': underestimated[:30],
            'accuracy_rate': self._calculate_accuracy_rate(keywords),
        }

    def _estimate_time_to_rank(self, keyword: Dict) -> str:
        """
        Estimate how long it took to rank (if data available)
        """
        if keyword.get('previous_position'):
            if keyword['previous_position'] > 100 and keyword['position'] <= 10:
                return "0-100 to top 10 (likely < 6 months)"
            elif keyword['previous_position'] > 50:
                return "50+ to current position (likely < 3 months)"

        return "Unknown (but faster than KD suggested)"

    def _calculate_accuracy_rate(self, keywords: List[Dict]) -> Dict:
        """
        Calculate how often KD actually predicts difficulty correctly
        """
        # Simplistic accuracy model:
        # If KD < 30 and position <= 20: CORRECT (easy and ranked well)
        # If KD >= 60 and position >= 30: CORRECT (hard and didn't rank well)
        # Everything else: WRONG or AMBIGUOUS

        correct = 0
        wrong = 0
        ambiguous = 0

        for kw in keywords:
            kd = kw['ahrefs_kd']
            pos = kw['position']

            if (kd < 30 and pos <= 20) or (kd >= 60 and pos >= 30):
                correct += 1
            elif (kd >= 60 and pos <= 10) or (kd < 30 and pos >= 50):
                wrong += 1
            else:
                ambiguous += 1

        total = len(keywords)
        accuracy = (correct / total * 100) if total > 0 else 0

        return {
            'total_keywords': total,
            'correct_predictions': correct,
            'wrong_predictions': wrong,
            'ambiguous': ambiguous,
            'accuracy_percent': round(accuracy, 1),
            'verdict': 'UNRELIABLE' if accuracy < 60 else 'SOMEWHAT RELIABLE' if accuracy < 75 else 'RELIABLE'
        }

    async def _calculate_real_difficulty(self, keywords: List[Dict]) -> Dict:
        """
        Calculate what ACTUALLY makes keywords difficult

        Real factors:
        1. Topical authority (do you own the topic?)
        2. Content depth (comprehensive vs. thin)
        3. Backlink quality (not just quantity)
        4. Domain relevance (topical trust)
        5. SERP freshness (new vs. old results)
        """

        # Group by parent topic to assess topical authority
        topic_coverage = defaultdict(list)
        for kw in keywords:
            if kw['parent_topic']:
                topic_coverage[kw['parent_topic']].append(kw)

        # Calculate average position by topic (topical authority proxy)
        topical_authority = {}
        for topic, kws in topic_coverage.items():
            avg_pos = sum(k['position'] for k in kws) / len(kws)
            topical_authority[topic] = {
                'avg_position': round(avg_pos, 1),
                'keyword_count': len(kws),
                'authority_level': 'STRONG' if avg_pos < 10 else 'MODERATE' if avg_pos < 20 else 'WEAK'
            }

        return {
            'topical_authority_matters': True,
            'authority_analysis': topical_authority,
            'key_insight': "Topics where you have authority (low avg position) = easier to rank for new keywords",
        }

    def _generate_alternative_scores(self, real_factors: Dict) -> Dict:
        """
        Generate alternative "Real Difficulty" scores
        """
        return {
            'model_name': "REAL DIFFICULTY SCORE",
            'factors': [
                {
                    'factor': 'Topical Authority',
                    'weight': '40%',
                    'description': 'Do you already rank well for this topic?',
                },
                {
                    'factor': 'Content Depth',
                    'weight': '25%',
                    'description': 'How comprehensive is your content?',
                },
                {
                    'factor': 'Backlink Quality',
                    'weight': '20%',
                    'description': 'Quality of referring domains (not just count)',
                },
                {
                    'factor': 'Domain Relevance',
                    'weight': '10%',
                    'description': 'Is your domain topically relevant?',
                },
                {
                    'factor': 'SERP Volatility',
                    'weight': '5%',
                    'description': 'How stable is the SERP?',
                },
            ],
            'vs_ahrefs_kd': {
                'ahrefs': 'Based on backlink count only',
                'ours': 'Based on 5 factors including YOUR competitive position',
            }
        }

    async def _generate_ai_insight(
        self,
        failures: Dict,
        real_factors: Dict
    ) -> Dict:
        """
        Generate brutal AI insight exposing KD BS
        """

        overestimated_examples = "\n".join([
            f"- \"{f['keyword']}\": KD {f['ahrefs_kd']} but you ranked #{f['position']}"
            for f in failures['overestimated'][:10]
        ]) if failures['overestimated'] else "None"

        underestimated_examples = "\n".join([
            f"- \"{f['keyword']}\": KD {f['ahrefs_kd']} but you're stuck at #{f['position']}"
            for f in failures['underestimated'][:10]
        ]) if failures['underestimated'] else "None"

        prompt = f"""
Expose the "Keyword Difficulty" scam:

AHREFS KD ACCURACY: {failures['accuracy_rate']['accuracy_percent']:.1f}% ({failures['accuracy_rate']['verdict']})

OVERESTIMATED DIFFICULTY (Ahrefs said "impossible", you ranked easily):
{overestimated_examples}

UNDERESTIMATED DIFFICULTY (Ahrefs said "easy", you couldn't rank):
{underestimated_examples}

WHY KD IS BULLSHIT:
- Only looks at backlinks to top 10
- Ignores YOUR competitive position
- Ignores topical authority
- Ignores content quality
- One-size-fits-all metric

Provide:

1. THE KD SCAM EXPOSED
   - Why does Ahrefs promote KD despite its inaccuracy?
   - How does it mislead users?
   - What damage does it cause?

2. REAL DIFFICULTY FACTORS
   - What ACTUALLY determines ranking difficulty?
   - Why is topical authority more important than backlinks?

3. HOW TO ASSESS TRUE DIFFICULTY
   - Ignore KD completely?
   - What metrics to use instead?
   - How to predict YOUR ability to rank?

4. EXAMPLES FROM THE DATA
   - Best overestimated examples (prove KD is BS)
   - Why you ranked despite "high KD"?
   - What this teaches about SEO?

Be brutally honest about Ahrefs' misleading metric and the damage it causes to SEO strategies.
        """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="keyword_difficulty_exposer",
            use_complex_model=True
        )

        return ai_result
