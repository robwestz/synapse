"""
MODE 3.1: Common Linker Discovery
Finds domains that link to 3+ competitors but NOT to you
These are "warm prospects" for link building
"""

from typing import Dict, List, Any, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import defaultdict

from app.models.uploads import ReferringDomain, Upload, Backlink
from app.core.ai_engine import AIEngine, PromptTemplates


class CommonLinkerDiscovery:
    """
    Identifies domains that link to multiple competitors but not you
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self, min_competitors: int = 3) -> Dict[str, Any]:
        """
        Find common linkers

        Args:
            min_competitors: Minimum number of competitors a domain must link to
        """

        # Step 1: Get your referring domains
        your_referring_domains = await self._get_referring_domains(is_primary=True)
        your_domain_set = set(rd['domain'] for rd in your_referring_domains)

        # Step 2: Get competitor referring domains
        competitor_referring_domains = await self._get_referring_domains(is_primary=False)

        # Step 3: Group by referring domain → which competitor sites they link to
        domain_to_competitors = defaultdict(set)
        domain_to_details = {}

        for rd in competitor_referring_domains:
            referring_domain = rd['domain']
            competitor_domain = rd['competitor_domain']

            domain_to_competitors[referring_domain].add(competitor_domain)

            # Keep highest DR if duplicate
            if referring_domain not in domain_to_details or rd['domain_rating'] > domain_to_details[referring_domain]['domain_rating']:
                domain_to_details[referring_domain] = {
                    'domain': referring_domain,
                    'domain_rating': rd['domain_rating'],
                    'dofollow_ref_domains': rd.get('dofollow_ref_domains'),
                    'traffic': rd.get('traffic'),
                }

        # Step 4: Find domains linking to min_competitors+ but NOT to you
        common_linkers = []

        for domain, competitors_linked in domain_to_competitors.items():
            if len(competitors_linked) >= min_competitors and domain not in your_domain_set:
                details = domain_to_details[domain]
                details['competitors_linked_to'] = list(competitors_linked)
                details['competitor_count'] = len(competitors_linked)
                details['link_opportunity_score'] = self._calculate_opportunity_score(
                    details['domain_rating'],
                    len(competitors_linked),
                    details.get('traffic', 0)
                )
                common_linkers.append(details)

        # Step 5: Sort by opportunity score
        common_linkers.sort(key=lambda x: x['link_opportunity_score'], reverse=True)

        # Step 6: Get anchor text insights for top prospects
        top_prospects = common_linkers[:20]
        anchor_insights = await self._get_anchor_insights(top_prospects)

        # Step 7: AI analysis
        ai_insight = await self._generate_ai_insight(
            top_prospects[:10],
            anchor_insights
        )

        return {
            "mode": "3.1_common_linker_discovery",
            "status": "completed",
            "summary": {
                "total_common_linkers": len(common_linkers),
                "high_authority_linkers": len([cl for cl in common_linkers if cl['domain_rating'] >= 60]),
                "avg_domain_rating": round(sum(cl['domain_rating'] for cl in common_linkers) / len(common_linkers), 1) if common_linkers else 0,
            },
            "top_opportunities": top_prospects[:20],
            "full_list": common_linkers,
            "anchor_insights": anchor_insights,
            "ai_insight": ai_insight,
        }

    async def _get_referring_domains(self, is_primary: bool) -> List[Dict]:
        """
        Get referring domains from database
        """
        query = (
            select(ReferringDomain, Upload.source_domain)
            .join(Upload, ReferringDomain.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.is_primary == is_primary)
            .where(Upload.processing_status == "completed")
            .where(ReferringDomain.domain_rating.isnot(None))
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        referring_domains = []
        for row in rows:
            rd_obj, competitor_domain = row
            referring_domains.append({
                "domain": rd_obj.domain,
                "domain_rating": rd_obj.domain_rating,
                "dofollow_ref_domains": rd_obj.dofollow_ref_domains,
                "traffic": rd_obj.traffic,
                "links_to_target": rd_obj.links_to_target,
                "competitor_domain": competitor_domain,
            })

        return referring_domains

    def _calculate_opportunity_score(
        self,
        domain_rating: int,
        competitor_count: int,
        traffic: float
    ) -> float:
        """
        Calculate link opportunity score (0-100)

        High score means:
        - High DR
        - Links to many competitors (warm prospect)
        - High traffic (relevant)
        """
        score = 0

        # Domain rating (max 50 points)
        if domain_rating >= 80:
            score += 50
        elif domain_rating >= 60:
            score += 35
        elif domain_rating >= 40:
            score += 20
        else:
            score += 10

        # Competitor count (max 30 points)
        # More competitors = warmer prospect
        if competitor_count >= 5:
            score += 30
        elif competitor_count >= 3:
            score += 20
        else:
            score += 10

        # Traffic (max 20 points)
        if traffic and traffic > 100000:
            score += 20
        elif traffic and traffic > 10000:
            score += 10

        return score

    async def _get_anchor_insights(self, top_prospects: List[Dict]) -> Dict:
        """
        Get anchor text insights for top prospects
        Helps understand what content they link to
        """
        prospect_domains = [p['domain'] for p in top_prospects[:10]]

        # Query backlinks to see anchor texts used
        query = (
            select(Backlink.referring_domain, Backlink.anchor, Backlink.target_url)
            .join(Upload, Backlink.upload_id == Upload.id)
            .where(Upload.user_id == self.user_id)
            .where(Upload.is_primary == False)  # Competitor backlinks
            .where(Backlink.referring_domain.in_(prospect_domains))
            .where(Backlink.anchor.isnot(None))
            .limit(500)
        )

        result = await self.session.execute(query)
        rows = result.fetchall()

        # Group anchors by domain
        domain_anchors = defaultdict(list)
        for referring_domain, anchor, target_url in rows:
            domain_anchors[referring_domain].append({
                "anchor": anchor,
                "target_url": target_url,
            })

        # Identify common anchor patterns
        anchor_insights = {}
        for domain, anchors in domain_anchors.items():
            anchor_texts = [a['anchor'] for a in anchors]

            # Find most common anchor patterns
            anchor_counts = defaultdict(int)
            for anchor in anchor_texts:
                if anchor and len(anchor) > 3:  # Filter out very short anchors
                    anchor_counts[anchor.lower()] += 1

            top_anchors = sorted(
                anchor_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            anchor_insights[domain] = {
                "total_links": len(anchors),
                "common_anchors": [{"text": anchor, "count": count} for anchor, count in top_anchors],
                "sample_target_urls": list(set(a['target_url'] for a in anchors))[:5],
            }

        return anchor_insights

    async def _generate_ai_insight(
        self,
        top_prospects: List[Dict],
        anchor_insights: Dict
    ) -> Dict:
        """
        Generate AI-powered link building strategy
        """

        # Enrich prospects with anchor data
        enriched_prospects = []
        for prospect in top_prospects:
            p = prospect.copy()
            if prospect['domain'] in anchor_insights:
                p['anchor_data'] = anchor_insights[prospect['domain']]
            enriched_prospects.append(p)

        prompt = PromptTemplates.backlink_common_linkers(enriched_prospects)

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode="backlink_common_linker",
            use_complex_model=True  # Complex analysis for link building
        )

        return ai_result
