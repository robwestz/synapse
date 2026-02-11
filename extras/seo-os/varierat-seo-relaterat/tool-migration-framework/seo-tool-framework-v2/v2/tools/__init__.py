"""
Test Tools Package
==================

Contains 5 mock implementations of SEO tools for testing the framework.
All tools follow the standardized pattern:

    @dataclass Config
    @dataclass Result (with to_dict())
    class Service:
        async initialize()
        async close()
        async analyze/generate/optimize/monitor()
        get_metrics()
        async batch_process()

Tools included:
    - keyword_clustering (analyzer)
    - content_gap_discovery (discoverer)
    - serp_volatility (monitor)
    - internal_link_optimizer (optimizer)
    - rag_content_brief (generator)
"""

from .test_tools.keyword_clustering import (
    KeywordClusteringService,
    KeywordClusteringServiceConfig,
    KeywordClusteringServiceResult,
)

from .test_tools.content_gap_discovery import (
    ContentGapDiscoveryService,
    ContentGapDiscoveryServiceConfig,
    ContentGapDiscoveryServiceResult,
)

from .test_tools.serp_volatility import (
    SerpVolatilityService,
    SerpVolatilityServiceConfig,
    SerpVolatilityServiceResult,
)

from .test_tools.internal_link_optimizer import (
    InternalLinkOptimizerService,
    InternalLinkOptimizerServiceConfig,
    InternalLinkOptimizerServiceResult,
)

from .test_tools.rag_content_brief import (
    RAGContentBriefService,
    RAGContentBriefServiceConfig,
    RAGContentBriefServiceResult,
)

__all__ = [
    # Keyword Clustering
    "KeywordClusteringService",
    "KeywordClusteringServiceConfig", 
    "KeywordClusteringServiceResult",
    
    # Content Gap Discovery
    "ContentGapDiscoveryService",
    "ContentGapDiscoveryServiceConfig",
    "ContentGapDiscoveryServiceResult",
    
    # SERP Volatility
    "SerpVolatilityService",
    "SerpVolatilityServiceConfig",
    "SerpVolatilityServiceResult",
    
    # Internal Link Optimizer
    "InternalLinkOptimizerService",
    "InternalLinkOptimizerServiceConfig",
    "InternalLinkOptimizerServiceResult",
    
    # RAG Content Brief
    "RAGContentBriefService",
    "RAGContentBriefServiceConfig",
    "RAGContentBriefServiceResult",
]
