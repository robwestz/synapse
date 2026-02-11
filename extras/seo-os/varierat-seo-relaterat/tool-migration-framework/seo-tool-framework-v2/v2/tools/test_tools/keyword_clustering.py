"""
Keyword Clustering Service
==========================

Clusters keywords by semantic similarity using embeddings.
This is a functional mock implementation for testing the framework.

Archetype: analyzer
Category: keywords
"""

import asyncio
import random
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass
class KeywordClusteringServiceConfig:
    """Configuration for the Keyword Clustering Service."""
    min_cluster_size: int = 3
    max_clusters: int = 20
    similarity_threshold: float = 0.7
    algorithm: str = "kmeans"  # kmeans, dbscan, hierarchical
    include_metrics: bool = True
    
    def __init__(
        self,
        min_cluster_size: int = 3,
        max_clusters: int = 20,
        similarity_threshold: float = 0.7,
        algorithm: str = "kmeans",
        include_metrics: bool = True,
    ):
        self.min_cluster_size = min_cluster_size
        self.max_clusters = max_clusters
        self.similarity_threshold = similarity_threshold
        self.algorithm = algorithm
        self.include_metrics = include_metrics


@dataclass
class KeywordCluster:
    """A single keyword cluster."""
    cluster_id: int
    name: str
    keywords: List[str]
    size: int
    avg_similarity: float
    suggested_pillar: str
    search_volume_total: int


@dataclass
class KeywordClusteringServiceResult:
    """Result from keyword clustering analysis."""
    success: bool
    clusters: List[KeywordCluster]
    total_keywords: int
    total_clusters: int
    unclustered_keywords: List[str]
    processing_time_ms: float
    algorithm_used: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "clusters": [asdict(c) for c in self.clusters],
            "total_keywords": self.total_keywords,
            "total_clusters": self.total_clusters,
            "unclustered_keywords": self.unclustered_keywords,
            "processing_time_ms": self.processing_time_ms,
            "algorithm_used": self.algorithm_used,
            "timestamp": self.timestamp,
        }


class KeywordClusteringService:
    """
    Service for clustering keywords by semantic similarity.
    
    This is a mock implementation that generates realistic clustering results
    for testing the framework. In production, this would use actual ML models.
    """
    
    def __init__(self, config: Optional[KeywordClusteringServiceConfig] = None):
        self.config = config or KeywordClusteringServiceConfig()
        self._initialized = False
        self._metrics = {
            "total_executions": 0,
            "total_keywords_processed": 0,
            "avg_execution_time_ms": 0,
        }
    
    async def initialize(self) -> None:
        """Initialize the service (load models, etc.)."""
        if self._initialized:
            return
        
        # Simulate model loading
        await asyncio.sleep(0.1)
        self._initialized = True
    
    async def close(self) -> None:
        """Clean up resources."""
        self._initialized = False
    
    async def analyze(self, data: Dict[str, Any]) -> KeywordClusteringServiceResult:
        """
        Analyze and cluster keywords.
        
        Args:
            data: Dictionary containing:
                - keywords: List of keywords or newline-separated string
                - min_cluster_size: Optional override for config
                - similarity_threshold: Optional override for config
        
        Returns:
            KeywordClusteringServiceResult with clusters
        """
        start_time = asyncio.get_event_loop().time()
        
        # Parse keywords
        keywords_input = data.get("keywords", [])
        if isinstance(keywords_input, str):
            keywords = [k.strip() for k in keywords_input.split("\n") if k.strip()]
        else:
            keywords = keywords_input
        
        if not keywords:
            return KeywordClusteringServiceResult(
                success=False,
                clusters=[],
                total_keywords=0,
                total_clusters=0,
                unclustered_keywords=[],
                processing_time_ms=0,
                algorithm_used=self.config.algorithm,
            )
        
        # Get config overrides
        min_cluster_size = data.get("min_cluster_size", self.config.min_cluster_size)
        similarity_threshold = data.get("similarity_threshold", self.config.similarity_threshold)
        
        # Simulate clustering (mock implementation)
        clusters = await self._mock_clustering(keywords, min_cluster_size)
        
        # Identify unclustered keywords
        clustered = set()
        for cluster in clusters:
            clustered.update(cluster.keywords)
        unclustered = [k for k in keywords if k not in clustered]
        
        # Calculate processing time
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        # Update metrics
        self._metrics["total_executions"] += 1
        self._metrics["total_keywords_processed"] += len(keywords)
        self._metrics["avg_execution_time_ms"] = (
            (self._metrics["avg_execution_time_ms"] * (self._metrics["total_executions"] - 1) + processing_time)
            / self._metrics["total_executions"]
        )
        
        return KeywordClusteringServiceResult(
            success=True,
            clusters=clusters,
            total_keywords=len(keywords),
            total_clusters=len(clusters),
            unclustered_keywords=unclustered,
            processing_time_ms=processing_time,
            algorithm_used=self.config.algorithm,
        )
    
    async def _mock_clustering(
        self, 
        keywords: List[str], 
        min_cluster_size: int
    ) -> List[KeywordCluster]:
        """Mock clustering implementation."""
        
        # Simulate processing time
        await asyncio.sleep(0.05 * len(keywords) / 10)
        
        # Group keywords by common words (simple mock logic)
        word_groups: Dict[str, List[str]] = {}
        
        for keyword in keywords:
            words = keyword.lower().split()
            # Use the most significant word as group key
            key_word = max(words, key=len) if words else "misc"
            
            if key_word not in word_groups:
                word_groups[key_word] = []
            word_groups[key_word].append(keyword)
        
        # Create clusters from groups
        clusters = []
        cluster_id = 1
        
        for key_word, group_keywords in word_groups.items():
            if len(group_keywords) >= min_cluster_size:
                # Generate realistic cluster data
                cluster = KeywordCluster(
                    cluster_id=cluster_id,
                    name=f"{key_word.title()} Keywords",
                    keywords=group_keywords,
                    size=len(group_keywords),
                    avg_similarity=round(random.uniform(0.7, 0.95), 3),
                    suggested_pillar=f"Ultimate Guide to {key_word.title()}",
                    search_volume_total=sum(
                        self._mock_search_volume(k) for k in group_keywords
                    ),
                )
                clusters.append(cluster)
                cluster_id += 1
        
        # Sort by size descending
        clusters.sort(key=lambda c: c.size, reverse=True)
        
        return clusters[:self.config.max_clusters]
    
    def _mock_search_volume(self, keyword: str) -> int:
        """Generate mock search volume based on keyword hash."""
        # Deterministic random based on keyword
        seed = int(hashlib.md5(keyword.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        volume = random.randint(100, 50000)
        random.seed()  # Reset seed
        return volume
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            **self._metrics,
            "config": asdict(self.config) if hasattr(self.config, '__dataclass_fields__') else vars(self.config),
            "initialized": self._initialized,
        }
    
    async def batch_process(
        self, 
        items: List[Dict[str, Any]]
    ) -> List[KeywordClusteringServiceResult]:
        """Process multiple keyword sets."""
        results = []
        for item in items:
            result = await self.analyze(item)
            results.append(result)
        return results
