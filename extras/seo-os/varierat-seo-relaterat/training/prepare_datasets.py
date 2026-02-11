"""
Dataset Preparation Utilities
Prepare and clean datasets for model training
"""
import pandas as pd
import numpy as np
import os
from typing import List, Dict
from bs4 import BeautifulSoup

from app.config import INTENT_LABELS
from app.logger import get_logger

logger = get_logger()


class DatasetPreparer:
    """Prepare datasets for training ML models"""

    def __init__(self):
        pass

    def create_intent_dataset(
        self,
        output_path: str,
        samples_per_class: int = 250
    ):
        """
        Create sample intent classification dataset

        In production, replace with real search query data
        """
        logger.info("Creating intent classification dataset...")

        data = []

        # Sample queries for each intent type
        sample_queries = {
            'Commercial': [
                'best {} for',
                'top {} reviews',
                '{} vs {}',
                'affordable {}',
                'cheap {}',
                '{} comparison',
                'buy {} online',
                '{} price comparison',
                'which {} should i buy',
                '{} deals'
            ],
            'Informational': [
                'how to {}',
                'what is {}',
                'why {}',
                '{} tutorial',
                '{} guide',
                'learn {}',
                '{} explanation',
                '{} definition',
                'understand {}',
                '{} tips'
            ],
            'Navigational': [
                '{} login',
                '{} website',
                '{} official site',
                'go to {}',
                '{} homepage',
                '{} portal',
                '{} dashboard',
                '{} account',
                '{} app',
                'open {}'
            ],
            'Transactional': [
                'buy {}',
                'purchase {}',
                'order {}',
                'download {}',
                'subscribe to {}',
                'get {}',
                'register for {}',
                'sign up {}',
                'book {}',
                'reserve {}'
            ]
        }

        # Example topics
        topics = [
            'laptop', 'smartphone', 'camera', 'headphones',
            'software', 'course', 'book', 'tool',
            'service', 'product', 'app', 'game'
        ]

        # Generate samples
        for intent, patterns in sample_queries.items():
            for _ in range(samples_per_class):
                pattern = np.random.choice(patterns)
                topic = np.random.choice(topics)

                # Fill pattern with topic
                if '{}' in pattern:
                    query = pattern.format(topic)
                else:
                    query = pattern

                data.append({
                    'query': query,
                    'intent': intent
                })

        # Create DataFrame
        df = pd.DataFrame(data)

        # Shuffle
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)

        # Save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)

        logger.info(f"Created intent dataset with {len(df)} samples")
        logger.info(f"Distribution:\n{df['intent'].value_counts()}")
        logger.info(f"Saved to {output_path}")

        return df

    def create_content_scoring_dataset(
        self,
        output_path: str,
        n_samples: int = 500
    ):
        """
        Create sample content scoring dataset

        In production, replace with real content and human-labeled quality scores
        """
        logger.info("Creating content scoring dataset...")

        data = []

        for i in range(n_samples):
            # Generate synthetic content with varying quality
            word_count = np.random.randint(100, 3000)
            heading_count = np.random.randint(0, 10)
            image_count = np.random.randint(0, 8)
            link_count = np.random.randint(0, 15)

            # Build HTML content
            content_parts = [f"<h1>Main Title {i}</h1>"]

            for h in range(heading_count):
                content_parts.append(f"<h2>Section {h}</h2>")
                words_in_section = word_count // max(heading_count, 1)
                content_parts.append(f"<p>{'Lorem ipsum dolor sit amet. ' * (words_in_section // 5)}</p>")

            for img in range(image_count):
                content_parts.append(f'<img src="image{img}.jpg" alt="Image {img}">')

            for link in range(link_count):
                content_parts.append(f'<a href="/page{link}">Link {link}</a>')

            content = '\n'.join(content_parts)

            # Calculate synthetic quality score based on features
            score = 50

            # Word count contribution
            if word_count >= 2000:
                score += 20
            elif word_count >= 1000:
                score += 10
            elif word_count < 300:
                score -= 15

            # Structure contribution
            if heading_count >= 4:
                score += 15
            elif heading_count == 0:
                score -= 10

            # Media contribution
            if image_count >= 3:
                score += 10
            elif image_count == 0:
                score -= 5

            # Links contribution
            if 3 <= link_count <= 10:
                score += 10
            elif link_count == 0:
                score -= 5

            # Add some randomness
            score += np.random.randint(-10, 10)

            # Clip score
            score = max(0, min(100, score))

            data.append({
                'content': content,
                'title': f'Content Title {i}',
                'keywords': 'keyword1,keyword2,keyword3',
                'url': f'/page/{i}',
                'quality_score': score
            })

        # Create DataFrame
        df = pd.DataFrame(data)

        # Save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)

        logger.info(f"Created content scoring dataset with {len(df)} samples")
        logger.info(f"Score distribution:\n{df['quality_score'].describe()}")
        logger.info(f"Saved to {output_path}")

        return df

    def create_traffic_dataset(
        self,
        output_path: str,
        days: int = 365
    ):
        """
        Create sample traffic dataset for time series prediction

        In production, replace with real traffic data
        """
        logger.info("Creating traffic prediction dataset...")

        # Generate synthetic traffic data with trends and seasonality
        dates = pd.date_range(start='2023-01-01', periods=days, freq='D')

        # Base traffic with trend
        base_traffic = 1000
        trend = np.linspace(0, 500, days)

        # Weekly seasonality (higher on weekdays)
        weekly_pattern = []
        for date in dates:
            if date.weekday() < 5:  # Monday-Friday
                weekly_pattern.append(1.2)
            else:  # Weekend
                weekly_pattern.append(0.8)
        weekly_seasonality = np.array(weekly_pattern) * 200

        # Random noise
        noise = np.random.normal(0, 100, days)

        # Calculate visits
        visits = base_traffic + trend + weekly_seasonality + noise
        visits = np.maximum(visits, 0).astype(int)

        # Create DataFrame
        df = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'visits': visits
        })

        # Save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)

        logger.info(f"Created traffic dataset with {len(df)} days")
        logger.info(f"Visit statistics:\n{df['visits'].describe()}")
        logger.info(f"Saved to {output_path}")

        return df

    def clean_html_content(self, html: str) -> str:
        """Clean HTML content"""
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style
        for script in soup(['script', 'style']):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean whitespace
        text = ' '.join(text.split())

        return text

    def validate_intent_dataset(self, df: pd.DataFrame) -> bool:
        """Validate intent classification dataset"""
        logger.info("Validating intent dataset...")

        # Check required columns
        if not all(col in df.columns for col in ['query', 'intent']):
            logger.error("Missing required columns")
            return False

        # Check for nulls
        if df.isnull().any().any():
            logger.warning(f"Found null values:\n{df.isnull().sum()}")

        # Check intent labels
        unknown_labels = set(df['intent'].unique()) - set(INTENT_LABELS)
        if unknown_labels:
            logger.error(f"Unknown intent labels: {unknown_labels}")
            return False

        # Check class balance
        logger.info(f"Class distribution:\n{df['intent'].value_counts()}")

        logger.info("Dataset validation passed")
        return True

    def validate_content_dataset(self, df: pd.DataFrame) -> bool:
        """Validate content scoring dataset"""
        logger.info("Validating content dataset...")

        # Check required columns
        required = ['content', 'quality_score']
        if not all(col in df.columns for col in required):
            logger.error(f"Missing required columns: {required}")
            return False

        # Check for nulls
        if df[required].isnull().any().any():
            logger.warning("Found null values in required columns")

        # Check score range
        if not df['quality_score'].between(0, 100).all():
            logger.error("Quality scores must be between 0 and 100")
            return False

        logger.info(f"Score statistics:\n{df['quality_score'].describe()}")
        logger.info("Dataset validation passed")

        return True


def main():
    """Main function to prepare all datasets"""
    preparer = DatasetPreparer()

    # Create directories
    os.makedirs('data', exist_ok=True)

    # Prepare intent classification dataset
    logger.info("\n" + "="*50)
    intent_df = preparer.create_intent_dataset(
        output_path='data/intent_training_data.csv',
        samples_per_class=250
    )
    preparer.validate_intent_dataset(intent_df)

    # Prepare content scoring dataset
    logger.info("\n" + "="*50)
    content_df = preparer.create_content_scoring_dataset(
        output_path='data/content_scoring_data.csv',
        n_samples=500
    )
    preparer.validate_content_dataset(content_df)

    # Prepare traffic prediction dataset
    logger.info("\n" + "="*50)
    traffic_df = preparer.create_traffic_dataset(
        output_path='data/traffic_data.csv',
        days=365
    )

    logger.info("\n" + "="*50)
    logger.info("All datasets prepared successfully!")


if __name__ == "__main__":
    main()
