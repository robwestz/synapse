"""
SERP API Client - Online Verifier for Entity Atlas.

Switchable "turbo" module that improves Intent, Entity, and Cluster accuracy.
All SERP functionality is ADDITIVE - never a hard dependency for output.

Configuration:
- serp_mode: OFF | ON_DEMAND | ALWAYS_ON
- Budget-controlled per project/run
- Cacheable with TTL
"""

from __future__ import annotations
import sys
import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from urllib.request import urlopen, Request
from urllib.error import URLError
import re

sys.path.insert(0, str(__file__).rsplit("clients", 1)[0].rstrip("/\\"))

from core.canonical_types import EntityType


class SerpMode(str, Enum):
    OFF = "OFF"
    ON_DEMAND = "ON_DEMAND"
    ALWAYS_ON = "ALWAYS_ON"


class SerpProvider(str, Enum):
    NONE = "none"
    SERPAPI = "serpapi"
    DATAFORSEO = "dataforseo"
    MOCK = "mock"


@dataclass
class SerpConfig:
    """SERP API configuration per project."""
    mode: SerpMode = SerpMode.OFF
    provider: SerpProvider = SerpProvider.NONE
    api_key: Optional[str] = None
    
    # Budget controls
    budget_daily_requests: int = 100
    budget_monthly_requests: int = 2000
    max_keywords_per_run: int = 50
    
    # Locale defaults
    country: str = "SE"
    language: str = "sv"
    
    # Cache settings
    cache_ttl_days: int = 7
    use_cache: bool = True


@dataclass
class SerpResult:
    """Single SERP result."""
    rank: int
    url: str
    domain: str
    title: str
    snippet: str
    page_type: str  # guide, category, product, brand, review, etc.


@dataclass
class SerpFeatures:
    """SERP features present."""
    has_paa: bool = False
    has_featured_snippet: bool = False
    has_local_pack: bool = False
    has_knowledge_panel: bool = False
    has_shopping: bool = False
    has_video: bool = False
    paa_questions: List[str] = field(default_factory=list)


@dataclass
class PageTypeDistribution:
    """Distribution of page types in SERP."""
    guide: float = 0.0
    category: float = 0.0
    product: float = 0.0
    brand: float = 0.0
    review: float = 0.0
    comparison: float = 0.0
    listicle: float = 0.0
    other: float = 0.0


@dataclass
class SerpObservation:
    """Complete SERP observation for a keyword."""
    keyword_id: str
    keyword: str
    country: str
    language: str
    snapshot_date: str
    
    provider: SerpProvider
    features: SerpFeatures
    top_results: List[SerpResult]
    page_type_distribution: PageTypeDistribution
    homogeneity_score: float  # 0-1, how uniform is the SERP
    
    # Inferred from SERP
    inferred_intent: Optional[str] = None
    inferred_archetype: Optional[str] = None
    dominant_entity_hints: List[str] = field(default_factory=list)
    
    # Meta
    cached: bool = False
    cost_credits: float = 0.0


@dataclass
class FetchMetadata:
    """Metadata for SERP fetch operation."""
    request_count: int = 0
    cached_count: int = 0
    error_count: int = 0
    total_cost_credits: float = 0.0
    keywords_processed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE TYPE CLASSIFIER (Rule-based v1)
# ═══════════════════════════════════════════════════════════════════════════════

