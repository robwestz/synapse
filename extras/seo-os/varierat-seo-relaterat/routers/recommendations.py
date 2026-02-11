"""
SEO Recommendations API Routes
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.models.recommendation_engine import RecommendationEngine
from app.models.topic_extractor import TopicExtractor
from app.logger import get_logger

logger = get_logger()
router = APIRouter()

# Initialize models
recommendation_engine = RecommendationEngine()
topic_extractor = TopicExtractor()


class RecommendationRequest(BaseModel):
    """Request model for generating recommendations"""
    analysis_data: dict = Field(..., description="Content analysis data")
    priority: str = Field(default="all", description="Filter by priority (high, medium, low, all)")


class TopicExtractionRequest(BaseModel):
    """Request model for topic extraction"""
    text: str = Field(..., description="Text to extract topics from", min_length=10)
    max_topics: int = Field(default=10, description="Maximum topics to extract", ge=1, le=50)
    include_entities: bool = Field(default=True, description="Include named entities")
    include_keyphrases: bool = Field(default=True, description="Include key phrases")


class SentimentRequest(BaseModel):
    """Request model for sentiment analysis"""
    text: str = Field(..., description="Text to analyze sentiment")


class SummaryRequest(BaseModel):
    """Request model for content summarization"""
    text: str = Field(..., description="Text to summarize", min_length=50)
    num_sentences: int = Field(default=3, description="Number of sentences in summary", ge=1, le=10)


class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    recommendations: Dict[str, List[dict]]
    summary: dict
    total_recommendations: int


@router.post("/generate-recommendations", response_model=RecommendationResponse)
async def generate_recommendations(request: RecommendationRequest):
    """
    Generate SEO recommendations

    Analyzes content and provides actionable recommendations across multiple
    categories including keyword optimization, content improvement, technical SEO,
    user experience, and link building.
    """
    try:
        logger.info("Generating SEO recommendations")

        result = recommendation_engine.generate_recommendations(
            analysis_data=request.analysis_data,
            priority=request.priority
        )

        return RecommendationResponse(**result)

    except ValueError as e:
        logger.warning(f"Recommendation generation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation generation failed: {str(e)}"
        )


@router.post("/extract-topics", response_model=dict)
async def extract_topics(request: TopicExtractionRequest):
    """
    Extract topics and entities from text

    Uses NLP to identify main topics, named entities, keywords, and content statistics.
    """
    try:
        logger.info("Extracting topics from text")

        result = topic_extractor.extract_topics(
            text=request.text,
            max_topics=request.max_topics,
            include_entities=request.include_entities,
            include_keyphrases=request.include_keyphrases
        )

        return result

    except Exception as e:
        logger.error(f"Error extracting topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Topic extraction failed: {str(e)}"
        )


@router.post("/analyze-sentiment", response_model=dict)
async def analyze_sentiment(request: SentimentRequest):
    """
    Analyze content sentiment

    Determines whether content has positive, negative, or neutral sentiment.
    """
    try:
        logger.info("Analyzing sentiment")

        result = topic_extractor.analyze_sentiment(request.text)

        return result

    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed: {str(e)}"
        )


@router.post("/extract-relationships", response_model=dict)
async def extract_relationships(request: TopicExtractionRequest):
    """
    Extract subject-verb-object relationships

    Identifies key relationships and actions mentioned in the text.
    """
    try:
        logger.info("Extracting relationships from text")

        relationships = topic_extractor.extract_relationships(request.text)

        return {
            "relationships": relationships,
            "total": len(relationships)
        }

    except Exception as e:
        logger.error(f"Error extracting relationships: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Relationship extraction failed: {str(e)}"
        )


@router.post("/extract-questions", response_model=dict)
async def extract_questions(request: TopicExtractionRequest):
    """
    Extract questions from text

    Identifies questions that can be answered or used for FAQ sections.
    """
    try:
        logger.info("Extracting questions from text")

        questions = topic_extractor.extract_questions(request.text)

        return {
            "questions": questions,
            "total": len(questions)
        }

    except Exception as e:
        logger.error(f"Error extracting questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Question extraction failed: {str(e)}"
        )


@router.post("/summarize", response_model=dict)
async def summarize_content(request: SummaryRequest):
    """
    Generate content summary

    Creates an extractive summary by selecting the most important sentences.
    """
    try:
        logger.info("Generating content summary")

        summary = topic_extractor.get_content_summary(
            text=request.text,
            num_sentences=request.num_sentences
        )

        return {
            "summary": summary,
            "original_length": len(request.text),
            "summary_length": len(summary)
        }

    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}"
        )
