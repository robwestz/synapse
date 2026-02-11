"""
SERP Lens Core — Main orchestrator for semantic intelligence.

Coordinates all components to produce enhanced PREFLIGHT data:
1. Google intelligence (PAA, related searches)
2. Target fingerprint (schema, keywords)
3. Publisher profile (topics, authority)
4. Semantic bridge analysis

Usage:
    from serp_lens import SerpLens

    lens = SerpLens()
    result = await lens.analyze(
        publisher_domain="sportligan.se",
        target_url="https://example.com/product",
        anchor_text="produktnyckelord"
    )

    # Get LLM-ready constraints
    constraints = result.get_llm_constraints()
"""

import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

from .config import SerpLensConfig, get_config
from .models import (
    SerpLensResult,
    GoogleIntelligence,
    TargetFingerprint,
    PublisherProfile,
    SemanticBridge
)
from .google_scraper import GoogleScraper
from .target_parser import TargetParser
from .publisher_sampler import PublisherSampler
from .publisher_sampler_light import PublisherSamplerLight
from .semantic_engine import SemanticEngine


class SerpLens:
    """
    Main entry point for SERP Lens semantic intelligence.

    Orchestrates all components and produces a unified result
    that enhances BACOWR's PREFLIGHT phase.
    """

    def __init__(self, config: Optional[SerpLensConfig] = None, light_mode: bool = True):
        """
        Initialize SERP Lens with optional custom configuration.

        Args:
            config: Custom configuration. If None, uses default.
            light_mode: If True (default), use fast publisher profiling.
                        Set False for deeper RSS/sitemap analysis.
        """
        self.config = config or get_config()
        self.light_mode = light_mode

        # Initialize components
        self._google_scraper = GoogleScraper(self.config.google)
        self._target_parser = TargetParser(self.config.target)

        # Use light publisher sampler by default (10x faster)
        if light_mode:
            self._publisher_sampler = PublisherSamplerLight(self.config.publisher)
        else:
            self._publisher_sampler = PublisherSampler(self.config.publisher)

        self._semantic_engine = SemanticEngine(self.config.semantic)

    async def analyze(
        self,
        publisher_domain: str,
        target_url: str,
        anchor_text: str,
        skip_google: bool = False,
        skip_target: bool = False,
        skip_publisher: bool = False
    ) -> SerpLensResult:
        """
        Perform full semantic analysis.

        Args:
            publisher_domain: Domain of the publisher site
            target_url: URL of the target page
            anchor_text: The anchor text to use
            skip_google: Skip Google SERP analysis (faster)
            skip_target: Skip target page analysis
            skip_publisher: Skip publisher analysis

        Returns:
            SerpLensResult with all analysis components
        """
        start_time = time.time()
        warnings: List[str] = []
        errors: List[str] = []

        # Derive search query from anchor text
        search_query = self._derive_search_query(anchor_text, target_url)

        # Run analyses (parallel when config allows)
        google_result: Optional[GoogleIntelligence] = None
        target_result: Optional[TargetFingerprint] = None
        publisher_result: Optional[PublisherProfile] = None

        if self.config.parallel_analysis:
            # Run all analyses in parallel
            tasks = []

            if not skip_google:
                tasks.append(self._safe_analyze_google(search_query, warnings, errors))
            else:
                tasks.append(self._async_none())

            if not skip_target:
                tasks.append(self._safe_analyze_target(target_url, warnings, errors))
            else:
                tasks.append(self._async_none())

            if not skip_publisher:
                tasks.append(self._safe_analyze_publisher(publisher_domain, warnings, errors))
            else:
                tasks.append(self._async_none())

            results = await asyncio.gather(*tasks)
            google_result, target_result, publisher_result = results

        else:
            # Run sequentially
            if not skip_google:
                google_result = await self._safe_analyze_google(search_query, warnings, errors)
            if not skip_target:
                target_result = await self._safe_analyze_target(target_url, warnings, errors)
            if not skip_publisher:
                publisher_result = await self._safe_analyze_publisher(publisher_domain, warnings, errors)

        # Generate semantic bridge (requires at least publisher and target)
        bridge_result: Optional[SemanticBridge] = None
        if publisher_result and target_result:
            try:
                bridge_result = self._semantic_engine.analyze(
                    publisher=publisher_result,
                    target=target_result,
                    google=google_result,
                    anchor_text=anchor_text
                )
            except Exception as e:
                errors.append(f"Semantic bridge analysis failed: {str(e)}")

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Determine completeness
        is_complete = all([
            google_result is not None or skip_google,
            target_result is not None or skip_target,
            publisher_result is not None or skip_publisher,
            bridge_result is not None
        ])

        return SerpLensResult(
            publisher_domain=publisher_domain,
            target_url=target_url,
            anchor_text=anchor_text,
            analyzed_at=datetime.now(),
            analysis_duration_ms=duration_ms,
            google_intelligence=google_result,
            target_fingerprint=target_result,
            publisher_profile=publisher_result,
            semantic_bridge=bridge_result,
            is_complete=is_complete,
            warnings=warnings,
            errors=errors
        )

    async def _async_none(self) -> None:
        """Helper for parallel execution when skipping."""
        return None

    async def _safe_analyze_google(
        self,
        query: str,
        warnings: List[str],
        errors: List[str]
    ) -> Optional[GoogleIntelligence]:
        """Safely analyze Google SERP."""
        try:
            return await asyncio.wait_for(
                self._google_scraper.analyze(query),
                timeout=self.config.total_timeout_seconds
            )
        except asyncio.TimeoutError:
            warnings.append("Google analysis timed out")
            return None
        except Exception as e:
            errors.append(f"Google analysis failed: {str(e)}")
            return None

    async def _safe_analyze_target(
        self,
        url: str,
        warnings: List[str],
        errors: List[str]
    ) -> Optional[TargetFingerprint]:
        """Safely analyze target page."""
        try:
            return await asyncio.wait_for(
                self._target_parser.analyze(url),
                timeout=self.config.total_timeout_seconds
            )
        except asyncio.TimeoutError:
            warnings.append("Target analysis timed out")
            return None
        except Exception as e:
            errors.append(f"Target analysis failed: {str(e)}")
            return None

    async def _safe_analyze_publisher(
        self,
        domain: str,
        warnings: List[str],
        errors: List[str]
    ) -> Optional[PublisherProfile]:
        """Safely analyze publisher."""
        try:
            return await asyncio.wait_for(
                self._publisher_sampler.analyze(domain),
                timeout=self.config.total_timeout_seconds
            )
        except asyncio.TimeoutError:
            warnings.append("Publisher analysis timed out")
            return None
        except Exception as e:
            errors.append(f"Publisher analysis failed: {str(e)}")
            return None

    def _derive_search_query(self, anchor_text: str, target_url: str) -> str:
        """
        Derive a search query from anchor text and target URL.

        The query should represent what a user might search for
        to find content related to the anchor.
        """
        # Start with anchor text
        query = anchor_text

        # If anchor is very short or generic, enhance with URL keywords
        if len(anchor_text.split()) < 2:
            # Extract keywords from URL path
            from urllib.parse import urlparse
            path = urlparse(target_url).path
            path_words = path.strip("/").replace("-", " ").replace("_", " ").split("/")
            path_keywords = [w for w in path_words if len(w) > 2]

            if path_keywords:
                query = f"{anchor_text} {' '.join(path_keywords[:2])}"

        return query

    # ==================== CONVENIENCE METHODS ====================

    async def quick_analyze(
        self,
        publisher_domain: str,
        target_url: str,
        anchor_text: str
    ) -> Dict[str, Any]:
        """
        Quick analysis returning just LLM constraints.

        This is a convenience method for integration with BACOWR.
        Returns a dict ready to be included in PREFLIGHT output.
        """
        result = await self.analyze(
            publisher_domain=publisher_domain,
            target_url=target_url,
            anchor_text=anchor_text
        )

        return result.get_llm_constraints()

    async def analyze_distance_only(
        self,
        publisher_domain: str,
        target_url: str
    ) -> Dict[str, Any]:
        """
        Quick semantic distance analysis (no Google scraping).

        Useful for bulk pre-screening of publisher-target pairings.
        """
        result = await self.analyze(
            publisher_domain=publisher_domain,
            target_url=target_url,
            anchor_text="",  # Not needed for distance
            skip_google=True
        )

        if result.semantic_bridge:
            return {
                "distance": result.semantic_bridge.raw_distance,
                "category": result.semantic_bridge.distance_category.value,
                "viable": result.semantic_bridge.distance_category.value not in ["unrelated"]
            }

        return {
            "distance": 0.0,
            "category": "unknown",
            "viable": False
        }


