"""
Nexus ML Client
Adapter to communicate with the high-performance ML Service (FastAPI).
"""
import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class NexusMLClient:
    def __init__(self, base_url: str = "http://localhost:8003/api/v1"):
        self.base_url = base_url

    def check_health(self) -> bool:
        try:
            response = requests.get(f"{self.base_url.replace('/api/v1', '')}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

    def classify_intent(self, query: str) -> Dict[str, Any]:
        """Calls the BERT-based intent classifier."""
        try:
            response = requests.post(
                f"{self.base_url}/classify-intent",
                json={"query": query},
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ML Service Intent Error: {e}")
            return {}

    def cluster_keywords(self, keywords: List[str]) -> Dict[str, Any]:
        """Calls the Word2Vec + K-means clustering service."""
        try:
            response = requests.post(
                f"{self.base_url}/cluster-keywords",
                json={"keywords": keywords},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ML Service Clustering Error: {e}")
            return {}

    def score_content(self, content: str, title: str, keywords: List[str]) -> Dict[str, Any]:
        """Calls the LightGBM content quality scorer."""
        try:
            response = requests.post(
                f"{self.base_url}/score-content",
                json={
                    "content": content,
                    "title": title,
                    "keywords": keywords
                },
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ML Service Scoring Error: {e}")
            return {}

# Singleton instance
ml_client = NexusMLClient()
