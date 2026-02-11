"""
BERT-based Search Intent Classifier
Classifies search queries into: Commercial, Informational, Navigational, Transactional
"""
import torch
import numpy as np
from transformers import BertTokenizer, BertForSequenceClassification
from typing import Dict, List, Optional
from app.config import get_settings, INTENT_LABELS
from app.logger import get_logger

settings = get_settings()
logger = get_logger()


class IntentClassifier:
    """BERT-based intent classification model"""

    def __init__(self):
        self.tokenizer: Optional[BertTokenizer] = None
        self.model: Optional[BertForSequenceClassification] = None
        self.labels = INTENT_LABELS
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.is_loaded = False

    def load_model(self, model_path: Optional[str] = None):
        """Load BERT model and tokenizer"""
        try:
            logger.info("Loading BERT intent classifier...")

            if model_path:
                # Load fine-tuned model
                self.tokenizer = BertTokenizer.from_pretrained(model_path)
                self.model = BertForSequenceClassification.from_pretrained(
                    model_path,
                    num_labels=len(self.labels)
                )
            else:
                # Load pre-trained BERT for demo (should be fine-tuned in production)
                self.tokenizer = BertTokenizer.from_pretrained(settings.BERT_MODEL)
                self.model = BertForSequenceClassification.from_pretrained(
                    settings.BERT_MODEL,
                    num_labels=len(self.labels)
                )

            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True

            logger.info(f"BERT intent classifier loaded on {self.device}")

        except Exception as e:
            logger.error(f"Error loading BERT model: {e}")
            raise

    def classify(self, query: str) -> Dict:
        """
        Classify search intent

        Args:
            query: Search query or keyword

        Returns:
            Dict with intent, confidence, and all probabilities
        """
        if not self.is_loaded:
            self.load_model()

        try:
            # Tokenize input
            inputs = self.tokenizer(
                query,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=settings.BERT_MAX_LENGTH
            )

            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)

            # Get prediction
            probs = probabilities.cpu().numpy()[0]
            predicted_idx = np.argmax(probs)
            predicted_label = self.labels[predicted_idx]
            confidence = float(probs[predicted_idx])

            # Build result
            result = {
                "query": query,
                "intent": predicted_label,
                "confidence": confidence,
                "probabilities": {
                    label: float(prob)
                    for label, prob in zip(self.labels, probs)
                }
            }

            logger.debug(f"Intent classification: {query} -> {predicted_label} ({confidence:.2f})")

            return result

        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            raise

    def classify_batch(self, queries: List[str]) -> List[Dict]:
        """
        Classify multiple queries

        Args:
            queries: List of search queries

        Returns:
            List of classification results
        """
        if not self.is_loaded:
            self.load_model()

        try:
            results = []

            # Process in batches
            batch_size = settings.BERT_BATCH_SIZE
            for i in range(0, len(queries), batch_size):
                batch = queries[i:i + batch_size]

                # Tokenize batch
                inputs = self.tokenizer(
                    batch,
                    return_tensors="pt",
                    truncation=True,
                    padding=True,
                    max_length=settings.BERT_MAX_LENGTH
                )

                # Move to device
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # Get predictions
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    logits = outputs.logits
                    probabilities = torch.softmax(logits, dim=-1)

                # Process results
                probs = probabilities.cpu().numpy()
                for j, query in enumerate(batch):
                    prob = probs[j]
                    predicted_idx = np.argmax(prob)
                    predicted_label = self.labels[predicted_idx]
                    confidence = float(prob[predicted_idx])

                    results.append({
                        "query": query,
                        "intent": predicted_label,
                        "confidence": confidence,
                        "probabilities": {
                            label: float(p)
                            for label, p in zip(self.labels, prob)
                        }
                    })

            logger.info(f"Classified {len(queries)} queries")

            return results

        except Exception as e:
            logger.error(f"Error in batch classification: {e}")
            raise

    def get_intent_explanation(self, intent: str) -> str:
        """Get explanation for intent type"""
        explanations = {
            "Commercial": "User is researching products/services-integrations-of-usp-features before purchase",
            "Informational": "User seeks knowledge or answers to questions",
            "Navigational": "User wants to find a specific website or page",
            "Transactional": "User intends to complete an action or purchase"
        }
        return explanations.get(intent, "Unknown intent")
