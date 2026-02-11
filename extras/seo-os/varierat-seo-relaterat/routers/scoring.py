"""
Content Scoring API Routes
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.models.content_scorer import ContentScorer
from app.logger import get_logger

logger = get_logger()
router = APIRouter()

# Initialize model
content_scorer = ContentScorer()


class ScoreRequest(BaseModel):
    """Request model for content scoring"""
    content: str = Field(..., description="Content to score (HTML or text)", min_length=10)
    title: Optional[str] = Field(default="", description="Page title")
    keywords: Optional[List[str]] = Field(default=None, description="Target keywords")
    url: Optional[str] = Field(default="", description="Page URL")


class ScoreResponse(BaseModel):
    """Response model for content scoring"""
    overall_score: float
    grade: str
    factor_scores: Dict[str, float]
    features: dict
    recommendations: List[str]


@router.post("/score-content", response_model=ScoreResponse)
async def score_content(request: ScoreRequest):
    """
    Score content quality based on SEO factors

    Analyzes content and returns a score from 0-100 along with detailed
    factor breakdowns and improvement recommendations.
    """
    try:
        logger.info(f"Scoring content (length: {len(request.content)} chars)")

        result = content_scorer.score_content(
            content=request.content,
            title=request.title,
            keywords=request.keywords,
            url=request.url
        )

        return ScoreResponse(**result)

    except Exception as e:
        logger.error(f"Error scoring content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content scoring failed: {str(e)}"
        )


@router.get("/scoring/factors", response_model=dict)
async def get_scoring_factors():
    """
    Get all content quality factors used in scoring

    Returns the list of factors that contribute to the overall content score.
    """
    from app.config import QUALITY_FACTORS

    return {
        "factors": QUALITY_FACTORS,
        "descriptions": {
            "readability": "Ease of reading and understanding the content",
            "keyword_density": "Optimal use of target keywords",
            "content_depth": "Comprehensive coverage of the topic",
            "heading_structure": "Proper use of headings and subheadings",
            "media_presence": "Inclusion of images, videos, and other media",
            "internal_links": "Links to other pages on the same website",
            "external_links": "Links to authoritative external sources",
            "freshness": "Recency and up-to-date nature of content"
        }
    }
