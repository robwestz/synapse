"""
Keyword Clustering API Routes
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.models.keyword_clusterer import KeywordClusterer
from app.logger import get_logger

logger = get_logger()
router = APIRouter()

# Initialize model
keyword_clusterer = KeywordClusterer()


class ClusterRequest(BaseModel):
    """Request model for keyword clustering"""
    keywords: List[str] = Field(..., description="Keywords to cluster", min_items=2, max_items=1000)
    n_clusters: Optional[int] = Field(default=None, description="Number of clusters (auto if None)")
    min_cluster_size: Optional[int] = Field(default=None, description="Minimum cluster size")
    max_cluster_size: Optional[int] = Field(default=None, description="Maximum cluster size")


class SimilarKeywordsRequest(BaseModel):
    """Request model for finding similar keywords"""
    keyword: str = Field(..., description="Keyword to find similar terms for")
    top_n: int = Field(default=10, description="Number of similar keywords to return", ge=1, le=50)


class ClusterResponse(BaseModel):
    """Response model for clustering"""
    n_clusters: int
    total_keywords: int
    silhouette_score: float
    clusters: List[dict]
    cluster_themes: Dict[int, str]
    metrics: dict


@router.post("/cluster-keywords", response_model=ClusterResponse)
async def cluster_keywords(request: ClusterRequest):
    """
    Cluster keywords by semantic similarity

    Groups keywords into semantically related clusters using Word2Vec embeddings
    and K-means clustering. Automatically determines optimal number of clusters
    if not specified.
    """
    try:
        logger.info(f"Clustering {len(request.keywords)} keywords")

        result = keyword_clusterer.cluster_keywords(
            keywords=request.keywords,
            n_clusters=request.n_clusters,
            min_cluster_size=request.min_cluster_size,
            max_cluster_size=request.max_cluster_size
        )

        return ClusterResponse(**result)

    except ValueError as e:
        logger.warning(f"Clustering validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error clustering keywords: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clustering failed: {str(e)}"
        )


@router.post("/keywords/similar", response_model=dict)
async def find_similar_keywords(request: SimilarKeywordsRequest):
    """
    Find keywords similar to a given keyword

    Uses Word2Vec embeddings to find semantically similar keywords.
    """
    try:
        logger.info(f"Finding similar keywords for: {request.keyword}")

        similar = keyword_clusterer.get_similar_keywords(
            keyword=request.keyword,
            top_n=request.top_n
        )

        return {
            "keyword": request.keyword,
            "similar_keywords": [
                {"keyword": kw, "similarity": float(score)}
                for kw, score in similar
            ],
            "total": len(similar)
        }

    except ValueError as e:
        logger.warning(f"Similar keywords error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error finding similar keywords: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Similar keywords search failed: {str(e)}"
        )
