"""
MODE 2.1: PAA Question Hijack Strategy
Extracts People Also Ask questions from SERP data and generates content strategy
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from collections import defaultdict
import re

from app.models.uploads import SERPOverview, Upload
from app.core.ai_engine import AIEngine, PromptTemplates


class PAAHijackAnalyzer:
    """
    Analyzes People Also Ask questions to identify content opportunities
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self) -> Dict[str, Any]:
        """
        Execute PAA hijack analysis
        """

        # Step 1: Get SERP overview data
        serp_data = await self._get_serp_data()

        if not serp_data:
            return {
                "error": "No SERP overview data found. Upload SERP Overview report first."
            }

        # Step 2: Filter for PAA results
        paa_results = [
            result for result in serp_data
            if result.get('result_type', '').lower() == 'people also ask'
        ]

        if not paa_results:
            return {
                "error": "No PAA questions found in SERP data."
            }

        # Step 3: Extract questions and group by keyword
        keyword_to_questions = defaultdict(list)
        all_questions = []

        for result in paa_results:
            keyword = result['keyword']
            question = result.get('title', '')  # PAA question is in title field

            if question:
                keyword_to_questions[keyword].append(question)
                all_questions.append({
                    'keyword': keyword,
                    'question': question,
                    'parent_topic': result.get('parent_topic')
                })

        # Step 4: Cluster questions by similarity
        question_clusters = self._cluster_questions(all_questions)

        # Step 5: Generate AI insights
        ai_insight = await self._generate_ai_insight(
            all_questions[:50],  # Top 50 for AI
            question_clusters,
            keyword_to_questions
        )

        return {
            "mode": "2.1_paa_hijack",
            "status": "completed",
            "summary": {
                "total_paa_questions": len(all_questions),
                "unique_keywords": len(keyword_to_questions),
                "question_clusters": len(question_clusters),
            },
            "question_clusters": question_clusters,
            "questions_by_keyword": dict(keyword_to_questions),
            "all_questions": all_questions,
            "ai_insight": ai_insight,
        }

    async def _get_serp_data(self) -> List[Dict]:
        """
        Get SERP overview data from database
        """
        query = (
            select(SERPOverview, Upload.source_domain)
            .join(Upload, SERPOverview.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.processing_status == "completed")
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        serp_results = []
        for row in rows:
            serp_obj, domain = row
            serp_results.append({
                "keyword": serp_obj.keyword,
                "parent_topic": serp_obj.parent_topic,
                "result_type": serp_obj.result_type,
                "title": serp_obj.title,
                "url": serp_obj.url,
                "domain": serp_obj.domain,
                "position": serp_obj.position,
            })

        return serp_results

    def _cluster_questions(self, questions: List[Dict]) -> List[Dict]:
        """
        Cluster questions by theme/intent

        Uses simple keyword matching for now
        TODO: Use embeddings for better clustering
        """
        clusters = defaultdict(list)

        # Common question patterns
        patterns = {
            "what": r"^what\s",
            "how": r"^how\s",
            "why": r"^why\s",
            "when": r"^when\s",
            "where": r"^where\s",
            "who": r"^who\s",
            "can": r"^can\s",
            "does": r"^does\s",
            "is": r"^is\s",
            "comparison": r"\s(vs|versus|or|compared to)\s",
            "cost": r"(cost|price|expensive|cheap|free)",
            "best": r"(best|top|greatest)",
        }

        for q in questions:
            question_lower = q['question'].lower()
            matched = False

            for pattern_name, pattern_regex in patterns.items():
                if re.search(pattern_regex, question_lower):
                    clusters[pattern_name].append(q)
                    matched = True
                    break

            if not matched:
                clusters["other"].append(q)

        # Convert to list format
        cluster_list = []
        for pattern, questions_list in clusters.items():
            if questions_list:
                cluster_list.append({
                    "pattern": pattern,
                    "question_count": len(questions_list),
                    "sample_questions": [q['question'] for q in questions_list[:5]],
                    "keywords": list(set(q['keyword'] for q in questions_list)),
                })

        # Sort by count
        cluster_list.sort(key=lambda x: x['question_count'], reverse=True)

        return cluster_list

    async def _generate_ai_insight(
        self,
        questions: List[Dict],
        clusters: List[Dict],
        keyword_to_questions: Dict
    ) -> Dict:
        """
        Generate AI-powered content strategy from PAA questions
        """

        # Build context
        context = {
            "total_questions": len(questions),
            "clusters": clusters,
        }

        # Find most common keyword
        most_common_keyword = max(
            keyword_to_questions.items(),
            key=lambda x: len(x[1])
        )[0]

        prompt = PromptTemplates.serp_paa_questions(
            paa_questions=[q['question'] for q in questions],
            keyword_context=most_common_keyword
        )

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="serp_paa_hijack",
            context=context,
            use_complex_model=False  # Sonnet is fine
        )

        return ai_result
