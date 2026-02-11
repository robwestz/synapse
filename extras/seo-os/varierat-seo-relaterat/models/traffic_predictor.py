"""
LSTM-based Traffic Forecasting
Predicts future website traffic based on historical data
"""
import numpy as np
import tensorflow as tf
from tensorflow import keras
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.config import get_settings
from app.logger import get_logger

settings = get_settings()
logger = get_logger()


class TrafficPredictor:
    """LSTM-based traffic prediction model"""

    def __init__(self):
        self.model: Optional[keras.Model] = None
        self.scaler_mean: Optional[float] = None
        self.scaler_std: Optional[float] = None
        self.is_loaded = False

    def load_model(self, model_path: Optional[str] = None):
        """Load LSTM model"""
        try:
            logger.info("Loading LSTM traffic predictor...")

            if model_path:
                self.model = keras.models.load_model(model_path)
                logger.info("LSTM model loaded from file")
            else:
                # Create default model architecture
                self.model = self._build_default_model()
                logger.warning("Using default LSTM model (not trained)")

            self.is_loaded = True
            logger.info("Traffic predictor ready")

        except Exception as e:
            logger.error(f"Error loading LSTM model: {e}")
            self.model = None
            self.is_loaded = True

    def _build_default_model(self) -> keras.Model:
        """Build default LSTM model architecture"""
        model = keras.Sequential([
            keras.layers.LSTM(64, activation='relu', input_shape=(settings.LSTM_SEQUENCE_LENGTH, 1), return_sequences=True),
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(32, activation='relu'),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(1)
        ])

        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )

        return model

    def predict_traffic(
        self,
        historical_data: List[Dict],
        forecast_days: int = None
    ) -> Dict:
        """
        Predict future traffic

        Args:
            historical_data: List of dicts with 'date' and 'visits' keys
            forecast_days: Number of days to forecast

        Returns:
            Dict with predictions and metadata
        """
        if not self.is_loaded:
            self.load_model()

        try:
            forecast_days = forecast_days or settings.LSTM_FORECAST_DAYS

            # Prepare data
            dates, visits = self._extract_time_series(historical_data)

            if len(visits) < settings.LSTM_SEQUENCE_LENGTH:
                raise ValueError(f"Need at least {settings.LSTM_SEQUENCE_LENGTH} data points")

            # Normalize
            normalized_visits = self._normalize(visits)

            # Create sequences
            X = self._create_sequences(normalized_visits)

            if self.model and len(X) > 0:
                # Make predictions
                predictions = []
                current_sequence = X[-1].reshape(1, settings.LSTM_SEQUENCE_LENGTH, 1)

                for _ in range(forecast_days):
                    # Predict next value
                    next_pred = self.model.predict(current_sequence, verbose=0)[0][0]
                    predictions.append(next_pred)

                    # Update sequence
                    current_sequence = np.roll(current_sequence, -1, axis=1)
                    current_sequence[0, -1, 0] = next_pred

                # Denormalize predictions
                predictions = self._denormalize(np.array(predictions))
            else:
                # Simple moving average fallback
                predictions = self._simple_forecast(visits, forecast_days)

            # Generate forecast dates
            last_date = dates[-1]
            forecast_dates = [
                last_date + timedelta(days=i+1)
                for i in range(forecast_days)
            ]

            # Calculate statistics
            stats = self._calculate_statistics(visits, predictions)

            result = {
                "forecast": [
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "predicted_visits": int(max(0, pred))
                    }
                    for date, pred in zip(forecast_dates, predictions)
                ],
                "statistics": stats,
                "historical_summary": {
                    "start_date": dates[0].strftime("%Y-%m-%d"),
                    "end_date": dates[-1].strftime("%Y-%m-%d"),
                    "total_days": len(dates),
                    "avg_daily_visits": round(float(np.mean(visits)), 2)
                }
            }

            logger.info(f"Generated {forecast_days}-day traffic forecast")

            return result

        except Exception as e:
            logger.error(f"Error predicting traffic: {e}")
            raise

    def _extract_time_series(self, data: List[Dict]) -> Tuple[List[datetime], np.ndarray]:
        """Extract and sort time series data"""
        # Sort by date
        sorted_data = sorted(data, key=lambda x: x['date'])

        dates = [
            datetime.strptime(d['date'], "%Y-%m-%d") if isinstance(d['date'], str)
            else d['date']
            for d in sorted_data
        ]
        visits = np.array([float(d['visits']) for d in sorted_data])

        return dates, visits

    def _normalize(self, data: np.ndarray) -> np.ndarray:
        """Normalize data using z-score"""
        self.scaler_mean = np.mean(data)
        self.scaler_std = np.std(data)

        if self.scaler_std == 0:
            self.scaler_std = 1.0

        normalized = (data - self.scaler_mean) / self.scaler_std
        return normalized

    def _denormalize(self, data: np.ndarray) -> np.ndarray:
        """Denormalize data"""
        if self.scaler_mean is None or self.scaler_std is None:
            return data

        return data * self.scaler_std + self.scaler_mean

    def _create_sequences(self, data: np.ndarray) -> np.ndarray:
        """Create sequences for LSTM input"""
        sequences = []
        seq_length = settings.LSTM_SEQUENCE_LENGTH

        for i in range(len(data) - seq_length):
            seq = data[i:i + seq_length]
            sequences.append(seq)

        return np.array(sequences).reshape(-1, seq_length, 1)

    def _simple_forecast(self, historical: np.ndarray, days: int) -> np.ndarray:
        """Simple moving average forecast as fallback"""
        window = min(7, len(historical))
        moving_avg = np.mean(historical[-window:])

        # Add slight trend
        if len(historical) > window:
            recent_trend = (historical[-1] - historical[-window]) / window
        else:
            recent_trend = 0

        predictions = []
        for i in range(days):
            pred = moving_avg + (recent_trend * i)
            predictions.append(pred)

        return np.array(predictions)

    def _calculate_statistics(self, historical: np.ndarray, predictions: np.ndarray) -> Dict:
        """Calculate prediction statistics"""
        hist_mean = float(np.mean(historical))
        pred_mean = float(np.mean(predictions))

        # Calculate trend
        if hist_mean > 0:
            trend_pct = ((pred_mean - hist_mean) / hist_mean) * 100
        else:
            trend_pct = 0.0

        # Calculate confidence (simplified)
        hist_std = float(np.std(historical))
        confidence = 1.0 / (1.0 + hist_std / (hist_mean + 1))

        return {
            "predicted_avg_daily": round(pred_mean, 2),
            "historical_avg_daily": round(hist_mean, 2),
            "trend_percentage": round(trend_pct, 2),
            "trend_direction": "up" if trend_pct > 0 else "down" if trend_pct < 0 else "stable",
            "confidence_score": round(confidence, 3),
            "total_predicted_visits": int(np.sum(predictions))
        }

    def analyze_seasonality(self, historical_data: List[Dict]) -> Dict:
        """Analyze traffic seasonality patterns"""
        try:
            dates, visits = self._extract_time_series(historical_data)

            # Day of week analysis
            dow_visits = {i: [] for i in range(7)}
            for date, visit in zip(dates, visits):
                dow = date.weekday()
                dow_visits[dow].append(visit)

            dow_averages = {
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dow]: round(float(np.mean(visits)), 2)
                for dow, visits in dow_visits.items() if visits
            }

            # Find peak day
            peak_day = max(dow_averages.items(), key=lambda x: x[1])

            return {
                "day_of_week_averages": dow_averages,
                "peak_day": peak_day[0],
                "peak_day_avg_visits": peak_day[1]
            }

        except Exception as e:
            logger.error(f"Error analyzing seasonality: {e}")
            return {}
