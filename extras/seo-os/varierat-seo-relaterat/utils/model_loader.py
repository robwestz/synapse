"""
Model Loader and Cache Manager
Handles loading and caching of ML models
"""
import os
from typing import Dict, Optional
from app.config import get_settings
from app.logger import get_logger

settings = get_settings()
logger = get_logger()


class ModelLoader:
    """Singleton model loader and cache manager"""

    _instance = None
    _models = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
            cls._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._models = {
                'intent_classifier': None,
                'content_scorer': None,
                'keyword_clusterer': None,
                'traffic_predictor': None,
                'topic_extractor': None,
                'recommendation_engine': None
            }
            self._initialized = True

    async def initialize_models(self):
        """Initialize all models on startup"""
        logger.info("Initializing ML models...")

        try:
            # Intent Classifier
            await self.load_intent_classifier()

            # Content Scorer
            await self.load_content_scorer()

            # Keyword Clusterer
            await self.load_keyword_clusterer()

            # Traffic Predictor
            await self.load_traffic_predictor()

            # Topic Extractor
            await self.load_topic_extractor()

            # Recommendation Engine
            await self.load_recommendation_engine()

            logger.info("All models initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise

    async def load_intent_classifier(self):
        """Load intent classification model"""
        if self._models['intent_classifier'] is None:
            try:
                from app.models.intent_classifier import IntentClassifier
                logger.info("Loading intent classifier...")

                model = IntentClassifier()

                # Check for trained model
                model_path = os.path.join(settings.MODEL_PATH, 'intent_classifier')
                if os.path.exists(model_path):
                    model.load_model(model_path)
                else:
                    model.load_model()

                self._models['intent_classifier'] = model
                logger.info("Intent classifier loaded")

            except Exception as e:
                logger.error(f"Error loading intent classifier: {e}")
                # Don't raise - allow service to start with lazy loading

    async def load_content_scorer(self):
        """Load content scoring model"""
        if self._models['content_scorer'] is None:
            try:
                from app.models.content_scorer import ContentScorer
                logger.info("Loading content scorer...")

                model = ContentScorer()

                # Check for trained model
                model_path = os.path.join(settings.MODEL_PATH, 'content_scorer.txt')
                if os.path.exists(model_path):
                    model.load_model(model_path)
                else:
                    model.load_model()

                self._models['content_scorer'] = model
                logger.info("Content scorer loaded")

            except Exception as e:
                logger.error(f"Error loading content scorer: {e}")

    async def load_keyword_clusterer(self):
        """Load keyword clustering model"""
        if self._models['keyword_clusterer'] is None:
            try:
                from app.models.keyword_clusterer import KeywordClusterer
                logger.info("Loading keyword clusterer...")

                model = KeywordClusterer()

                # Check for trained model
                model_path = os.path.join(settings.MODEL_PATH, 'word2vec.model')
                if os.path.exists(model_path):
                    model.load_model(model_path)
                else:
                    model.load_model()

                self._models['keyword_clusterer'] = model
                logger.info("Keyword clusterer loaded")

            except Exception as e:
                logger.error(f"Error loading keyword clusterer: {e}")

    async def load_traffic_predictor(self):
        """Load traffic prediction model"""
        if self._models['traffic_predictor'] is None:
            try:
                from app.models.traffic_predictor import TrafficPredictor
                logger.info("Loading traffic predictor...")

                model = TrafficPredictor()

                # Check for trained model
                model_path = os.path.join(settings.MODEL_PATH, 'lstm_traffic.h5')
                if os.path.exists(model_path):
                    model.load_model(model_path)
                else:
                    model.load_model()

                self._models['traffic_predictor'] = model
                logger.info("Traffic predictor loaded")

            except Exception as e:
                logger.error(f"Error loading traffic predictor: {e}")

    async def load_topic_extractor(self):
        """Load topic extraction model"""
        if self._models['topic_extractor'] is None:
            try:
                from app.models.topic_extractor import TopicExtractor
                logger.info("Loading topic extractor...")

                model = TopicExtractor()
                model.load_model()

                self._models['topic_extractor'] = model
                logger.info("Topic extractor loaded")

            except Exception as e:
                logger.error(f"Error loading topic extractor: {e}")

    async def load_recommendation_engine(self):
        """Load recommendation engine"""
        if self._models['recommendation_engine'] is None:
            try:
                from app.models.recommendation_engine import RecommendationEngine
                logger.info("Loading recommendation engine...")

                model = RecommendationEngine()
                model.load_model()

                self._models['recommendation_engine'] = model
                logger.info("Recommendation engine loaded")

            except Exception as e:
                logger.error(f"Error loading recommendation engine: {e}")

    def get_model(self, model_name: str):
        """Get cached model by name"""
        return self._models.get(model_name)

    def get_models_status(self) -> Dict:
        """Get status of all models"""
        status = {}

        for model_name, model in self._models.items():
            if model is None:
                status[model_name] = "not_loaded"
            elif hasattr(model, 'is_loaded') and model.is_loaded:
                status[model_name] = "loaded"
            else:
                status[model_name] = "initialized"

        return {
            "models": status,
            "total_models": len(self._models),
            "loaded_count": sum(1 for s in status.values() if s == "loaded")
        }

    def clear_cache(self, model_name: Optional[str] = None):
        """Clear model cache"""
        if model_name:
            if model_name in self._models:
                self._models[model_name] = None
                logger.info(f"Cleared cache for {model_name}")
        else:
            # Clear all
            for key in self._models:
                self._models[key] = None
            logger.info("Cleared all model caches")
