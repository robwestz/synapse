"""
Training Script for Intent Classification Model
Fine-tune BERT for search intent classification
"""
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertForSequenceClassification, AdamW
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import numpy as np
import pandas as pd
from typing import List, Dict
import os

from app.config import get_settings, INTENT_LABELS
from app.logger import get_logger

settings = get_settings()
logger = get_logger()


class IntentDataset(Dataset):
    """Dataset for intent classification"""

    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]

        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'label': torch.tensor(label, dtype=torch.long)
        }


class IntentModelTrainer:
    """Trainer for intent classification model"""

    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = None
        self.model = None

    def prepare_data(self, data_path: str) -> tuple:
        """
        Load and prepare training data

        Expected CSV format: query, intent
        """
        logger.info(f"Loading data from {data_path}")

        # Load data
        df = pd.read_csv(data_path)

        # Validate columns
        if 'query' not in df.columns or 'intent' not in df.columns:
            raise ValueError("CSV must have 'query' and 'intent' columns")

        # Map intent labels to indices
        label_to_idx = {label: idx for idx, label in enumerate(INTENT_LABELS)}

        # Convert labels
        df['label'] = df['intent'].map(label_to_idx)

        # Check for unknown labels
        if df['label'].isna().any():
            unknown = df[df['label'].isna()]['intent'].unique()
            raise ValueError(f"Unknown intent labels: {unknown}")

        # Split data
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            df['query'].tolist(),
            df['label'].tolist(),
            test_size=0.2,
            random_state=42,
            stratify=df['label']
        )

        logger.info(f"Training samples: {len(train_texts)}, Validation samples: {len(val_texts)}")

        return train_texts, val_texts, train_labels, val_labels

    def train(
        self,
        train_texts: List[str],
        train_labels: List[int],
        val_texts: List[str],
        val_labels: List[int],
        epochs: int = 3,
        batch_size: int = 16,
        learning_rate: float = 2e-5,
        output_dir: str = None
    ):
        """
        Train the intent classification model

        Args:
            train_texts: Training queries
            train_labels: Training labels
            val_texts: Validation queries
            val_labels: Validation labels
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
            output_dir: Directory to save model
        """
        logger.info("Initializing model and tokenizer...")

        # Initialize tokenizer and model
        self.tokenizer = BertTokenizer.from_pretrained(settings.BERT_MODEL)
        self.model = BertForSequenceClassification.from_pretrained(
            settings.BERT_MODEL,
            num_labels=len(INTENT_LABELS)
        )
        self.model.to(self.device)

        # Create datasets
        train_dataset = IntentDataset(
            train_texts, train_labels, self.tokenizer, settings.BERT_MAX_LENGTH
        )
        val_dataset = IntentDataset(
            val_texts, val_labels, self.tokenizer, settings.BERT_MAX_LENGTH
        )

        # Create data loaders
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)

        # Optimizer
        optimizer = AdamW(self.model.parameters(), lr=learning_rate)

        # Training loop
        logger.info(f"Starting training for {epochs} epochs...")

        for epoch in range(epochs):
            # Training
            self.model.train()
            train_loss = 0

            for batch in train_loader:
                optimizer.zero_grad()

                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['label'].to(self.device)

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )

                loss = outputs.loss
                train_loss += loss.item()

                loss.backward()
                optimizer.step()

            avg_train_loss = train_loss / len(train_loader)

            # Validation
            val_accuracy, val_loss = self.evaluate(val_loader)

            logger.info(
                f"Epoch {epoch + 1}/{epochs} - "
                f"Train Loss: {avg_train_loss:.4f}, "
                f"Val Loss: {val_loss:.4f}, "
                f"Val Accuracy: {val_accuracy:.4f}"
            )

        # Final evaluation
        logger.info("Training complete. Final evaluation:")
        self._detailed_evaluation(val_loader, val_labels)

        # Save model
        if output_dir:
            self.save_model(output_dir)

    def evaluate(self, data_loader) -> tuple:
        """Evaluate model on data loader"""
        self.model.eval()
        predictions = []
        true_labels = []
        total_loss = 0

        with torch.no_grad():
            for batch in data_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['label'].to(self.device)

                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )

                total_loss += outputs.loss.item()

                logits = outputs.logits
                preds = torch.argmax(logits, dim=-1)

                predictions.extend(preds.cpu().numpy())
                true_labels.extend(labels.cpu().numpy())

        accuracy = accuracy_score(true_labels, predictions)
        avg_loss = total_loss / len(data_loader)

        return accuracy, avg_loss

    def _detailed_evaluation(self, data_loader, true_labels):
        """Print detailed evaluation metrics"""
        self.model.eval()
        predictions = []

        with torch.no_grad():
            for batch in data_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)

                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits
                preds = torch.argmax(logits, dim=-1)

                predictions.extend(preds.cpu().numpy())

        # Classification report
        report = classification_report(
            true_labels,
            predictions,
            target_names=INTENT_LABELS,
            digits=4
        )

        logger.info(f"\nClassification Report:\n{report}")

    def save_model(self, output_dir: str):
        """Save trained model"""
        logger.info(f"Saving model to {output_dir}")

        os.makedirs(output_dir, exist_ok=True)

        # Save model and tokenizer
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)

        logger.info("Model saved successfully")


def main():
    """Main training function"""
    # Configuration
    DATA_PATH = "data/intent_training_data.csv"
    OUTPUT_DIR = os.path.join(settings.MODEL_PATH, "intent_classifier")
    EPOCHS = 3
    BATCH_SIZE = 16
    LEARNING_RATE = 2e-5

    # Initialize trainer
    trainer = IntentModelTrainer()

    # Prepare data
    train_texts, val_texts, train_labels, val_labels = trainer.prepare_data(DATA_PATH)

    # Train model
    trainer.train(
        train_texts=train_texts,
        train_labels=train_labels,
        val_texts=val_texts,
        val_labels=val_labels,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        output_dir=OUTPUT_DIR
    )

    logger.info("Training pipeline complete!")


if __name__ == "__main__":
    main()
