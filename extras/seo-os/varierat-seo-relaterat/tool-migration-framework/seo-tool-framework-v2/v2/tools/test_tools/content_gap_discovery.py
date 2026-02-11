"""
Content Gap Discovery Service
=============================

Discovers content opportunities by analyzing competitor keywords.
This is a functional mock implementation for testing the framework.

Archetype: discoverer
Category: content
"""

import asyncio
import random
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class ContentGapDiscoveryServiceConfig:
    """Configuration for the Content Gap Discovery Service."""
    min_search_volume: int = 100
    max_difficulty: int = 70
    min_opportunity_score: int = 50
    include_questions: bool = True
    max_results: int = 100
    
    def __init__(
        self,
        min_search_volume: int = 100,
        max_difficulty: int = 70,
        min_opportunity_score: int = 50,
        include_questions: bool = True,
        max_results: int = 100,
    ):
        self.min_search_volume = min_search_volume
        self.max_difficulty = max_difficulty
        self.min_opportunity_score = min_opportunity_score
        self.include_questions = include_questions
        self.max_results = max_results


@dataclass
class ContentGap:
    """A single content gap opportunity."""
    keyword: str
    search_volume: int
    difficulty: int
    opportunity_score: int
    competitor_count: int
    competitors_ranking: List[str]
    suggested_content_type: str
    estimated_traffic: int
    intent: str  # informational, transactional, navigational


@dataclass
class ContentGapDiscoveryServiceResult:
    """Result from content gap discovery."""
    success: bool
    gaps: List[ContentGap]
    total_gaps_found: int
    avg_opportunity_score: float
    total_estimated_traffic: int
    domain_analyzed: str
    competitors_analyzed: List[str]
    processing_time_ms: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "gaps": [asdict(g) for g in self.gaps],
            "total_gaps_found": self.total_gaps_found,
            "avg_opportunity_score": self.avg_opportunity_score,
            "total_estimated_traffic": self.total_estimated_traffic,
            "domain_analyzed": self.domain_analyzed,
            "competitors_analyzed": self.competitors_analyzed,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp,
        }


