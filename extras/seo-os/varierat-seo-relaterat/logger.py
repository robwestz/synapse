"""
Logging configuration for ML Service
"""
import sys
from loguru import logger
from app.config import get_settings

settings = get_settings()


def setup_logger():
    """Configure loguru logger"""
    # Remove default handler
    logger.remove()

    # Console handler with colors
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )

    # File handler
    logger.add(
        settings.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        rotation="100 MB",
        retention="10 days",
        compression="zip"
    )

    return logger


# Initialize logger
app_logger = setup_logger()


def get_logger():
    """Get logger instance"""
    return app_logger
