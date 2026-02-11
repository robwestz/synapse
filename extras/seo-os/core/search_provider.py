"""
Search Provider Framework
Standardizes search execution for analysis tools.
"""
import logging
import time
import random
import os
import requests
import json
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    rank: int
    title: str
    link: str
    snippet: str
    source: str = "google"
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

@dataclass
class SearchResponse:
    query: str
    timestamp: str
    results: List[SearchResult]
    provider: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "query": self.query,
            "timestamp": self.timestamp,
            "results": [r.to_dict() for r in self.results],
            "provider": self.provider,
            "metadata": self.metadata
        }

class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, num_results: int = 10, **kwargs) -> SearchResponse:
        pass

    def refine_results(self, response: SearchResponse, config: Dict) -> List[Dict]:
        """
        Applies recipe filters (organic only) and projects selected fields.
        """
        raw_results = [r.to_dict() for r in response.results]
        filters = config.get("filters", {})
        fields = config.get("fields", [])

        # 1. Organic Filtering
        if filters.get("organic_only", False):
            # Remove typical ad footprints
            refined = [r for r in raw_results if "googleadservices" not in r['link'] and "aclk" not in r['link']]
        else:
            refined = raw_results

        # 2. Field Projection
        if fields:
            final = []
            for r in refined:
                # Always ensure rank exists if requested or as a baseline
                row = {k: v for k, v in r.items() if k in fields}
                
                # Special handling for derived fields
                if "domain" in fields:
                    try: row["domain"] = r['link'].split("/")[2]
                    except: row["domain"] = "unknown"
                
                if "date" in fields:
                    row["date"] = r.get("extra_data", {}).get("date", "")
                
                final.append(row)
            return final
        
        return refined

class DuckDuckGoProvider(SearchProvider):
    """
    Uses duckduckgo_search (ddgs) as a proxy for 'Google-like' results.
    Includes rate limiting to avoid blocks.
    """
    def search(self, query: str, num_results: int = 10, **kwargs) -> SearchResponse:
        # SAFETY: Sleep randomly 1-3 seconds between calls to act human
        time.sleep(random.uniform(1.0, 3.0))
        
        results = []
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                region = kwargs.get('region', 'wt-wt')
                ddg_results = ddgs.text(query, region=region, max_results=num_results)
                
                for i, r in enumerate(ddg_results):
                    results.append(SearchResult(
                        rank=i+1,
                        title=r.get('title', ''),
                        link=r.get('href', ''),
                        snippet=r.get('body', ''),
                        source="duckduckgo"
                    ))
                    
        except ImportError:
            return self._error_response(query, "Missing dependency: duckduckgo-search")
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return self._error_response(query, str(e))

        return SearchResponse(
            query=query,
            timestamp=datetime.now().isoformat(),
            results=results,
            provider="duckduckgo",
            metadata={"count": len(results)}
        )

    def _error_response(self, query, error):
        return SearchResponse(
            query=query,
            timestamp=datetime.now().isoformat(),
            results=[],
            provider="duckduckgo",
            metadata={"error": error}
        )

class SerperProvider(SearchProvider):
    """
    Uses Serper.dev API (Google Wrapper).
    Pros: High volume, fast, real Google data.
    Cons: Requires API key.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        
    def search(self, query: str, num_results: int = 10, **kwargs) -> SearchResponse:
        if not self.api_key:
            return SearchResponse(
                query=query,
                timestamp=datetime.now().isoformat(),
                results=[],
                provider="serper",
                metadata={"error": "Missing SERPER_API_KEY"}
            )
            
        url = "https://google.serper.dev/search"
        payload = json.dumps({
            "q": query,
            "num": num_results,
            "gl": kwargs.get("region", "se")[-2:] # Extract 'se' from 'se-sv'
        })
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            response.raise_for_status()
            data = response.json()
            
            results = []
            organic = data.get("organic", [])
            for i, r in enumerate(organic):
                results.append(SearchResult(
                    rank=r.get("position", i+1),
                    title=r.get("title", ""),
                    link=r.get("link", ""),
                    snippet=r.get("snippet", ""),
                    source="google_api",
                    extra_data={"date": r.get("date", "")}
                ))
                
            return SearchResponse(
                query=query,
                timestamp=datetime.now().isoformat(),
                results=results,
                provider="serper",
                metadata={"count": len(results), "credits_used": 1}
            )
            
        except Exception as e:
            logger.error(f"Serper API failed: {e}")
            return SearchResponse(
                query=query,
                timestamp=datetime.now().isoformat(),
                results=[],
                provider="serper",
                metadata={"error": str(e)}
            )

class MockProvider(SearchProvider):
    def search(self, query: str, num_results: int = 10, **kwargs) -> SearchResponse:
        results = []
        for i in range(num_results):
            results.append(SearchResult(
                rank=i+1,
                title=f"Mock Result {i+1} for {query}",
                link=f"https://example.com/result-{i+1}",
                snippet=f"This is a simulated description for result {i+1} regarding {query}...",
                source="mock"
            ))
        
        return SearchResponse(
            query=query,
            timestamp=datetime.now().isoformat(),
            results=results,
            provider="mock",
            metadata={"note": "Simulated data"}
        )

def get_provider(name: str = "ddg", api_key: Optional[str] = None) -> SearchProvider:
    if name == "mock":
        return MockProvider()
    elif name == "serper":
        return SerperProvider(api_key)
    elif name == "ddg":
        return DuckDuckGoProvider()
    else:
        # Default to DDG if unknown
        return DuckDuckGoProvider()