class ContentGapDiscoveryService:
    """
    Service for discovering content gaps compared to competitors.
    
    This is a mock implementation that generates realistic gap analysis results
    for testing the framework. In production, this would use actual SEO APIs.
    """
    
    # Mock keyword database for realistic results
    MOCK_KEYWORDS = [
        ("seo tools comparison", "informational", "comparison"),
        ("best keyword research tool", "transactional", "listicle"),
        ("how to do technical seo audit", "informational", "guide"),
        ("backlink checker free", "transactional", "tool-page"),
        ("what is domain authority", "informational", "explainer"),
        ("content optimization tips", "informational", "guide"),
        ("local seo checklist", "informational", "checklist"),
        ("ecommerce seo strategy", "informational", "guide"),
        ("google algorithm updates 2024", "informational", "news"),
        ("schema markup generator", "transactional", "tool-page"),
        ("competitor analysis template", "transactional", "template"),
        ("link building strategies", "informational", "guide"),
        ("seo roi calculator", "transactional", "tool-page"),
        ("mobile seo best practices", "informational", "guide"),
        ("voice search optimization", "informational", "guide"),
        ("featured snippet optimization", "informational", "guide"),
        ("seo for startups", "informational", "guide"),
        ("enterprise seo platform", "transactional", "comparison"),
        ("seo reporting dashboard", "transactional", "tool-page"),
        ("rank tracking software", "transactional", "comparison"),
    ]
    
    def __init__(self, config: Optional[ContentGapDiscoveryServiceConfig] = None):
        self.config = config or ContentGapDiscoveryServiceConfig()
        self._initialized = False
        self._metrics = {
            "total_executions": 0,
            "total_gaps_found": 0,
            "avg_execution_time_ms": 0,
        }
    
    async def initialize(self) -> None:
        """Initialize the service."""
        if self._initialized:
            return
        await asyncio.sleep(0.1)
        self._initialized = True
    
    async def close(self) -> None:
        """Clean up resources."""
        self._initialized = False
    
    async def generate(self, parameters: Dict[str, Any]) -> ContentGapDiscoveryServiceResult:
        """
        Discover content gaps for a domain.
        
        Args:
            parameters: Dictionary containing:
                - domain: The domain to analyze
                - competitors: List of competitor domains
                - min_search_volume: Optional override
                - max_difficulty: Optional override
        
        Returns:
            ContentGapDiscoveryServiceResult with gaps
        """
        start_time = asyncio.get_event_loop().time()
        
        domain = parameters.get("domain", "example.com")
        competitors = parameters.get("competitors", [])
        
        # Handle string input for competitors
        if isinstance(competitors, str):
            competitors = [c.strip() for c in competitors.split("\n") if c.strip()]
        
        if not competitors:
            competitors = ["competitor1.com", "competitor2.com", "competitor3.com"]
        
        # Config overrides
        min_volume = parameters.get("min_search_volume", self.config.min_search_volume)
        max_difficulty = parameters.get("max_difficulty", self.config.max_difficulty)
        
        # Generate mock gaps
        gaps = await self._discover_gaps(domain, competitors, min_volume, max_difficulty)
        
        # Calculate aggregates
        total_traffic = sum(g.estimated_traffic for g in gaps)
        avg_opportunity = sum(g.opportunity_score for g in gaps) / len(gaps) if gaps else 0
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Update metrics
        self._metrics["total_executions"] += 1
        self._metrics["total_gaps_found"] += len(gaps)
        self._metrics["avg_execution_time_ms"] = (
            (self._metrics["avg_execution_time_ms"] * (self._metrics["total_executions"] - 1) + processing_time)
            / self._metrics["total_executions"]
        )
        
        return ContentGapDiscoveryServiceResult(
            success=True,
            gaps=gaps,
            total_gaps_found=len(gaps),
            avg_opportunity_score=round(avg_opportunity, 1),
            total_estimated_traffic=total_traffic,
            domain_analyzed=domain,
            competitors_analyzed=competitors,
            processing_time_ms=processing_time,
        )
    
    async def _discover_gaps(
        self,
        domain: str,
        competitors: List[str],
        min_volume: int,
        max_difficulty: int,
    ) -> List[ContentGap]:
        """Mock gap discovery implementation."""
        
        # Simulate API calls
        await asyncio.sleep(0.1 * len(competitors))
        
        gaps = []
        
        for keyword, intent, content_type in self.MOCK_KEYWORDS:
            # Generate deterministic random values based on keyword + domain
            seed = int(hashlib.md5(f"{keyword}{domain}".encode()).hexdigest()[:8], 16)
            random.seed(seed)
            
            volume = random.randint(500, 30000)
            difficulty = random.randint(20, 85)
            
            # Check filters
            if volume < min_volume or difficulty > max_difficulty:
                random.seed()
                continue
            
            # Calculate opportunity score
            opportunity = self._calculate_opportunity(volume, difficulty, len(competitors))
            
            if opportunity < self.config.min_opportunity_score:
                random.seed()
                continue
            
            # Determine which competitors rank
            ranking_competitors = random.sample(competitors, min(random.randint(1, 3), len(competitors)))
            
            gap = ContentGap(
                keyword=keyword,
                search_volume=volume,
                difficulty=difficulty,
                opportunity_score=opportunity,
                competitor_count=len(ranking_competitors),
                competitors_ranking=ranking_competitors,
                suggested_content_type=content_type,
                estimated_traffic=int(volume * 0.3 * (100 - difficulty) / 100),
                intent=intent,
            )
            gaps.append(gap)
            random.seed()
        
        # Sort by opportunity score
        gaps.sort(key=lambda g: g.opportunity_score, reverse=True)
        
        return gaps[:self.config.max_results]
    
    def _calculate_opportunity(
        self, 
        volume: int, 
        difficulty: int, 
        competitor_count: int
    ) -> int:
        """Calculate opportunity score (0-100)."""
        # Higher volume = higher score
        volume_score = min(volume / 300, 40)
        
        # Lower difficulty = higher score
        difficulty_score = (100 - difficulty) * 0.4
        
        # More competitors ranking = higher opportunity
        competitor_score = min(competitor_count * 5, 20)
        
        return int(volume_score + difficulty_score + competitor_score)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            **self._metrics,
            "config": vars(self.config),
            "initialized": self._initialized,
        }
    
    async def batch_process(
        self, 
        items: List[Dict[str, Any]]
    ) -> List[ContentGapDiscoveryServiceResult]:
        """Process multiple domains."""
        results = []
        for item in items:
            result = await self.generate(item)
            results.append(result)
        return results