PAGE_TYPE_PATTERNS = {
    "guide": {
        "url": ["/guide", "/hur-", "/how-", "/tutorial", "/steg-for-steg"],
        "title": ["hur ", "guide", "steg för steg", "tutorial", "så gör du"]
    },
    "category": {
        "url": ["/kategori/", "/category/", "/produkter/", "/products/"],
        "title": ["produkter", "products", "alla ", "shop"]
    },
    "product": {
        "url": ["/produkt/", "/product/", "/p/", "/item/"],
        "title": ["köp ", "pris", "kr", "sek", "rea"]
    },
    "review": {
        "url": ["/recension", "/review", "/test-", "/omdome"],
        "title": ["recension", "review", "test", "omdöme", "betyg"]
    },
    "comparison": {
        "url": ["/jamfor", "/compare", "/vs/"],
        "title": ["vs", "jämför", "compare", "bästa", "top 10", "top 5"]
    },
    "listicle": {
        "url": ["/lista", "/list", "/basta-"],
        "title": ["bästa", "top ", "10 ", "5 ", "lista"]
    },
    "brand": {
        "url": ["/om-oss", "/about", "/kontakt"],
        "title": ["officiell", "official", "™", "®"]
    }
}


def classify_page_type(url: str, title: str) -> str:
    """Classify page type from URL and title patterns."""
    url_lower = url.lower()
    title_lower = title.lower()
    
    scores = {pt: 0 for pt in PAGE_TYPE_PATTERNS}
    
    for page_type, patterns in PAGE_TYPE_PATTERNS.items():
        for pattern in patterns.get("url", []):
            if pattern in url_lower:
                scores[page_type] += 2
        for pattern in patterns.get("title", []):
            if pattern in title_lower:
                scores[page_type] += 3
    
    best_type = max(scores, key=scores.get)
    if scores[best_type] > 0:
        return best_type
    return "other"


def calculate_homogeneity(page_types: List[str]) -> float:
    """Calculate how homogeneous the SERP is (0-1)."""
    if not page_types:
        return 0.0
    
    from collections import Counter
    counts = Counter(page_types)
    most_common_count = counts.most_common(1)[0][1]
    
    return most_common_count / len(page_types)


# ═══════════════════════════════════════════════════════════════════════════════
# SERP API CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

