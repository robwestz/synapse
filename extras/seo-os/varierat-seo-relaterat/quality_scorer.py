"""
Quality Scorer

ML-based content quality scoring using LightGBM.
Predicts content quality before generation based on:
- Keyword characteristics
- Entity selection
- Publisher requirements
- Historical performance data

Can also score generated content post-hoc.
"""

import os
import logging
import pickle
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

import numpy as np
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Model paths
MODEL_DIR = Path(os.getenv("MODEL_DIR", "/app/models"))
QUALITY_MODEL_PATH = MODEL_DIR / "quality_scorer.lgb"
FEATURE_SCALER_PATH = MODEL_DIR / "feature_scaler.pkl"


# ═══════════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════════

class QualityFeatures(BaseModel):
    """Features for quality prediction"""
    # Keyword features
    keyword_length: int
    keyword_word_count: int
    keyword_search_volume: Optional[float] = None
    keyword_difficulty: Optional[float] = None
    
    # Entity features
    entity_count: int
    avg_entity_length: float
    entity_type_diversity: float
    
    # Content requirements
    target_word_count: int
    include_faq: bool
    outline_sections: int
    
    # Publisher match
    publisher_formality: float
    publisher_avg_words: int
    
    # Computed
    marriage_score: Optional[float] = None


class QualityPrediction(BaseModel):
    """Quality prediction result"""
    predicted_score: float  # 0-100
    confidence: float
    risk_factors: List[str]
    improvement_suggestions: List[str]
    
    # Feature importances
    top_positive_factors: List[Tuple[str, float]]
    top_negative_factors: List[Tuple[str, float]]


class ContentQualityScore(BaseModel):
    """Post-generation quality score"""
    overall_score: float
    
    # Component scores
    readability_score: float
    seo_score: float
    engagement_score: float
    accuracy_score: float
    
    # Details
    word_count_accuracy: float
    keyword_density: float
    entity_coverage: float
    heading_structure: float
    
    # Issues
    issues: List[str]
    strengths: List[str]


# ═══════════════════════════════════════════════════════════════════════════
# SCORER
# ═══════════════════════════════════════════════════════════════════════════

