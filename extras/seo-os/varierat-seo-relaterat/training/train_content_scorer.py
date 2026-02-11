"""
Training Script for Content Scoring Model
Train LightGBM model for content quality scoring
"""
import lightgbm as lgb
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import os

from app.config import get_settings
from app.logger import get_logger
from app.utils.feature_extraction import ContentFeatureExtractor

settings = get_settings()
logger = get_logger()


class ContentScorerTrainer:
    """Trainer for content quality scoring model"""

    def __init__(self):
        self.model = None
        self.feature_extractor = ContentFeatureExtractor()
        self.feature_names = []

    def prepare_data(self, data_path: str) -> tuple:
        """
        Load and prepare training data

        Expected CSV format: content, title, keywords, quality_score
        """
        logger.info(f"Loading data from {data_path}")

        # Load data
        df = pd.read_csv(data_path)

        # Validate columns
        required_cols = ['content', 'quality_score']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"CSV must have columns: {required_cols}")

        logger.info(f"Loaded {len(df)} samples")

        # Extract features
        features_list = []

        for idx, row in df.iterrows():
            if idx % 100 == 0:
                logger.info(f"Extracting features: {idx}/{len(df)}")

            try:
                features = self.feature_extractor.extract_features(
                    content=row['content'],
                    title=row.get('title', ''),
                    keywords=row.get('keywords', '').split(',') if row.get('keywords') else [],
                    url=row.get('url', '')
                )

                # Extract numeric features
                feature_values = self._extract_feature_values(features)
                features_list.append(feature_values)

            except Exception as e:
                logger.error(f"Error extracting features for row {idx}: {e}")
                features_list.append([0] * 10)  # Default values

        # Create feature dataframe
        X = pd.DataFrame(features_list, columns=self.feature_names)
        y = df['quality_score'].values

        # Validate scores
        y = np.clip(y, settings.CONTENT_SCORE_MIN, settings.CONTENT_SCORE_MAX)

        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        logger.info(f"Training samples: {len(X_train)}, Validation samples: {len(X_val)}")

        return X_train, X_val, y_train, y_val

    def _extract_feature_values(self, features: dict) -> list:
        """Extract numeric feature values in consistent order"""
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

        # Store feature names (first time only)
        if not self.feature_names:
            self.feature_names = [
                'word_count',
                'avg_sentence_length',
                'readability_score',
                'keyword_density',
                'heading_count',
                'image_count',
                'internal_link_count',
                'external_link_count',
                'paragraph_count',
                'unique_words_ratio'
            ]

        return feature_list

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: np.ndarray,
        X_val: pd.DataFrame,
        y_val: np.ndarray,
        output_path: str = None
    ):
        """
        Train the content scoring model

        Args:
            X_train: Training features
            y_train: Training labels (quality scores)
            X_val: Validation features
            y_val: Validation labels
            output_path: Path to save model
        """
        logger.info("Training LightGBM content scorer...")

        # Create datasets
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

        # Parameters
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': 0
        }

        # Train model
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=500,
            valid_sets=[train_data, val_data],
            valid_names=['train', 'val'],
            callbacks=[
                lgb.early_stopping(stopping_rounds=50),
                lgb.log_evaluation(period=50)
            ]
        )

        # Evaluate
        self.evaluate(X_val, y_val)

        # Feature importance
        self._log_feature_importance()

        # Save model
        if output_path:
            self.save_model(output_path)

    def evaluate(self, X: pd.DataFrame, y: np.ndarray):
        """Evaluate model performance"""
        logger.info("Evaluating model...")

        predictions = self.model.predict(X)

        # Clip predictions
        predictions = np.clip(predictions, settings.CONTENT_SCORE_MIN, settings.CONTENT_SCORE_MAX)

        # Calculate metrics
        rmse = np.sqrt(mean_squared_error(y, predictions))
        mae = mean_absolute_error(y, predictions)
        r2 = r2_score(y, predictions)

        logger.info(f"Evaluation Metrics:")
        logger.info(f"  RMSE: {rmse:.4f}")
        logger.info(f"  MAE: {mae:.4f}")
        logger.info(f"  R²: {r2:.4f}")

        # Distribution analysis
        logger.info(f"\nPrediction Distribution:")
        logger.info(f"  Min: {predictions.min():.2f}")
        logger.info(f"  Max: {predictions.max():.2f}")
        logger.info(f"  Mean: {predictions.mean():.2f}")
        logger.info(f"  Std: {predictions.std():.2f}")

    def _log_feature_importance(self):
        """Log feature importance"""
        importance = self.model.feature_importance(importance_type='gain')
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)

        logger.info(f"\nFeature Importance:")
        logger.info(f"\n{feature_importance.to_string()}")

    def save_model(self, output_path: str):
        """Save trained model"""
        logger.info(f"Saving model to {output_path}")

        # Create directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save model
        self.model.save_model(output_path)

        logger.info("Model saved successfully")


def generate_sample_data(output_path: str, n_samples: int = 1000):
    """
    Generate sample training data for demonstration

    In production, this should be replaced with real labeled data
    """
    logger.info(f"Generating {n_samples} sample records...")

    data = []

    for i in range(n_samples):
        # Generate synthetic content
        word_count = np.random.randint(100, 3000)
        content = " ".join(["word"] * word_count)

        # Add some HTML structure
        content = f"<h1>Title</h1><p>{content}</p>"

        # Generate synthetic quality score based on features
        # (In production, use real human-labeled scores)
        base_score = 50
        if word_count > 1000:
            base_score += 20
        if word_count > 2000:
            base_score += 10

        quality_score = min(100, max(0, base_score + np.random.randint(-20, 20)))

        data.append({
            'content': content,
            'title': 'Sample Title',
            'keywords': 'keyword1,keyword2',
            'quality_score': quality_score
        })

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)

    logger.info(f"Sample data saved to {output_path}")


def main():
    """Main training function"""
    # Configuration
    DATA_PATH = "data/content_scoring_data.csv"
    OUTPUT_PATH = os.path.join(settings.MODEL_PATH, "content_scorer.txt")

    # Generate sample data if needed
    if not os.path.exists(DATA_PATH):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        generate_sample_data(DATA_PATH, n_samples=500)

    # Initialize trainer
    trainer = ContentScorerTrainer()

    # Prepare data
    X_train, X_val, y_train, y_val = trainer.prepare_data(DATA_PATH)

    # Train model
    trainer.train(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        output_path=OUTPUT_PATH
    )

    logger.info("Training pipeline complete!")


if __name__ == "__main__":
    main()