class SerpApiClient:
    """
    SERP API Client with switchable providers.
    
    Rule: All SERP functionality is ADDITIVE - never a hard dependency.
    """
    
    def __init__(self, config: SerpConfig):
        self.config = config
        self._cache: Dict[str, SerpObservation] = {}
        self._usage_today: int = 0
        self._usage_month: int = 0
    
    def _cache_key(self, keyword: str, country: str, language: str) -> str:
        """Generate cache key."""
        return hashlib.sha1(f"{keyword}|{country}|{language}".encode()).hexdigest()[:16]
    
    def _get_from_cache(self, keyword: str, country: str, language: str) -> Optional[SerpObservation]:
        """Get cached observation if valid."""
        if not self.config.use_cache:
            return None
        
        key = self._cache_key(keyword, country, language)
        obs = self._cache.get(key)
        
        if obs:
            cache_date = datetime.fromisoformat(obs.snapshot_date)
            if datetime.now() - cache_date < timedelta(days=self.config.cache_ttl_days):
                obs.cached = True
                return obs
        
        return None
    
    def _save_to_cache(self, obs: SerpObservation):
        """Save observation to cache."""
        key = self._cache_key(obs.keyword, obs.country, obs.language)
        self._cache[key] = obs
    
    def can_fetch(self) -> tuple[bool, str]:
        """Check if we can make more requests."""
        if self.config.mode == SerpMode.OFF:
            return False, "SERP mode is OFF"
        
        if self._usage_today >= self.config.budget_daily_requests:
            return False, "Daily budget exhausted"
        
        if self._usage_month >= self.config.budget_monthly_requests:
            return False, "Monthly budget exhausted"
        
        return True, "OK"
    
    def estimate_cost(self, keyword_count: int) -> Dict[str, Any]:
        """Estimate cost before fetching."""
        effective_count = min(keyword_count, self.config.max_keywords_per_run)
        
        # Assume some will be cached
        estimated_cached = int(effective_count * 0.3) if self.config.use_cache else 0
        estimated_requests = effective_count - estimated_cached
        
        credits_per_request = 1.0  # Adjust based on provider
        
        return {
            "keywords": keyword_count,
            "effective_keywords": effective_count,
            "estimated_cached": estimated_cached,
            "estimated_requests": estimated_requests,
            "estimated_cost_credits": estimated_requests * credits_per_request,
            "daily_budget_remaining": self.config.budget_daily_requests - self._usage_today
        }
    
    def fetch(
        self,
        keywords: List[str],
        country: Optional[str] = None,
        language: Optional[str] = None,
        force_refresh: bool = False
    ) -> tuple[List[SerpObservation], FetchMetadata]:
        """
        Fetch SERP data for keywords.
        
        Returns observations and metadata about the fetch operation.
        """
        country = country or self.config.country
        language = language or self.config.language
        
        can, reason = self.can_fetch()
        if not can:
            return [], FetchMetadata(errors=[reason])
        
        observations = []
        meta = FetchMetadata()
        
        # Limit to max per run
        keywords = keywords[:self.config.max_keywords_per_run]
        
        for keyword in keywords:
            meta.keywords_processed.append(keyword)
            
            # Check cache first
            if not force_refresh:
                cached = self._get_from_cache(keyword, country, language)
                if cached:
                    observations.append(cached)
                    meta.cached_count += 1
                    continue
            
            # Fetch from provider
            try:
                obs = self._fetch_single(keyword, country, language)
                if obs:
                    self._save_to_cache(obs)
                    observations.append(obs)
                    meta.request_count += 1
                    meta.total_cost_credits += obs.cost_credits
                    self._usage_today += 1
                    self._usage_month += 1
            except Exception as e:
                meta.error_count += 1
                meta.errors.append(f"{keyword}: {str(e)}")
        
        return observations, meta
    
    def _fetch_single(self, keyword: str, country: str, language: str) -> Optional[SerpObservation]:
        """Fetch single keyword from provider."""
        if self.config.provider == SerpProvider.MOCK:
            return self._mock_fetch(keyword, country, language)
        elif self.config.provider == SerpProvider.SERPAPI:
            return self._serpapi_fetch(keyword, country, language)
        elif self.config.provider == SerpProvider.DATAFORSEO:
            return self._dataforseo_fetch(keyword, country, language)
        else:
            return None
    
    def _mock_fetch(self, keyword: str, country: str, language: str) -> SerpObservation:
        """Generate mock SERP data for testing."""
        from core.canonical_types import generate_keyword_id
        
        # Generate realistic mock results
        mock_results = [
            SerpResult(
                rank=i+1,
                url=f"https://example{i}.com/{keyword.replace(' ', '-')}",
                domain=f"example{i}.com",
                title=f"{keyword.title()} - Guide {i+1}",
                snippet=f"Här hittar du allt om {keyword}...",
                page_type=classify_page_type(f"/guide/{keyword}", f"{keyword} guide")
            )
            for i in range(10)
        ]
        
        page_types = [r.page_type for r in mock_results]
        
        return SerpObservation(
            keyword_id=generate_keyword_id(keyword.lower(), country, language),
            keyword=keyword,
            country=country,
            language=language,
            snapshot_date=datetime.now().isoformat(),
            provider=SerpProvider.MOCK,
            features=SerpFeatures(
                has_paa=True,
                paa_questions=[f"Vad är {keyword}?", f"Hur fungerar {keyword}?"]
            ),
            top_results=mock_results,
            page_type_distribution=self._calculate_distribution(page_types),
            homogeneity_score=calculate_homogeneity(page_types),
            cost_credits=0.0
        )
    
    def _serpapi_fetch(self, keyword: str, country: str, language: str) -> Optional[SerpObservation]:
        """Fetch from SerpAPI."""
        if not self.config.api_key:
            raise ValueError("SerpAPI requires api_key")
        
        # Implementation would call SerpAPI here
        # For now, fall back to mock
        return self._mock_fetch(keyword, country, language)
    
    def _dataforseo_fetch(self, keyword: str, country: str, language: str) -> Optional[SerpObservation]:
        """Fetch from DataForSEO."""
        if not self.config.api_key:
            raise ValueError("DataForSEO requires api_key")
        
        # Implementation would call DataForSEO here
        # For now, fall back to mock
        return self._mock_fetch(keyword, country, language)
    
    def _calculate_distribution(self, page_types: List[str]) -> PageTypeDistribution:
        """Calculate page type distribution from list."""
        if not page_types:
            return PageTypeDistribution()
        
        from collections import Counter
        counts = Counter(page_types)
        total = len(page_types)
        
        return PageTypeDistribution(
            guide=counts.get("guide", 0) / total,
            category=counts.get("category", 0) / total,
            product=counts.get("product", 0) / total,
            brand=counts.get("brand", 0) / total,
            review=counts.get("review", 0) / total,
            comparison=counts.get("comparison", 0) / total,
            listicle=counts.get("listicle", 0) / total,
            other=counts.get("other", 0) / total
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ONLINE VERIFIER
# ═══════════════════════════════════════════════════════════════════════════════

class OnlineVerifier:
    """
    Uses SERP data to verify/upgrade offline attributions.
    
    Only runs when:
    - serp_mode != OFF
    - Budget allows
    - Confidence thresholds require verification
    """
    
    def __init__(self, client: SerpApiClient):
        self.client = client
    
    def should_verify(
        self,
        intent_confidence: float,
        entity_confidence: float,
        cluster_conflict: bool = False
    ) -> bool:
        """Determine if SERP verification should run."""
        if self.client.config.mode == SerpMode.OFF:
            return False
        
        if self.client.config.mode == SerpMode.ALWAYS_ON:
            return True
        
        # ON_DEMAND: only verify low confidence or conflicts
        if intent_confidence < 0.7:
            return True
        if entity_confidence < 0.6:
            return True
        if cluster_conflict:
            return True
        
        return False
    
    def verify_intent(self, keyword: str, offline_intent: str, serp: SerpObservation) -> tuple[str, float, str]:
        """
        Verify intent using SERP evidence.
        
        Returns: (verified_intent, confidence, evidence_source)
        """
        # Analyze page type distribution
        dist = serp.page_type_distribution
        
        # Strong signals from SERP
        if dist.category + dist.product > 0.5:
            if offline_intent in ("TRANS", "COMMERCIAL"):
                return offline_intent, 0.9, "serp_confirms"
            else:
                return "COMMERCIAL", 0.8, "serp_override"
        
        if dist.guide + dist.review > 0.6:
            if offline_intent == "INFO":
                return "INFO", 0.9, "serp_confirms"
            elif offline_intent == "COMMERCIAL":
                return "COMMERCIAL", 0.85, "serp_hybrid"  # Guides can be commercial
        
        if serp.features.has_local_pack:
            return "LOCAL", 0.9, "serp_feature"
        
        # Default: keep offline with slight boost
        return offline_intent, 0.75, "offline_with_serp"
    
    def verify_entity_type(self, keyword: str, offline_type: str, serp: SerpObservation) -> tuple[str, float, str]:
        """Verify entity type using SERP evidence."""
        dist = serp.page_type_distribution
        
        # Product signals
        if dist.product > 0.3:
            if offline_type == "PRODUCT":
                return "PRODUCT", 0.9, "serp_confirms"
            else:
                return "PRODUCT", 0.75, "serp_suggests"
        
        # Brand signals
        if dist.brand > 0.2 or serp.features.has_knowledge_panel:
            if offline_type == "BRAND":
                return "BRAND", 0.9, "serp_confirms"
        
        return offline_type, 0.7, "offline_with_serp"


def create_serp_client(config: Optional[SerpConfig] = None) -> SerpApiClient:
    """Factory function to create SERP client."""
    if config is None:
        config = SerpConfig(mode=SerpMode.OFF)
    return SerpApiClient(config)