class QualityScorer:
    """ML-based quality scoring"""

    def __init__(self, model_path: Optional[Path] = None):
        self.model = None
        self.scaler = None
        self.model_path = model_path or QUALITY_MODEL_PATH
        
        # Try to load model
        self._load_model()

    def _load_model(self):
        """Load trained model if available"""
        try:
            if self.model_path.exists():
                import lightgbm as lgb
                self.model = lgb.Booster(model_file=str(self.model_path))
                logger.info("Loaded quality scoring model")
                
                if FEATURE_SCALER_PATH.exists():
                    with open(FEATURE_SCALER_PATH, "rb") as f:
                        self.scaler = pickle.load(f)
        except ImportError:
            logger.warning("LightGBM not installed, using rule-based scoring")
        except Exception as e:
            logger.warning(f"Could not load model: {e}")

    def predict_quality(self, features: QualityFeatures) -> QualityPrediction:
        """Predict content quality before generation"""
        
        # Extract feature vector
        feature_vector = self._extract_features(features)
        
        if self.model is not None:
            # ML prediction
            if self.scaler:
                feature_vector = self.scaler.transform([feature_vector])[0]
            
            predicted_score = float(self.model.predict([feature_vector])[0])
            predicted_score = max(0, min(100, predicted_score))
            confidence = 0.85
        else:
            # Rule-based fallback
            predicted_score = self._rule_based_prediction(features)
            confidence = 0.6
        
        # Analyze factors
        risk_factors = self._identify_risks(features)
        suggestions = self._generate_suggestions(features, predicted_score)
        positive, negative = self._analyze_factors(features)
        
        return QualityPrediction(
            predicted_score=round(predicted_score, 2),
            confidence=confidence,
            risk_factors=risk_factors,
            improvement_suggestions=suggestions,
            top_positive_factors=positive,
            top_negative_factors=negative,
        )

    def score_content(
        self,
        content: str,
        keyword: str,
        target_word_count: int,
        required_entities: List[str],
    ) -> ContentQualityScore:
        """Score generated content post-hoc"""
        
        words = content.split()
        word_count = len(words)
        
        # Calculate component scores
        readability = self._calculate_readability(content)
        seo = self._calculate_seo_score(content, keyword)
        engagement = self._calculate_engagement(content)
        accuracy = self._calculate_accuracy(content, required_entities)
        
        # Metrics
        word_count_accuracy = 1 - abs(word_count - target_word_count) / target_word_count
        word_count_accuracy = max(0, min(1, word_count_accuracy))
        
        keyword_count = content.lower().count(keyword.lower())
        keyword_density = (keyword_count / word_count) * 100 if word_count > 0 else 0
        
        covered_entities = sum(1 for e in required_entities if e.lower() in content.lower())
        entity_coverage = covered_entities / len(required_entities) if required_entities else 1.0
        
        heading_count = content.count("\n#") + content.count("<h")
        heading_structure = min(heading_count / 5, 1.0)  # Expect ~5 headings
        
        # Overall score (weighted)
        overall = (
            readability * 0.25 +
            seo * 0.30 +
            engagement * 0.20 +
            accuracy * 0.25
        )
        
        # Identify issues and strengths
        issues = []
        strengths = []
        
        if word_count_accuracy < 0.8:
            issues.append(f"Word count off target ({word_count} vs {target_word_count})")
        else:
            strengths.append("Word count on target")
        
        if keyword_density < 0.5:
            issues.append("Keyword density too low")
        elif keyword_density > 3:
            issues.append("Keyword density too high (stuffing risk)")
        else:
            strengths.append("Good keyword density")
        
        if entity_coverage < 0.8:
            issues.append(f"Missing entities: {len(required_entities) - covered_entities}")
        else:
            strengths.append("All required entities covered")
        
        if readability < 50:
            issues.append("Content may be difficult to read")
        elif readability > 70:
            strengths.append("Excellent readability")
        
        return ContentQualityScore(
            overall_score=round(overall, 2),
            readability_score=round(readability, 2),
            seo_score=round(seo, 2),
            engagement_score=round(engagement, 2),
            accuracy_score=round(accuracy, 2),
            word_count_accuracy=round(word_count_accuracy * 100, 2),
            keyword_density=round(keyword_density, 2),
            entity_coverage=round(entity_coverage * 100, 2),
            heading_structure=round(heading_structure * 100, 2),
            issues=issues,
            strengths=strengths,
        )

    def _extract_features(self, features: QualityFeatures) -> List[float]:
        """Extract numeric feature vector"""
        return [
            features.keyword_length,
            features.keyword_word_count,
            features.keyword_search_volume or 0,
            features.keyword_difficulty or 50,
            features.entity_count,
            features.avg_entity_length,
            features.entity_type_diversity,
            features.target_word_count,
            1 if features.include_faq else 0,
            features.outline_sections,
            features.publisher_formality,
            features.publisher_avg_words,
            features.marriage_score or 50,
        ]

    def _rule_based_prediction(self, features: QualityFeatures) -> float:
        """Rule-based quality prediction when model not available"""
        score = 60.0  # Base score
        
        # Entity count (optimal: 3-8)
        if 3 <= features.entity_count <= 8:
            score += 10
        elif features.entity_count > 10:
            score -= 10
        
        # Word count alignment
        if 800 <= features.target_word_count <= 2000:
            score += 5
        
        # Marriage score
        if features.marriage_score:
            score += (features.marriage_score - 50) * 0.3
        
        # Publisher match
        if features.publisher_formality > 0:
            score += 5
        
        # FAQ inclusion
        if features.include_faq:
            score += 5
        
        # Outline structure
        if features.outline_sections >= 3:
            score += 5
        
        return max(0, min(100, score))

    def _identify_risks(self, features: QualityFeatures) -> List[str]:
        """Identify risk factors"""
        risks = []
        
        if features.entity_count > 10:
            risks.append("Too many entities may result in unfocused content")
        
        if features.entity_count == 0:
            risks.append("No entities - content may lack depth")
        
        if features.marriage_score and features.marriage_score < 40:
            risks.append("Low marriage score - entities may feel forced")
        
        if features.target_word_count < 500:
            risks.append("Very short content may not rank well")
        
        if features.target_word_count > 3000:
            risks.append("Very long content may have engagement issues")
        
        return risks

    def _generate_suggestions(
        self, 
        features: QualityFeatures, 
        predicted_score: float
    ) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if predicted_score < 70:
            if features.entity_count < 3:
                suggestions.append("Add 2-3 more relevant entities")
            
            if not features.include_faq:
                suggestions.append("Include FAQ section for featured snippets")
            
            if features.outline_sections < 4:
                suggestions.append("Add more outline sections for structure")
        
        if features.marriage_score and features.marriage_score < 60:
            suggestions.append("Review entity selection for better keyword fit")
        
        return suggestions

    def _analyze_factors(
        self, 
        features: QualityFeatures
    ) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
        """Analyze positive and negative factors"""
        positive = []
        negative = []
        
        # Entity count
        if 3 <= features.entity_count <= 8:
            positive.append(("entity_count", 0.15))
        elif features.entity_count > 10:
            negative.append(("entity_count", -0.10))
        
        # Marriage score
        if features.marriage_score:
            if features.marriage_score > 70:
                positive.append(("marriage_score", 0.20))
            elif features.marriage_score < 40:
                negative.append(("marriage_score", -0.15))
        
        # FAQ
        if features.include_faq:
            positive.append(("include_faq", 0.10))
        
        # Structure
        if features.outline_sections >= 4:
            positive.append(("outline_structure", 0.12))
        
        return (
            sorted(positive, key=lambda x: -x[1])[:3],
            sorted(negative, key=lambda x: x[1])[:3],
        )

    def _calculate_readability(self, content: str) -> float:
        """Calculate readability score"""
        words = content.split()
        word_count = len(words)
        
        if word_count == 0:
            return 0
        
        sentences = content.count('.') + content.count('!') + content.count('?')
        sentences = max(sentences, 1)
        
        # Approximate syllables
        syllables = sum(self._count_syllables(word) for word in words)
        
        # Flesch Reading Ease
        if word_count > 0 and sentences > 0:
            fre = 206.835 - (1.015 * (word_count / sentences)) - (84.6 * (syllables / word_count))
            return max(0, min(100, fre))
        
        return 50

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        prev_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        
        if word.endswith('e'):
            count -= 1
        
        return max(count, 1)

    def _calculate_seo_score(self, content: str, keyword: str) -> float:
        """Calculate SEO score"""
        score = 50.0
        lower_content = content.lower()
        lower_keyword = keyword.lower()
        
        # Keyword in first 100 words
        first_100 = " ".join(content.split()[:100]).lower()
        if lower_keyword in first_100:
            score += 15
        
        # Keyword density (1-2% optimal)
        word_count = len(content.split())
        keyword_count = lower_content.count(lower_keyword)
        density = (keyword_count / word_count) * 100 if word_count > 0 else 0
        
        if 0.8 <= density <= 2.5:
            score += 20
        elif 0.3 <= density <= 4:
            score += 10
        
        # Headings present
        if content.count("\n#") >= 3 or content.count("<h") >= 3:
            score += 15
        
        return min(score, 100)

    def _calculate_engagement(self, content: str) -> float:
        """Calculate engagement score"""
        score = 50.0
        
        # Question marks (engagement)
        if content.count('?') >= 2:
            score += 10
        
        # Lists/bullets
        if content.count('\n- ') >= 3 or content.count('\n* ') >= 3:
            score += 10
        
        # Varied sentence length
        sentences = content.split('.')
        if sentences:
            lengths = [len(s.split()) for s in sentences if s.strip()]
            if lengths:
                variance = np.var(lengths) if len(lengths) > 1 else 0
                if variance > 20:  # Good variety
                    score += 15
        
        # Action words
        action_words = ['discover', 'learn', 'find', 'get', 'start', 'try']
        if any(word in content.lower() for word in action_words):
            score += 10
        
        return min(score, 100)

    def _calculate_accuracy(self, content: str, required_entities: List[str]) -> float:
        """Calculate accuracy based on entity coverage"""
        if not required_entities:
            return 80.0
        
        covered = sum(1 for e in required_entities if e.lower() in content.lower())
        coverage = covered / len(required_entities)
        
        return coverage * 100