# ==================== STANDALONE FUNCTIONS ====================


async def analyze(
    publisher_domain: str,
    target_url: str,
    anchor_text: str
) -> SerpLensResult:
    """
    Standalone analysis function.

    Usage:
        from serp_lens.core import analyze
        result = await analyze("sportligan.se", "https://...", "anchor")
    """
    lens = SerpLens()
    return await lens.analyze(
        publisher_domain=publisher_domain,
        target_url=target_url,
        anchor_text=anchor_text
    )


def analyze_sync(
    publisher_domain: str,
    target_url: str,
    anchor_text: str
) -> SerpLensResult:
    """
    Synchronous wrapper for analysis.

    Usage:
        from serp_lens.core import analyze_sync
        result = analyze_sync("sportligan.se", "https://...", "anchor")
    """
    return asyncio.run(analyze(
        publisher_domain=publisher_domain,
        target_url=target_url,
        anchor_text=anchor_text
    ))


# ==================== PREFLIGHT+ INTEGRATION ====================


class PreflightPlus:
    """
    Integration layer for BACOWR PREFLIGHT enhancement.

    Wraps SerpLens and formats output specifically for
    BACOWR's PREFLIGHT phase consumption.
    """

    def __init__(self):
        self._lens = SerpLens()

    async def enhance_preflight(
        self,
        publisher_domain: str,
        target_url: str,
        anchor_text: str
    ) -> Dict[str, Any]:
        """
        Generate PREFLIGHT+ data for BACOWR.

        Returns a dict formatted for direct inclusion in
        BACOWR's PREFLIGHT SUMMARY output.
        """
        result = await self._lens.analyze(
            publisher_domain=publisher_domain,
            target_url=target_url,
            anchor_text=anchor_text
        )

        # Format for BACOWR consumption
        output = {
            "serp_lens_version": "3.0.0",
            "analysis_complete": result.is_complete,
            "analysis_duration_ms": result.analysis_duration_ms
        }

        # Google signals
        if result.google_intelligence:
            g = result.google_intelligence
            output["google_signals"] = {
                "paa_questions": [q.question for q in g.paa_questions[:5]],
                "related_concepts": [r.query for r in g.related_searches[:8]],
                "detected_intent": g.detected_intent.value,
                "key_entities": g.dominant_entities[:5],
                "serp_features": {
                    "has_featured_snippet": g.has_featured_snippet,
                    "has_knowledge_panel": g.has_knowledge_panel,
                    "is_ymyl": g.is_ymyl
                }
            }

        # Semantic bridge
        if result.semantic_bridge:
            b = result.semantic_bridge
            output["semantic_intelligence"] = {
                "distance": {
                    "score": round(b.raw_distance, 3),
                    "category": b.distance_category.value
                },
                "bridge_required": b.distance_category.value in ["distant", "unrelated"],
                "top_bridges": [
                    {
                        "concept": s.concept,
                        "confidence": s.confidence.value,
                        "rationale": s.rationale
                    }
                    for s in b.suggestions[:3]
                ],
                "constraints": {
                    "optimal_angle": b.recommended_angle,
                    "entities_to_weave": b.required_entities[:5],
                    "entities_to_avoid": b.forbidden_entities[:5]
                },
                "trust_link_guidance": {
                    "base_on": b.trust_link_topics[:5],
                    "never": b.trust_link_avoid[:3]
                }
            }

        # Publisher profile summary
        if result.publisher_profile:
            p = result.publisher_profile
            output["publisher_intelligence"] = {
                "identity": p.site_name or p.domain,
                "primary_topics": p.primary_topics[:5],
                "recent_focus": p.recent_article_topics[:5],
                "confidence": round(p.confidence, 2)
            }

        # Target fingerprint summary
        if result.target_fingerprint:
            t = result.target_fingerprint
            output["target_intelligence"] = {
                "title": t.title[:100] if t.title else None,
                "primary_entity": t.primary_entity_type,
                "main_keywords": t.main_keywords[:5],
                "page_type": {
                    "is_ecommerce": t.is_ecommerce,
                    "has_reviews": t.has_reviews
                }
            }

        # Warnings and errors
        if result.warnings:
            output["warnings"] = result.warnings
        if result.errors:
            output["errors"] = result.errors

        return output

    def enhance_preflight_sync(
        self,
        publisher_domain: str,
        target_url: str,
        anchor_text: str
    ) -> Dict[str, Any]:
        """Synchronous wrapper for PREFLIGHT+ enhancement."""
        return asyncio.run(self.enhance_preflight(
            publisher_domain=publisher_domain,
            target_url=target_url,
            anchor_text=anchor_text
        ))


# Export convenience instance
preflight_plus = PreflightPlus()
