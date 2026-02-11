"""
LightGBM-based Content Quality Scorer
Scores content quality from 0-100 based on multiple SEO factors
"""
import lightgbm as lgb
import numpy as np
from typing import Dict, Optional, List
from app.config import get_settings, QUALITY_FACTORS
from app.logger import get_logger
from app.utils.feature_extraction import ContentFeatureExtractor

settings = get_settings()
logger = get_logger()


class ContentScorer:
    """LightGBM-based content quality scoring"""

    def __init__(self):
        self.model: Optional[lgb.Booster] = None
        self.feature_extractor = ContentFeatureExtractor()
        self.is_loaded = False

    def load_model(self, model_path: Optional[str] = None):
        """Load LightGBM model"""
        try:
            logger.info("Loading LightGBM content scorer...")

            if model_path:
                self.model = lgb.Booster(model_file=model_path)
            else:
                # Use default heuristic-based scoring if no trained model
                logger.warning("No trained model found, using heuristic scoring")
                self.model = None

            self.is_loaded = True
            logger.info("Content scorer loaded successfully")

        except Exception as e:
            logger.error(f"Error loading content scorer: {e}")
            # Fall back to heuristic scoring
            self.model = None
            self.is_loaded = True

    def score_content(
        self,
        content: str,
        title: str = "",
        keywords: Optional[List[str]] = None,
        url: str = ""
    ) -> Dict:
        """
        Score content quality

        Args:
            content: HTML or text content
            title: Page title
            keywords: Target keywords
            url: Page URL

        Returns:
            Dict with overall score and factor breakdowns
        """
        if not self.is_loaded:
            self.load_model()

        try:
            # Extract features
            features = self.feature_extractor.extract_features(
                content=content,
                title=title,
                keywords=keywords or [],
                url=url
            )

            if self.model:
                # Use trained model
                feature_values = self._prepare_features(features)
                score = float(self.model.predict([feature_values])[0])
                score = np.clip(score, settings.CONTENT_SCORE_MIN, settings.CONTENT_SCORE_MAX)
            else:
                # Use heuristic scoring
                score = self._heuristic_score(features)

            # Calculate factor scores
            factor_scores = self._calculate_factor_scores(features)

            # Generate recommendations
            recommendations = self._generate_recommendations(factor_scores, features)

            result = {
                "overall_score": round(score, 2),
                "grade": self._get_grade(score),
                "factor_scores": factor_scores,
                "features": features,
                "recommendations": recommendations
            }

            logger.debug(f"Content scored: {score:.2f}/100")

            return result

        except Exception as e:
            logger.error(f"Error scoring content: {e}")
            raise

    def _prepare_features(self, features: Dict) -> List[float]:
        """Prepare features for model prediction"""
        # Extract numeric features in consistent order
        feature_list = [
            features.get('word_count', 0),
            features.get('avg_sentence_length', 0),
            features.get('readability_score', 0),
            features.get('keyword_density', 0),
            features.get('heading_count', 0),
            features.get('image_count', 0),
            features.get('internal_link_count', 0),
            features.get('external_link_count', 0),
            features.get('paragraph_count', 0),
            features.get('unique_words_ratio', 0)
        ]
        return feature_list

    def _heuristic_score(self, features: Dict) -> float:
        """Calculate heuristic score based on features"""
        score = 0.0
        max_score = 100.0

        # Word count (0-20 points)
        word_count = features.get('word_count', 0)
        if word_count >= 2000:
            score += 20
        elif word_count >= 1000:
            score += 15
        elif word_count >= 500:
            score += 10
        elif word_count >= 300:
            score += 5

        # Readability (0-15 points)
        readability = features.get('readability_score', 0)
        if 60 <= readability <= 80:
            score += 15
        elif 50 <= readability < 90:
            score += 10
        else:
            score += 5

        # Keyword optimization (0-15 points)
        keyword_density = features.get('keyword_density', 0)
        if 0.01 <= keyword_density <= 0.03:
            score += 15
        elif 0.005 <= keyword_density <= 0.05:
            score += 10
        else:
            score += 5

        # Heading structure (0-15 points)
        heading_count = features.get('heading_count', 0)
        if heading_count >= 5:
            score += 15
        elif heading_count >= 3:
            score += 10
        elif heading_count >= 1:
            score += 5

        # Media presence (0-10 points)
        image_count = features.get('image_count', 0)
        if image_count >= 3:
            score += 10
        elif image_count >= 1:
            score += 5

        # Internal links (0-10 points)
        internal_links = features.get('internal_link_count', 0)
        if internal_links >= 5:
            score += 10
        elif internal_links >= 2:
            score += 7
        elif internal_links >= 1:
            score += 3

        # External links (0-10 points)
        external_links = features.get('external_link_count', 0)
        if 2 <= external_links <= 10:
            score += 10
        elif external_links >= 1:
            score += 5

        # Content structure (0-5 points)
        paragraph_count = features.get('paragraph_count', 0)
        if paragraph_count >= 5:
            score += 5
        elif paragraph_count >= 3:
            score += 3

        return min(score, max_score)

    def _calculate_factor_scores(self, features: Dict) -> Dict[str, float]:
        """Calculate individual factor scores"""
        scores = {}

        # Readability
        readability = features.get('readability_score', 0)
        scores['readability'] = min(100, (readability / 80) * 100) if readability > 0 else 0

        # Keyword density
        kd = features.get('keyword_density', 0)
        optimal_kd = 0.02
        scores['keyword_density'] = max(0, 100 - abs(kd - optimal_kd) * 5000)

        # Content depth
        word_count = features.get('word_count', 0)
        scores['content_depth'] = min(100, (word_count / 2000) * 100)

        # Heading structure
        heading_count = features.get('heading_count', 0)
        scores['heading_structure'] = min(100, (heading_count / 8) * 100)

        # Media presence
        image_count = features.get('image_count', 0)
        scores['media_presence'] = min(100, (image_count / 5) * 100)

        # Internal links
        internal_links = features.get('internal_link_count', 0)
        scores['internal_links'] = min(100, (internal_links / 8) * 100)

        # External links
        external_links = features.get('external_link_count', 0)
        scores['external_links'] = min(100, (external_links / 5) * 100)

        # Freshness (placeholder)
        scores['freshness'] = 100.0

        return {k: round(v, 2) for k, v in scores.items()}

    def _generate_recommendations(self, factor_scores: Dict, features: Dict) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        if factor_scores.get('readability', 100) < 60:
            recommendations.append("Improve readability: use shorter sentences and simpler words")

        if factor_scores.get('keyword_density', 100) < 50:
            recommendations.append("Optimize keyword usage: include target keywords naturally")

        if factor_scores.get('content_depth', 100) < 50:
            recommendations.append("Expand content: add more detailed information and examples")

        if factor_scores.get('heading_structure', 100) < 50:
            recommendations.append("Add more headings: break content into clear sections")

        if factor_scores.get('media_presence', 100) < 50:
            recommendations.append("Add images/media: include relevant visuals to enhance content")

        if factor_scores.get('internal_links', 100) < 50:
            recommendations.append("Add internal links: link to related content on your site")

        if factor_scores.get('external_links', 100) < 50:
            recommendations.append("Add authoritative sources: link to credible external resources")

        return recommendations

    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
