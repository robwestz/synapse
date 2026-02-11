"""
FastAPI main application
Competitive Intelligence Maximizer - Ahrefs Obliterator
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

from app.core.database import init_db, close_db
from app.api.v1 import upload, intelligence


# Create FastAPI app
app = FastAPI(
    title="Competitive Intelligence Maximizer",
    description="Extract EVERY strategic insight Ahrefs hides. 50+ intelligence modes.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Initialize database on startup
    """
    await init_db()
    print("🚀 Competitive Intelligence Maximizer API started")
    print("📊 Database initialized")
    print("🔥 Ready to obliterate Ahrefs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Close database connections on shutdown
    """
    await close_db()
    print("👋 API shutdown complete")


# Include routers
app.include_router(upload.router, prefix="/api/v1")
app.include_router(intelligence.router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """
    API root - health check
    """
    return {
        "service": "Competitive Intelligence Maximizer",
        "status": "operational",
        "tagline": "What Ahrefs doesn't want you to discover",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "upload": "/api/v1/upload",
            "intelligence": "/api/v1/intelligence",
        }
    }


# Health check
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "database": "connected",
        "ai_engine": "ready",
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") == "true" else "An error occurred",
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
    )
