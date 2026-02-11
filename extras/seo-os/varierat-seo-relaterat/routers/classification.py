"""
Intent Classification API Routes
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.intent_classifier import IntentClassifier
from app.logger import get_logger

logger = get_logger()
router = APIRouter()

# Initialize model
intent_classifier = IntentClassifier()


class ClassifyRequest(BaseModel):
    """Request model for intent classification"""
    query: str = Field(..., description="Search query or keyword to classify", min_length=1, max_length=500)
    explain: bool = Field(default=False, description="Include explanation of intent type")


class ClassifyBatchRequest(BaseModel):
    """Request model for batch classification"""
    queries: List[str] = Field(..., description="List of queries to classify", min_items=1, max_items=100)


class ClassificationResponse(BaseModel):
    """Response model for classification"""
    query: str
    intent: str
    confidence: float
    probabilities: dict
    explanation: Optional[str] = None


class BatchClassificationResponse(BaseModel):
    """Response model for batch classification"""
    results: List[ClassificationResponse]
    total: int


@router.post("/classify-intent", response_model=ClassificationResponse)
async def classify_intent(request: ClassifyRequest):
    """
    Classify search intent for a single query

    Returns the predicted intent (Commercial, Informational, Navigational, or Transactional)
    with confidence scores for each category.
    """
    try:
        logger.info(f"Classifying intent for query: {request.query}")

        result = intent_classifier.classify(request.query)

        response = ClassificationResponse(
            query=result['query'],
            intent=result['intent'],
            confidence=result['confidence'],
            probabilities=result['probabilities']
        )

        if request.explain:
            response.explanation = intent_classifier.get_intent_explanation(result['intent'])

        return response

    except Exception as e:
        logger.error(f"Error in intent classification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )


@router.post("/classify-intent/batch", response_model=BatchClassificationResponse)
async def classify_intent_batch(request: ClassifyBatchRequest):
    """
    Classify search intent for multiple queries

    Efficiently processes multiple queries in batch for better performance.
    """
    try:
        logger.info(f"Batch classifying {len(request.queries)} queries")

        results = intent_classifier.classify_batch(request.queries)

        response_results = [
            ClassificationResponse(
                query=r['query'],
                intent=r['intent'],
                confidence=r['confidence'],
                probabilities=r['probabilities']
            )
            for r in results
        ]

        return BatchClassificationResponse(
            results=response_results,
            total=len(response_results)
        )

    except Exception as e:
        logger.error(f"Error in batch classification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch classification failed: {str(e)}"
        )


@router.get("/intents", response_model=dict)
async def get_intent_types():
    """
    Get available intent types and their descriptions

    Returns all possible intent classifications with explanations.
    """
    from app.config import INTENT_LABELS

    intents = {}
    for label in INTENT_LABELS:
        intents[label] = intent_classifier.get_intent_explanation(label)

    return {
        "intent_types": intents,
        "total": len(intents)
    }
