"""
Traffic Prediction API Routes
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
from app.models.traffic_predictor import TrafficPredictor
from app.logger import get_logger

logger = get_logger()
router = APIRouter()

# Initialize model
traffic_predictor = TrafficPredictor()


class TrafficDataPoint(BaseModel):
    """Single traffic data point"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    visits: int = Field(..., description="Number of visits", ge=0)

    @validator('date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")


class PredictRequest(BaseModel):
    """Request model for traffic prediction"""
    historical_data: List[TrafficDataPoint] = Field(..., description="Historical traffic data", min_items=30)
    forecast_days: Optional[int] = Field(default=7, description="Number of days to forecast", ge=1, le=30)


class SeasonalityRequest(BaseModel):
    """Request model for seasonality analysis"""
    historical_data: List[TrafficDataPoint] = Field(..., description="Historical traffic data", min_items=7)


class PredictionResponse(BaseModel):
    """Response model for traffic prediction"""
    forecast: List[dict]
    statistics: dict
    historical_summary: dict


@router.post("/predict-traffic", response_model=PredictionResponse)
async def predict_traffic(request: PredictRequest):
    """
    Predict future website traffic

    Uses LSTM neural network to forecast future traffic based on historical data.
    Requires at least 30 days of historical data for accurate predictions.
    """
    try:
        logger.info(f"Predicting traffic for {request.forecast_days} days")

        # Convert to dict format
        historical_data = [
            {"date": dp.date, "visits": dp.visits}
            for dp in request.historical_data
        ]

        result = traffic_predictor.predict_traffic(
            historical_data=historical_data,
            forecast_days=request.forecast_days
        )

        return PredictionResponse(**result)

    except ValueError as e:
        logger.warning(f"Traffic prediction validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error predicting traffic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Traffic prediction failed: {str(e)}"
        )


@router.post("/traffic/seasonality", response_model=dict)
async def analyze_seasonality(request: SeasonalityRequest):
    """
    Analyze traffic seasonality patterns

    Identifies patterns like day-of-week effects and peak traffic periods
    from historical data.
    """
    try:
        logger.info("Analyzing traffic seasonality")

        # Convert to dict format
        historical_data = [
            {"date": dp.date, "visits": dp.visits}
            for dp in request.historical_data
        ]

        result = traffic_predictor.analyze_seasonality(historical_data)

        return result

    except Exception as e:
        logger.error(f"Error analyzing seasonality: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Seasonality analysis failed: {str(e)}"
        )
