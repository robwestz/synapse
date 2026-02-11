"""
Configuration settings for ML Service
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "SEO Intelligence ML Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8003
    WORKERS: int = 2

    # Models
    MODEL_PATH: str = "/app/models"
    CACHE_MODELS: bool = True

    # BERT Configuration
    BERT_MODEL: str = "bert-base-uncased"
    BERT_MAX_LENGTH: int = 512
    BERT_BATCH_SIZE: int = 16

    # Content Scoring
    CONTENT_SCORE_MIN: int = 0
    CONTENT_SCORE_MAX: int = 100

    # Clustering
    CLUSTER_MIN_SIZE: int = 5
    CLUSTER_MAX_SIZE: int = 50
    WORD2VEC_DIM: int = 100
    WORD2VEC_WINDOW: int = 5

    # Time Series
    LSTM_SEQUENCE_LENGTH: int = 30
    LSTM_FORECAST_DAYS: int = 7

    # NLP
    SPACY_MODEL: str = "en_core_web_sm"
    MIN_TOPIC_CONFIDENCE: float = 0.5

    # Redis (for caching)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_ENABLED: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/app/logs/ml-service.log"

    # Performance
    MAX_CONTENT_LENGTH: int = 100000  # characters
    REQUEST_TIMEOUT: int = 60  # seconds

    # Feature Extraction
    MIN_WORD_LENGTH: int = 3
    MAX_FEATURES: int = 1000

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Intent classification labels
INTENT_LABELS = [
    "Commercial",
    "Informational",
    "Navigational",
    "Transactional"
]

# Content quality factors
QUALITY_FACTORS = [
    "readability",
    "keyword_density",
    "content_depth",
    "heading_structure",
    "media_presence",
    "internal_links",
    "external_links",
    "freshness"
]

# SEO recommendation types
RECOMMENDATION_TYPES = [
    "keyword_optimization",
    "content_improvement",
    "technical_seo",
    "user_experience",
    "link_building"
]