# ═══════════════════════════════════════════════════════════════════════════
# MODEL TRAINING (utility functions)
# ═══════════════════════════════════════════════════════════════════════════

def prepare_training_data(
    samples: List[Dict[str, Any]]
) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare training data from historical generations"""
    X = []
    y = []
    
    for sample in samples:
        features = QualityFeatures(**sample["features"])
        scorer = QualityScorer()
        feature_vector = scorer._extract_features(features)
        
        X.append(feature_vector)
        y.append(sample["actual_quality_score"])
    
    return np.array(X), np.array(y)


def train_model(X: np.ndarray, y: np.ndarray, save_path: Path):
    """Train and save quality scoring model"""
    try:
        import lightgbm as lgb
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        # Create datasets
        train_data = lgb.Dataset(X_train_scaled, label=y_train)
        val_data = lgb.Dataset(X_val_scaled, label=y_val)
        
        # Parameters
        params = {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.9,
            "verbose": -1,
        }
        
        # Train
        model = lgb.train(
            params,
            train_data,
            num_boost_round=100,
            valid_sets=[val_data],
        )
        
        # Save
        save_path.parent.mkdir(parents=True, exist_ok=True)
        model.save_model(str(save_path))
        
        with open(FEATURE_SCALER_PATH, "wb") as f:
            pickle.dump(scaler, f)
        
        logger.info(f"Model saved to {save_path}")
        
    except ImportError:
        logger.error("LightGBM not installed. Install with: pip install lightgbm")
