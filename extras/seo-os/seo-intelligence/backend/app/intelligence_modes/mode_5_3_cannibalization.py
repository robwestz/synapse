"""
MODE 5.3: Keyword Cannibalization Detector
Identifies keywords where you rank with DIFFERENT URLs
This dilutes authority and prevents you from ranking higher
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import defaultdict

from app.models.uploads import OrganicKeyword, Upload
from app.core.ai_engine import AIEngine


class CannibalizationDetector:
    """
    Detects keyword cannibalization:
    - Same keyword ranking with 2+ different URLs
    - Similar keywords in same cluster ranking with different URLs
    - Dilution of topical authority

    Solution: Consolidate or redirect to single authoritative page
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self) -> Dict[str, Any]:
        """
        Execute cannibalization detection
        """

        # Step 1: Get your keywords with URLs
        your_keywords = await self._get_your_keywords()

        if not your_keywords:
            return {
                "error": "No keyword data found for your site. Upload primary Organic Keywords report."
            }

        # Step 2: Detect exact keyword cannibalization
        exact_cannibalization = self._detect_exact_cannibalization(your_keywords)

        # Step 3: Detect cluster cannibalization
        cluster_cannibalization = self._detect_cluster_cannibalization(your_keywords)

        # Step 4: Calculate impact
        impact_analysis = self._calculate_impact(exact_cannibalization, cluster_cannibalization)

        # Step 5: Generate consolidation recommendations
        recommendations = self._generate_recommendations(exact_cannibalization, cluster_cannibalization)

        # Step 6: Generate AI insight
        ai_insight = await self._generate_ai_insight(
            exact_cannibalization[:20],
            cluster_cannibalization[:20],
            impact_analysis
        )

        return {
            "mode": "5.3_cannibalization_detector",
            "status": "completed",
            "summary": {
                "exact_cannibalization_issues": len(exact_cannibalization),
                "cluster_cannibalization_issues": len(cluster_cannibalization),
                "total_keywords_affected": impact_analysis['total_keywords_affected'],
                "estimated_traffic_loss": impact_analysis['estimated_traffic_loss'],
            },
            "exact_cannibalization": exact_cannibalization[:50],
            "cluster_cannibalization": cluster_cannibalization[:50],
            "impact_analysis": impact_analysis,
            "consolidation_recommendations": recommendations,
            "ai_insight": ai_insight,
        }

    async def _get_your_keywords(self) -> List[Dict]:
        """
        Get your keywords with URLs and positions
        """
        query = (
            select(OrganicKeyword)
            .join(Upload, OrganicKeyword.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.is_primary == True)
            .where(Upload.processing_status == "completed")
            .where(OrganicKeyword.url.isnot(None))
            .where(OrganicKeyword.keyword.isnot(None))
        )

        result = await self.session.execute(query)
        rows = result.scalars().all()

        keywords = []
        for kw in rows:
            keywords.append({
                'keyword': kw.keyword,
                'url': kw.url,
                'position': kw.position or 100,
                'volume': kw.volume or 0,
                'traffic': kw.traffic or 0,
                'parent_topic': kw.parent_topic,
            })

        return keywords

    def _detect_exact_cannibalization(self, keywords: List[Dict]) -> List[Dict]:
        """
        Find exact same keywords ranking with different URLs
        """
        # Group by keyword (case-insensitive)
        keyword_groups = defaultdict(list)

        for kw in keywords:
            keyword_lower = kw['keyword'].lower()
            keyword_groups[keyword_lower].append(kw)

        # Find keywords with multiple URLs
        cannibalization_issues = []

        for keyword, rankings in keyword_groups.items():
            unique_urls = list(set(r['url'] for r in rankings))

            if len(unique_urls) > 1:
                # Sort by position (best first)
                rankings_sorted = sorted(rankings, key=lambda x: x['position'])

                cannibalization_issues.append({
                    'keyword': keyword,
                    'competing_urls': len(unique_urls),
                    'urls': unique_urls[:5],  # Top 5 URLs
                    'best_position': rankings_sorted[0]['position'],
                    'worst_position': rankings_sorted[-1]['position'],
                    'volume': rankings_sorted[0]['volume'],
                    'traffic': sum(r['traffic'] for r in rankings),
                    'rankings': rankings_sorted,
                    'severity': self._classify_severity(len(unique_urls), rankings_sorted[0]['position']),
                    'recommended_canonical': rankings_sorted[0]['url'],  # Best performing URL
                })

        # Sort by severity and traffic potential
        cannibalization_issues.sort(
            key=lambda x: (x['severity_score'], x['volume']),
            reverse=True
        )

        return cannibalization_issues

    def _classify_severity(self, url_count: int, best_position: int) -> Dict:
        """
        Classify cannibalization severity
        """
        # More URLs = more severe
        # Better ranking = more important to fix (closer to page 1)

        severity_score = 0

        # URL count component
        if url_count >= 5:
            severity_score += 50
            level = "CRITICAL"
        elif url_count >= 3:
            severity_score += 30
            level = "HIGH"
        else:
            severity_score += 10
            level = "MODERATE"

        # Position component (closer to page 1 = more important)
        if best_position <= 10:
            severity_score += 40
        elif best_position <= 20:
            severity_score += 30
        elif best_position <= 50:
            severity_score += 20
        else:
            severity_score += 10

        return {
            'level': level,
            'score': severity_score,
        }

    def _detect_cluster_cannibalization(self, keywords: List[Dict]) -> List[Dict]:
        """
        Find parent topics where multiple URLs compete
        (less severe than exact keyword cannibalization but still dilutes authority)
        """
        # Group by parent topic
        topic_groups = defaultdict(list)

        for kw in keywords:
            if kw['parent_topic']:
                topic_groups[kw['parent_topic']].append(kw)

        # Find topics with too many unique URLs
        cluster_issues = []

        for topic, rankings in topic_groups.items():
            unique_urls = list(set(r['url'] for r in rankings))
            keyword_count = len(rankings)

            # Calculate URL diversity ratio
            # Ideal: 1 hub page + spokes (1 URL per 10-20 keywords)
            ideal_urls = max(1, keyword_count // 15)
            url_diversity = len(unique_urls) / ideal_urls if ideal_urls > 0 else len(unique_urls)

            # Flag if too many URLs for the cluster size
            if url_diversity > 2:  # More than 2x ideal URL count
                # Find most common URL (likely the hub)
                url_counts = defaultdict(int)
                for r in rankings:
                    url_counts[r['url']] += 1

                hub_url = max(url_counts.items(), key=lambda x: x[1])[0]

                cluster_issues.append({
                    'parent_topic': topic,
                    'total_keywords': keyword_count,
                    'unique_urls': len(unique_urls),
                    'url_diversity_ratio': round(url_diversity, 2),
                    'ideal_url_count': ideal_urls,
                    'suggested_hub_url': hub_url,
                    'total_volume': sum(r['volume'] for r in rankings),
                    'total_traffic': sum(r['traffic'] for r in rankings),
                })

        # Sort by diversity ratio
        cluster_issues.sort(key=lambda x: x['url_diversity_ratio'], reverse=True)

        return cluster_issues

    def _calculate_impact(
        self,
        exact_issues: List[Dict],
        cluster_issues: List[Dict]
    ) -> Dict:
        """
        Calculate overall impact of cannibalization
        """
        # Count affected keywords
        exact_keywords = sum(len(issue['rankings']) for issue in exact_issues)
        cluster_keywords = sum(issue['total_keywords'] for issue in cluster_issues)

        # Estimate traffic loss from cannibalization
        # Assumption: consolidating could improve avg position by 3-5 ranks
        # Position improvement → CTR improvement → more traffic

        estimated_loss = 0
        for issue in exact_issues:
            # If best position is 8 and you have 3 URLs competing,
            # consolidation could move you to position 5-6
            # Calculate traffic delta
            current_traffic = issue['traffic']
            potential_improvement = min(issue['best_position'] - 1, 5)  # Max 5 position improvement
            potential_traffic = current_traffic * (1 + potential_improvement * 0.1)  # 10% per position
            estimated_loss += (potential_traffic - current_traffic)

        return {
            'total_keywords_affected': exact_keywords,
            'total_clusters_affected': len(cluster_issues),
            'estimated_traffic_loss': round(estimated_loss, 0),
            'fix_priority': 'HIGH' if len(exact_issues) > 20 else 'MODERATE' if len(exact_issues) > 5 else 'LOW',
        }

    def _generate_recommendations(
        self,
        exact_issues: List[Dict],
        cluster_issues: List[Dict]
    ) -> List[Dict]:
        """
        Generate specific consolidation recommendations
        """
        recommendations = []

        # Top exact cannibalization issues
        for issue in exact_issues[:10]:
            recommendations.append({
                'keyword': issue['keyword'],
                'action': 'CONSOLIDATE',
                'canonical_url': issue['recommended_canonical'],
                'redirect_urls': [url for url in issue['urls'] if url != issue['recommended_canonical']],
                'expected_improvement': f"Position {issue['best_position']} → {max(1, issue['best_position'] - 3)}",
                'priority': issue['severity']['level'],
            })

        return recommendations

    async def _generate_ai_insight(
        self,
        exact_issues: List[Dict],
        cluster_issues: List[Dict],
        impact: Dict
    ) -> Dict:
        """
        Generate AI strategic insight
        """

        exact_summary = "\n".join([
            f"- \"{i['keyword']}\": {i['competing_urls']} URLs competing (best: pos {i['best_position']})"
            for i in exact_issues[:10]
        ]) if exact_issues else "None found"

        cluster_summary = "\n".join([
            f"- {c['parent_topic']}: {c['unique_urls']} URLs for {c['total_keywords']} keywords (ratio: {c['url_diversity_ratio']}x)"
            for c in cluster_issues[:5]
        ]) if cluster_issues else "None found"

        prompt = f"""
Analyze this keyword cannibalization analysis:

EXACT KEYWORD CANNIBALIZATION ({len(exact_issues)} issues):
{exact_summary}

CLUSTER CANNIBALIZATION ({len(cluster_issues)} issues):
{cluster_summary}

IMPACT:
- Keywords affected: {impact['total_keywords_affected']}
- Estimated traffic loss: {impact['estimated_traffic_loss']:,.0f}/month
- Fix priority: {impact['fix_priority']}

Provide:

1. CANNIBALIZATION DIAGNOSIS
   - How bad is the cannibalization problem?
   - What's causing it?
   - Why is it hurting rankings?

2. CONSOLIDATION STRATEGY
   - Which pages to consolidate first?
   - Redirect vs. canonical vs. noindex?
   - How to choose the "winner" URL?

3. IMPLEMENTATION PLAN
   - Step-by-step consolidation process
   - How to preserve link equity?
   - What to do with content from "loser" pages?

4. PREVENTION
   - How to prevent future cannibalization?
   - Content planning best practices
   - Internal linking structure

Be specific about HOW to consolidate and WHY it will improve rankings.
        """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="cannibalization_detector",
            use_complex_model=True
        )

        return ai_result

    def _classify_severity(self, url_count: int, best_position: int) -> Dict:
        """
        Classify cannibalization severity
        """
        severity_score = 0

        if url_count >= 5:
            severity_score += 50
            level = "CRITICAL"
        elif url_count >= 3:
            severity_score += 30
            level = "HIGH"
        else:
            severity_score += 10
            level = "MODERATE"

        if best_position <= 10:
            severity_score += 40
        elif best_position <= 20:
            severity_score += 30
        elif best_position <= 50:
            severity_score += 20
        else:
            severity_score += 10

        return {
            'level': level,
            'score': severity_score,
        }
