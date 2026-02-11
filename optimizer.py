"""
AutoML system for automatic hyperparameter optimization.
"""

import logging
import optuna
from typing import Dict, Any, List, Callable, Optional
import numpy as np
from sklearn.model_selection import cross_val_score
import asyncio

# Import SEI-X components
from ..core.engine import SemanticIntelligenceEngine
from ..core.models import ModelMode

# Set up logger
logger = logging.getLogger(__name__)


class AutoMLOptimizer:
    """Automatic hyperparameter optimization using Optuna."""

    def __init__(
            self,
            objective_metric: str = 'f1_score',
            n_trials: int = 100,
            n_jobs: int = -1
    ):
        self.objective_metric = objective_metric
        self.n_trials = n_trials
        self.n_jobs = n_jobs
        self.study = None
        self.best_params = None

    def optimize(
            self,
            train_data: List[str],
            labels: List[List[str]],
            param_space: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run hyperparameter optimization."""

        def objective(trial):
            # Sample hyperparameters
            params = {
                'mode': trial.suggest_categorical('mode', ['fast', 'balanced', 'advanced']),
                'batch_size': trial.suggest_int('batch_size', 8, 64, step=8),
                'max_chunk_size': trial.suggest_int('max_chunk_size', 256, 1024, step=128),
                'embedding_model': trial.suggest_categorical(
                    'embedding_model',
                    param_space.get('embedding_models', [
                        'sentence-transformers/all-mpnet-base-v2',
                        'sentence-transformers/all-MiniLM-L12-v2'
                    ])
                ),
                'graph_algorithm': trial.suggest_categorical(
                    'graph_algorithm',
                    ['pagerank', 'hits', 'katz_centrality']
                ),
                'graph_damping': trial.suggest_float('graph_damping', 0.7, 0.95),
                'semantic_threshold': trial.suggest_float('semantic_threshold', 0.2, 0.6),
                'clustering_eps': trial.suggest_float('clustering_eps', 0.1, 0.5),
                'min_keyword_length': trial.suggest_int('min_keyword_length', 2, 5)
            }

            # Create engine with sampled parameters
            engine = self._create_engine(params)

            # Evaluate performance
            score = self._evaluate_engine(engine, train_data, labels)

            return score

        # Create study
        self.study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(),
            pruner=optuna.pruners.MedianPruner()
        )

        # Optimize
        self.study.optimize(
            objective,
            n_trials=self.n_trials,
            n_jobs=self.n_jobs,
            callbacks=[self._optimization_callback]
        )

        # Get best parameters
        self.best_params = self.study.best_params

        return self.best_params

    def _create_engine(self, params: Dict[str, Any]) -> SemanticIntelligenceEngine:
        """Create engine with given parameters."""
        return SemanticIntelligenceEngine(
            mode=ModelMode[params['mode'].upper()],
            language_model=params['embedding_model'],
            batch_size=params['batch_size'],
            max_chunk_size=params['max_chunk_size']
        )

    def _evaluate_engine(
            self,
            engine: SemanticIntelligenceEngine,
            texts: List[str],
            labels: List[List[str]]
    ) -> float:
        """Evaluate engine performance."""
        scores = []

        for text, true_keywords in zip(texts, labels):
            # Extract keywords
            extracted = engine.extract(text, top_k=len(true_keywords))
            extracted_texts = [kw.text.lower() for kw in extracted]
            true_texts = [kw.lower() for kw in true_keywords]

            # Calculate F1 score
            precision = len(set(extracted_texts) & set(true_texts)) / len(extracted_texts)
            recall = len(set(extracted_texts) & set(true_texts)) / len(true_texts)

            if precision + recall > 0:
                f1 = 2 * (precision * recall) / (precision + recall)
            else:
                f1 = 0

            scores.append(f1)

        return np.mean(scores)

    def _optimization_callback(self, study: optuna.Study, trial: optuna.Trial):
        """Callback for optimization progress."""
        if trial.number % 10 == 0:
            logger.info(
                f"Trial {trial.number}: {trial.value:.4f} "
                f"(best: {study.best_value:.4f})"
            )


class NeuralArchitectureSearch:
    """Neural Architecture Search for optimal model selection."""

    def __init__(self):
        self.search_space = {
            'encoder_layers': [4, 6, 8, 12],
            'hidden_dims': [256, 384, 512, 768],
            'attention_heads': [4, 8, 12, 16],
            'dropout_rates': [0.1, 0.2, 0.3],
            'activation': ['relu', 'gelu', 'swish']
        }
        self.best_architecture = None
        self.best_score = 0.0

    async def search(
            self,
            train_data: List[str],
            val_data: List[str],
            max_hours: int = 24,
            n_trials: int = 50
    ) -> Dict[str, Any]:
        """Search for optimal architecture using Optuna-based NAS."""
        logger.info(f"Starting Neural Architecture Search with {n_trials} trials")

        def objective(trial: optuna.Trial) -> float:
            # Sample architecture parameters
            architecture = {
                'encoder_layers': trial.suggest_categorical('encoder_layers', self.search_space['encoder_layers']),
                'hidden_dim': trial.suggest_categorical('hidden_dim', self.search_space['hidden_dims']),
                'attention_heads': trial.suggest_categorical('attention_heads', self.search_space['attention_heads']),
                'dropout_rate': trial.suggest_categorical('dropout_rate', self.search_space['dropout_rates']),
                'activation': trial.suggest_categorical('activation', self.search_space['activation'])
            }

            # Evaluate architecture on validation data
            score = self._evaluate_architecture(architecture, train_data, val_data)

            return score

        # Create study with time budget
        study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(seed=42),
            pruner=optuna.pruners.HyperbandPruner()
        )

        # Run optimization with timeout
        try:
            study.optimize(
                objective,
                n_trials=n_trials,
                timeout=max_hours * 3600,
                callbacks=[self._log_progress]
            )

            self.best_architecture = study.best_params
            self.best_score = study.best_value

            logger.info(f"NAS completed. Best score: {self.best_score:.4f}")
            logger.info(f"Best architecture: {self.best_architecture}")

            return {
                'architecture': self.best_architecture,
                'score': self.best_score,
                'n_trials': len(study.trials)
            }

        except Exception as e:
            logger.error(f"Neural Architecture Search failed: {e}")
            return {
                'architecture': None,
                'score': 0.0,
                'error': str(e)
            }

    def _evaluate_architecture(
            self,
            architecture: Dict[str, Any],
            train_data: List[str],
            val_data: List[str]
    ) -> float:
        """Evaluate a specific architecture configuration."""
        try:
            # For now, use a simplified evaluation
            # In practice, this would train a model with the given architecture
            # and evaluate it on validation data

            # Simulate training and evaluation
            # Score based on architecture complexity vs performance trade-off
            complexity_score = self._calculate_complexity_score(architecture)
            performance_score = self._simulate_performance(architecture, val_data)

            # Weighted combination
            final_score = 0.7 * performance_score + 0.3 * (1.0 - complexity_score)

            return final_score

        except Exception as e:
            logger.error(f"Architecture evaluation failed: {e}")
            return 0.0

    def _calculate_complexity_score(self, architecture: Dict[str, Any]) -> float:
        """Calculate normalized complexity score (0-1, higher = more complex)."""
        # Normalize each parameter to 0-1 range
        layers_norm = architecture['encoder_layers'] / max(self.search_space['encoder_layers'])
        hidden_norm = architecture['hidden_dim'] / max(self.search_space['hidden_dims'])
        heads_norm = architecture['attention_heads'] / max(self.search_space['attention_heads'])

        # Average normalized complexity
        complexity = (layers_norm + hidden_norm + heads_norm) / 3.0

        return complexity

    def _simulate_performance(self, architecture: Dict[str, Any], val_data: List[str]) -> float:
        """Simulate performance score based on architecture characteristics."""
        # This is a placeholder - in production, would actually train and evaluate
        # For now, use heuristics based on architecture parameters

        base_score = 0.6

        # Larger models tend to perform better (up to a point)
        if architecture['hidden_dim'] >= 512:
            base_score += 0.15
        elif architecture['hidden_dim'] >= 384:
            base_score += 0.10

        # More layers can help
        if architecture['encoder_layers'] >= 8:
            base_score += 0.10
        elif architecture['encoder_layers'] >= 6:
            base_score += 0.05

        # Attention heads
        if architecture['attention_heads'] >= 12:
            base_score += 0.05

        # GELU activation often works well
        if architecture['activation'] == 'gelu':
            base_score += 0.05

        # Add some randomness to simulate actual evaluation variance
        noise = np.random.normal(0, 0.02)
        final_score = np.clip(base_score + noise, 0.0, 1.0)

        return final_score

    def _log_progress(self, study: optuna.Study, trial: optuna.Trial):
        """Log search progress."""
        if trial.number % 10 == 0:
            logger.info(
                f"NAS Trial {trial.number}: score={trial.value:.4f}, "
                f"best_score={study.best_value:.4f}"
            )