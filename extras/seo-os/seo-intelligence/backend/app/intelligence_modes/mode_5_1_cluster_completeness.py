"""
MODE 5.1: Cluster Completeness Score
Calculates semantic coverage percentage for each parent topic
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import defaultdict

from app.models.uploads import OrganicKeyword, Upload
from app.core.ai_engine import AIEngine


class ClusterCompletenessAnalyzer:
    """
    Measures topical authority through cluster completeness

    Complete cluster = you rank for high percentage of all keywords in that topic
    Incomplete cluster = gaps in semantic coverage
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self) -> Dict[str, Any]:
        """
        Execute cluster completeness analysis
        """

        # Step 1: Get all keywords (yours + competitors) grouped by parent topic
        all_keywords = await self._get_all_keywords_by_topic()

        if not all_keywords:
            return {
                "error": "No keyword data found. Upload Organic Keywords report."
            }

        # Step 2: Calculate completeness per cluster
        cluster_analysis = self._calculate_completeness(all_keywords)

        # Step 3: Identify complete, incomplete, and missing clusters
        categorized = self._categorize_clusters(cluster_analysis)

        # Step 4: Generate AI insight
        ai_insight = await self._generate_ai_insight(cluster_analysis, categorized)

        return {
            "mode": "5.1_cluster_completeness",
            "status": "completed",
            "summary": {
                "total_clusters_analyzed": len(cluster_analysis),
                "complete_clusters": len(categorized['complete']),
                "partial_clusters": len(categorized['partial']),
                "minimal_clusters": len(categorized['minimal']),
                "missing_clusters": len(categorized['missing']),
                "avg_completeness": round(sum(c['completeness_score'] for c in cluster_analysis) / len(cluster_analysis), 1) if cluster_analysis else 0,
            },
            "cluster_completeness": cluster_analysis,
            "complete_clusters": categorized['complete'],
            "partial_clusters": categorized['partial'],
            "minimal_clusters": categorized['minimal'],
            "missing_clusters": categorized['missing'],
            "ai_insight": ai_insight,
        }

    async def _get_all_keywords_by_topic(self) -> Dict[str, Dict]:
        """
        Get all keywords grouped by parent topic
        """
        query = (
            select(OrganicKeyword, Upload.is_primary, Upload.source_domain)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.processing_status == "completed")
            .where(OrganicKeyword.parent_topic.isnot(None))
            .where(OrganicKeyword.keyword.isnot(None))
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        # Group by topic
        topics = defaultdict(lambda: {
            'all_keywords': set(),
            'your_keywords': set(),
            'competitor_keywords': set(),
            'total_volume': 0,
            'your_traffic': 0,
        })

        for row in rows:
            kw_obj, is_primary, domain = row
            topic = kw_obj.parent_topic
            keyword = kw_obj.keyword.lower()

            topics[topic]['all_keywords'].add(keyword)

            if is_primary:
                topics[topic]['your_keywords'].add(keyword)
                topics[topic]['your_traffic'] += kw_obj.traffic or 0
            else:
                topics[topic]['competitor_keywords'].add(keyword)

            topics[topic]['total_volume'] += kw_obj.volume or 0

        return dict(topics)

    def _calculate_completeness(self, topics: Dict[str, Dict]) -> List[Dict]:
        """
        Calculate completeness score for each cluster
        """
        analysis = []

        for topic_name, data in topics.items():
            total_keywords = len(data['all_keywords'])
            your_keywords = len(data['your_keywords'])

            if total_keywords == 0:
                continue

            completeness_score = (your_keywords / total_keywords) * 100

            # Calculate semantic depth
            semantic_depth = your_keywords  # Simple metric: number of keywords you rank for

            # Missing keywords
            missing_keywords = data['all_keywords'] - data['your_keywords']

            analysis.append({
                'parent_topic': topic_name,
                'total_keywords_in_cluster': total_keywords,
                'your_keywords': your_keywords,
                'missing_keywords': len(missing_keywords),
                'completeness_score': round(completeness_score, 1),
                'semantic_depth': semantic_depth,
                'total_search_volume': data['total_volume'],
                'your_current_traffic': round(data['your_traffic'], 0),
                'potential_traffic': round(data['total_volume'] * 0.3, 0),  # Rough estimate
                'sample_missing_keywords': list(missing_keywords)[:10],
                'authority_level': self._classify_authority_level(completeness_score),
            })

        # Sort by completeness score
        analysis.sort(key=lambda x: x['completeness_score'], reverse=True)

        return analysis

    def _classify_authority_level(self, completeness: float) -> str:
        """
        Classify topical authority based on completeness
        """
        if completeness >= 80:
            return "TOPICAL AUTHORITY"
        elif completeness >= 60:
            return "STRONG COVERAGE"
        elif completeness >= 40:
            return "MODERATE COVERAGE"
        elif completeness >= 20:
            return "WEAK COVERAGE"
        else:
            return "MINIMAL PRESENCE"

    def _categorize_clusters(self, analysis: List[Dict]) -> Dict:
        """
        Categorize clusters by completeness level
        """
        categories = {
            'complete': [],      # 80%+ completeness
            'partial': [],       # 40-79% completeness
            'minimal': [],       # 1-39% completeness
            'missing': [],       # 0% completeness
        }

        for cluster in analysis:
            score = cluster['completeness_score']

            if score >= 80:
                categories['complete'].append(cluster)
            elif score >= 40:
                categories['partial'].append(cluster)
            elif score > 0:
                categories['minimal'].append(cluster)
            else:
                categories['missing'].append(cluster)

        return categories

    async def _generate_ai_insight(
        self,
        analysis: List[Dict],
        categorized: Dict
    ) -> Dict:
        """
        Generate AI strategic insight on cluster completeness
        """

        # Top complete clusters
        complete = "\n".join([
            f"- {c['parent_topic']}: {c['completeness_score']:.1f}% ({c['your_keywords']}/{c['total_keywords_in_cluster']} keywords)"
            for c in categorized['complete'][:5]
        ]) if categorized['complete'] else "None"

        # Top incomplete clusters (high opportunity)
        incomplete_high_volume = sorted(
            categorized['partial'] + categorized['minimal'],
            key=lambda x: x['total_search_volume'],
            reverse=True
        )[:5]

        incomplete = "\n".join([
            f"- {c['parent_topic']}: {c['completeness_score']:.1f}% ({c['missing_keywords']} missing keywords, {c['total_search_volume']:,} volume)"
            for c in incomplete_high_volume
        ]) if incomplete_high_volume else "None"

        prompt = f"""
Analyze this topical authority / cluster completeness analysis:

COMPLETE CLUSTERS (80%+ coverage = topical authority):
{complete}

INCOMPLETE CLUSTERS (high opportunity):
{incomplete}

OVERALL STATISTICS:
- Total clusters: {len(analysis)}
- Complete (80%+): {len(categorized['complete'])}
- Partial (40-79%): {len(categorized['partial'])}
- Minimal (<40%): {len(categorized['minimal'])}
- Missing (0%): {len(categorized['missing'])}

Provide:

1. TOPICAL AUTHORITY ASSESSMENT
   - Which topics do you own?
   - Which topics are you weak in?
   - What does this say about your content strategy?

2. SEMANTIC GAP STRATEGY
   - How to improve cluster completeness?
   - Which clusters to prioritize?

3. CONTENT PLANNING
   - How many articles needed per incomplete cluster?
   - Hub-and-spoke vs. comprehensive guide approach?

4. LONG-TERM AUTHORITY BUILDING
   - Path from 40% to 80% completeness
   - Which clusters to dominate first?
   - How to achieve topical authority status?

Be specific about the relationship between cluster completeness and rankings.
        """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="cluster_completeness",
            use_complex_model=True
        )

        return ai_result
