"""
FastAPI ML Service for SEO Intelligence Platform
Provides AI/ML capabilities including intent classification, content scoring,
keyword clustering, traffic prediction, and automated recommendations.
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response
import time

from app.config import get_settings
from app.logger import get_logger
from app.routers import classification, scoring, clustering, prediction, recommendations

settings = get_settings()
logger = get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('ml_service_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('ml_service_request_duration_seconds', 'Request duration', ['endpoint'])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Startup: Initialize models
    logger.info("Loading ML models...")
    try:
        from app.utils.model_loader import ModelLoader
        model_loader = ModelLoader()
        await model_loader.initialize_models()
        logger.info("All models loaded successfully")
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        logger.warning("Service starting with on-demand model loading")

    yield

    # Shutdown
    logger.info("Shutting down ML service")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI/ML Service for SEO Intelligence Platform",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_DURATION.labels(endpoint=request.url.path).observe(process_time)

    return response


# Include routers
app.include_router(classification.router, prefix="/api/v1", tags=["Classification"])
app.include_router(scoring.router, prefix="/api/v1", tags=["Scoring"])
app.include_router(clustering.router, prefix="/api/v1", tags=["Clustering"])
app.include_router(prediction.router, prefix="/api/v1", tags=["Prediction"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["Recommendations"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs",
            "classification": "/api/v1/classify-intent",
            "scoring": "/api/v1/score-content",
            "clustering": "/api/v1/cluster-keywords",
            "prediction": "/api/v1/predict-traffic",
            "recommendations": "/api/v1/generate-recommendations"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")


@app.get("/models/status", tags=["Models"])
async def models_status():
    """Check status of loaded models"""
    try:
        from app.utils.model_loader import ModelLoader
        model_loader = ModelLoader()
        status = model_loader.get_models_status()
        return status
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS
    )
