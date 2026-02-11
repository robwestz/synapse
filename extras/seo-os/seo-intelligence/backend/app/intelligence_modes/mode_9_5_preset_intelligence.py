"""
MODE 9.5: Preset Intelligence Packs
Pre-configured analysis bundles for common use cases
"""

from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_engine import AIEngine
from .mode_1_1_cluster_dominance import ClusterDominanceAnalyzer
from .mode_1_5_intent_gap import IntentGapAnalyzer
from .mode_3_1_common_linker import CommonLinkerDiscovery
from .mode_4_2_low_competition import LowCompetitionFinder
from .mode_5_1_cluster_completeness import ClusterCompletenessAnalyzer
from .mode_7_1_competitor_profile import ComprehensiveCompetitorProfiler


class PresetIntelligencePacks:
    """
    Pre-configured intelligence bundles for specific use cases

    Packs:
    1. E-commerce Domination
    2. SaaS Competitor Crusher
    3. Local SEO Supremacy
    4. Content Empire Builder
    5. Quick Win Hunter
    6. Competitive Deep Dive
    """

    def __init__(self, session: AsyncSession, user_id: str):
        self.session = session
        self.user_id = user_id
        self.ai_engine = AIEngine()

    async def execute(self, pack_name: str, **params) -> Dict[str, Any]:
        """
        Execute preset intelligence pack
        """

        packs = {
            'ecommerce_domination': self._ecommerce_pack,
            'saas_crusher': self._saas_pack,
            'local_seo': self._local_pack,
            'content_empire': self._content_pack,
            'quick_wins': self._quick_wins_pack,
            'competitive_deep_dive': self._competitive_pack,
        }

        if pack_name not in packs:
            return {
                "error": f"Unknown pack: {pack_name}",
                "available_packs": list(packs.keys())
            }

        # Execute the pack
        pack_results = await packs[pack_name](**params)

        # Generate synthesis
        synthesis = await self._generate_synthesis(pack_name, pack_results)

        return {
            "mode": "9.5_preset_intelligence_pack",
            "status": "completed",
            "pack_name": pack_name,
            "pack_description": self._get_pack_description(pack_name),
            "results": pack_results,
            "synthesis": synthesis,
        }

    async def _ecommerce_pack(self, **params) -> Dict:
        """
        E-commerce Domination Pack

        Focus:
        - Product keyword gaps
        - Transactional intent coverage
        - Competitor product portfolio
        """

        # Execute relevant modes
        intent_analyzer = IntentGapAnalyzer(self.session, self.user_id)
        intent_results = await intent_analyzer.execute()

        low_comp_finder = LowCompetitionFinder(self.session, self.user_id)
        low_comp_results = await low_comp_finder.execute(
            min_volume=500,
            max_difficulty=30
        )

        # Filter for transactional keywords
        transactional_opportunities = []
        if 'full_list' in low_comp_results:
            transactional_opportunities = [
                kw for kw in low_comp_results['full_list']
                if kw.get('intent', {}).get('transactional', False)
            ][:20]

        return {
            'intent_gap_analysis': intent_results,
            'low_competition_products': transactional_opportunities,
            'key_findings': {
                'transactional_gap': intent_results.get('intent_gaps', {}).get('transactional', {}),
                'product_opportunities': len(transactional_opportunities),
            }
        }

    async def _saas_pack(self, **params) -> Dict:
        """
        SaaS Competitor Crusher Pack

        Focus:
        - Feature comparison keywords
        - Integration keywords
        - Branded vs non-branded
        - Demo/trial keywords
        """

        cluster_analyzer = ClusterDominanceAnalyzer(self.session, self.user_id)
        cluster_results = await cluster_analyzer.execute()

        intent_analyzer = IntentGapAnalyzer(self.session, self.user_id)
        intent_results = await intent_analyzer.execute()

        # Focus on commercial intent (comparisons, reviews)
        commercial_gap = intent_results.get('intent_gaps', {}).get('commercial', {})

        return {
            'cluster_dominance': cluster_results,
            'commercial_intent_gap': commercial_gap,
            'key_findings': {
                'comparison_opportunities': commercial_gap.get('gap_keyword_count', 0),
                'traffic_potential': commercial_gap.get('missing_traffic_potential', 0),
            }
        }

    async def _local_pack(self, **params) -> Dict:
        """
        Local SEO Supremacy Pack

        Focus:
        - Geographic keyword gaps
        - Local pack presence
        - NAP consistency
        """

        cluster_analyzer = ClusterDominanceAnalyzer(self.session, self.user_id)
        cluster_results = await cluster_analyzer.execute()

        completeness_analyzer = ClusterCompletenessAnalyzer(self.session, self.user_id)
        completeness_results = await completeness_analyzer.execute()

        return {
            'cluster_analysis': cluster_results,
            'topical_completeness': completeness_results,
            'key_findings': {
                'local_cluster_coverage': 'Analysis of geographic keyword clusters',
            }
        }

    async def _content_pack(self, **params) -> Dict:
        """
        Content Empire Builder Pack

        Focus:
        - Topical authority gaps
        - Cluster completeness
        - Content depth benchmarking
        """

        completeness_analyzer = ClusterCompletenessAnalyzer(self.session, self.user_id)
        completeness_results = await completeness_analyzer.execute()

        cluster_analyzer = ClusterDominanceAnalyzer(self.session, self.user_id)
        cluster_results = await cluster_analyzer.execute()

        return {
            'cluster_completeness': completeness_results,
            'cluster_opportunities': cluster_results,
            'key_findings': {
                'incomplete_clusters': len(completeness_results.get('partial_clusters', [])),
                'content_gaps': len(cluster_results.get('top_opportunities', [])),
                'avg_completeness': completeness_results.get('summary', {}).get('avg_completeness', 0),
            }
        }

    async def _quick_wins_pack(self, **params) -> Dict:
        """
        Quick Win Hunter Pack

        Focus:
        - Low competition high volume
        - Low-hanging fruit
        - Fast ranking opportunities
        """

        low_comp_finder = LowCompetitionFinder(self.session, self.user_id)
        low_comp_results = await low_comp_finder.execute(
            min_volume=1000,
            max_difficulty=25,
            max_competitor_dr=45
        )

        return {
            'quick_win_opportunities': low_comp_results,
            'key_findings': {
                'total_opportunities': len(low_comp_results.get('full_list', [])),
                'estimated_traffic': low_comp_results.get('summary', {}).get('avg_volume', 0),
            }
        }

    async def _competitive_pack(self, competitor_domain: str = None, **params) -> Dict:
        """
        Competitive Deep Dive Pack

        Focus:
        - Comprehensive competitor profile
        - Common linker discovery
        - Cluster dominance comparison
        """

        if not competitor_domain:
            return {
                'error': 'competitor_domain parameter required for this pack'
            }

        profiler = ComprehensiveCompetitorProfiler(self.session, self.user_id)
        profile_results = await profiler.execute(competitor_domain)

        linker_discovery = CommonLinkerDiscovery(self.session, self.user_id)
        linker_results = await linker_discovery.execute()

        return {
            'competitor_profile': profile_results,
            'common_linkers': linker_results,
            'key_findings': {
                'threat_level': profile_results.get('profile', {}).get('overall_strength_score', {}).get('threat_level', ''),
                'link_opportunities': len(linker_results.get('common_linkers', [])),
            }
        }

    def _get_pack_description(self, pack_name: str) -> str:
        """
        Get description for each pack
        """
        descriptions = {
            'ecommerce_domination': "Analyze product keyword gaps, transactional intent, and competitor product portfolios",
            'saas_crusher': "Identify feature comparison opportunities, integration keywords, and demo/trial content gaps",
            'local_seo': "Discover geographic keyword gaps, local pack opportunities, and location-based content needs",
            'content_empire': "Build topical authority through cluster completeness and content depth analysis",
            'quick_wins': "Find low-hanging fruit - high volume, low competition keywords for fast wins",
            'competitive_deep_dive': "Complete competitor intelligence with link opportunities and strategic analysis",
        }
        return descriptions.get(pack_name, "Custom intelligence pack")

    async def _generate_synthesis(self, pack_name: str, results: Dict) -> Dict:
        """
        Generate AI synthesis of pack results
        """

        prompt = f"""
Synthesize this {pack_name.replace('_', ' ').title()} intelligence pack:

PACK RESULTS SUMMARY:
{self._format_results_for_ai(results)}

Provide:

1. TOP 3 IMMEDIATE ACTIONS
   - What to do first?
   - Why these actions?

2. STRATEGIC PRIORITIES
   - Where to focus resources?
   - What's the biggest opportunity?

3. IMPLEMENTATION ROADMAP
   - Week 1-2 actions
   - Month 1 goals
   - Quarter 1 targets

4. SUCCESS METRICS
   - How to measure progress?
   - What KPIs to track?

Be specific and actionable. This is a ready-to-execute plan.
        """

        ai_result = await self.ai_engine.generate_insight(
            prompt=prompt,
            mode=f"preset_pack_{pack_name}",
            use_complex_model=True
        )

        return ai_result

    def _format_results_for_ai(self, results: Dict) -> str:
        """
        Format results for AI prompt
        """
        key_findings = results.get('key_findings', {})

        formatted = []
        for key, value in key_findings.items():
            formatted.append(f"- {key.replace('_', ' ').title()}: {value}")

        return "\n".join(formatted) if formatted else "No key findings available"

    @staticmethod
    def get_available_packs() -> List[Dict]:
        """
        Return list of available preset packs
        """
        return [
            {
                "pack_id": "ecommerce_domination",
                "name": "E-commerce Domination",
                "description": "Product keyword gaps, transactional intent, competitor products",
                "best_for": "Online stores, product-based businesses",
                "modes_included": ["Intent Gap", "Low Competition Finder", "Cluster Dominance"],
            },
            {
                "pack_id": "saas_crusher",
                "name": "SaaS Competitor Crusher",
                "description": "Feature comparisons, integrations, branded analysis",
                "best_for": "SaaS companies, software products",
                "modes_included": ["Cluster Dominance", "Intent Gap", "Commercial Analysis"],
            },
            {
                "pack_id": "local_seo",
                "name": "Local SEO Supremacy",
                "description": "Geographic keywords, local pack, location-based content",
                "best_for": "Local businesses, multi-location companies",
                "modes_included": ["Cluster Analysis", "Topical Completeness", "Geographic Gaps"],
            },
            {
                "pack_id": "content_empire",
                "name": "Content Empire Builder",
                "description": "Topical authority, cluster completeness, content depth",
                "best_for": "Publishers, content marketers, authority sites",
                "modes_included": ["Cluster Completeness", "Cluster Dominance", "Content Depth"],
            },
            {
                "pack_id": "quick_wins",
                "name": "Quick Win Hunter",
                "description": "Low competition, high volume, fast ranking opportunities",
                "best_for": "Quick results, limited budgets, new sites",
                "modes_included": ["Low Competition Finder", "Snippet Vulnerability", "Intent Analysis"],
            },
            {
                "pack_id": "competitive_deep_dive",
                "name": "Competitive Deep Dive",
                "description": "Full competitor analysis, link opportunities, strategic intel",
                "best_for": "Competitive markets, strategic planning",
                "modes_included": ["Competitor Profile", "Common Linker", "Moat Analysis"],
                "requires_params": ["competitor_domain"],
            },
        ]
