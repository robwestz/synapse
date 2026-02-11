# ML Service - Team Theta: AI & Machine Learning

AI/ML Service for the SEO Intelligence Platform providing advanced machine learning capabilities for SEO analysis and optimization.

## Overview

This service provides real AI-powered features including:
- **Search Intent Classification** - BERT-based classification (Commercial, Informational, Navigational, Transactional)
- **Content Quality Scoring** - LightGBM-based scoring (0-100 scale)
- **Keyword Clustering** - Word2Vec + K-means semantic grouping
- **Traffic Prediction** - LSTM-based time-series forecasting
- **Topic Extraction** - spaCy NLP for topics and entities
- **SEO Recommendations** - Hybrid rules + ML recommendations

## Features

### 1. Intent Classification
- BERT-based transformer model
- 4 intent types: Commercial, Informational, Navigational, Transactional
- >90% accuracy target
- Batch processing support

### 2. Content Quality Scoring
- Multi-factor analysis (readability, keyword density, depth, structure)
- 0-100 scoring scale with letter grades
- Detailed factor breakdowns
- Actionable improvement recommendations

### 3. Keyword Clustering
- Word2Vec embeddings
- K-means clustering with auto-optimization
- Semantic similarity detection
- Cluster theme extraction

### 4. Traffic Prediction
- LSTM neural network
- Time-series forecasting (7-30 days)
- Seasonality analysis
- Trend detection

### 5. Topic & Entity Extraction
- spaCy NLP pipeline
- Named entity recognition
- Key phrase extraction
- Relationship extraction
- Sentiment analysis

### 6. Recommendation Engine
- Keyword optimization suggestions
- Content improvement recommendations
- Technical SEO recommendations
- UX enhancements
- Link building strategies

## Technology Stack

- **Framework**: FastAPI
- **Deep Learning**: TensorFlow, PyTorch, Transformers
- **ML Libraries**: scikit-learn, LightGBM, XGBoost
- **NLP**: spaCy, NLTK, Gensim
- **Time Series**: Prophet, statsmodels
- **Data Processing**: Pandas, NumPy, BeautifulSoup

## Project Structure

```
ml-service/
├── app/
│   ├── models/              # ML model implementations
│   │   ├── intent_classifier.py
│   │   ├── content_scorer.py
│   │   ├── keyword_clusterer.py
│   │   ├── traffic_predictor.py
│   │   ├── topic_extractor.py
│   │   └── recommendation_engine.py
│   ├── routers/             # API routes
│   │   ├── classification.py
│   │   ├── scoring.py
│   │   ├── clustering.py
│   │   ├── prediction.py
│   │   └── recommendations.py
│   ├── utils/               # Utilities
│   │   ├── feature_extraction.py
│   │   ├── preprocessing.py
│   │   └── model_loader.py
│   ├── training/            # Training scripts
│   │   ├── train_intent_model.py
│   │   ├── train_content_scorer.py
│   │   └── prepare_datasets.py
│   ├── main.py             # FastAPI application
│   ├── config.py           # Configuration
│   └── logger.py           # Logging setup
├── models/                 # Trained model files
├── Dockerfile
├── requirements.txt
└── README.md
```

## Installation

### Local Development

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Download NLP models**:
```bash
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

3. **Run the service**:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

### Docker Deployment

1. **Build image**:
```bash
docker build -t seo-ml-service .
```

2. **Run container**:
```bash
docker run -d -p 8003:8003 --name ml-service seo-ml-service
```

## API Endpoints

### Health & Monitoring
- `GET /` - Service information
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /models/status` - Model loading status

### Intent Classification
- `POST /api/v1/classify-intent` - Classify single query
- `POST /api/v1/classify-intent/batch` - Batch classification
- `GET /api/v1/intents` - Get intent types

### Content Scoring
- `POST /api/v1/score-content` - Score content quality
- `GET /api/v1/scoring/factors` - Get scoring factors

### Keyword Clustering
- `POST /api/v1/cluster-keywords` - Cluster keywords
- `POST /api/v1/keywords/similar` - Find similar keywords

### Traffic Prediction
- `POST /api/v1/predict-traffic` - Predict future traffic
- `POST /api/v1/traffic/seasonality` - Analyze seasonality

### Recommendations
- `POST /api/v1/generate-recommendations` - Generate SEO recommendations
- `POST /api/v1/extract-topics` - Extract topics and entities
- `POST /api/v1/analyze-sentiment` - Analyze sentiment
- `POST /api/v1/extract-relationships` - Extract relationships
- `POST /api/v1/extract-questions` - Extract questions
- `POST /api/v1/summarize` - Generate content summary

## API Examples

### Classify Intent
```bash
curl -X POST "http://localhost:8003/api/v1/classify-intent" \
  -H "Content-Type: application/json" \
  -d '{"query": "best laptops for programming", "explain": true}'
```

### Score Content
```bash
curl -X POST "http://localhost:8003/api/v1/score-content" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "<h1>Title</h1><p>Content here...</p>",
    "title": "My Article",
    "keywords": ["seo", "optimization"]
  }'
```

### Cluster Keywords
```bash
curl -X POST "http://localhost:8003/api/v1/cluster-keywords" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["seo", "optimization", "ranking", "keywords", "backlinks"]
  }'
```

### Predict Traffic
```bash
curl -X POST "http://localhost:8003/api/v1/predict-traffic" \
  -H "Content-Type: application/json" \
  -d '{
    "historical_data": [
      {"date": "2024-01-01", "visits": 1000},
      {"date": "2024-01-02", "visits": 1100}
    ],
    "forecast_days": 7
  }'
```

## Training Models

### Prepare Datasets
```bash
python -m app.training.prepare_datasets
```

### Train Intent Classifier
```bash
python -m app.training.train_intent_model
```

### Train Content Scorer
```bash
python -m app.training.train_content_scorer
```

## Configuration

Configuration can be set via environment variables or `.env` file:

```env
# Application
APP_NAME=SEO Intelligence ML Service
DEBUG=false

# Server
HOST=0.0.0.0
PORT=8003
WORKERS=2

# Models
MODEL_PATH=/app/models
CACHE_MODELS=true

# BERT
BERT_MODEL=bert-base-uncased
BERT_MAX_LENGTH=512

# spaCy
SPACY_MODEL=en_core_web_sm

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/ml-service.log
```

## Performance

- **Intent Classification**: ~50-100ms per query
- **Content Scoring**: ~200-500ms per document
- **Keyword Clustering**: ~1-3s for 100 keywords
- **Traffic Prediction**: ~500ms-2s per forecast
- **Topic Extraction**: ~100-300ms per document

## Model Accuracy

- **Intent Classifier**: >90% accuracy (with fine-tuning)
- **Content Scorer**: R² > 0.85 (with training data)
- **Keyword Clusterer**: Silhouette score > 0.5
- **Traffic Predictor**: MAE < 10% of mean traffic

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
flake8 app/
```

### API Documentation
Access interactive API docs at:
- Swagger UI: `http://localhost:8003/docs`
- ReDoc: `http://localhost:8003/redoc`

## Integration

This service integrates with:
- **Backend Service** (Port 8000) - Main orchestration
- **Analysis Service** (Port 8002) - Content analysis
- **PostgreSQL** - Data storage
- **Redis** (optional) - Caching

## Monitoring

- Prometheus metrics at `/metrics`
- Health checks at `/health`
- Structured logging with loguru
- Request timing middleware

## Future Enhancements

- [ ] GPU acceleration for faster inference
- [ ] Model versioning and A/B testing
- [ ] Real-time model retraining pipeline
- [ ] Multi-language support
- [ ] Advanced ensemble methods
- [ ] Explainable AI features
- [ ] Model compression for edge deployment

## Team Theta

**Mission**: Provide cutting-edge AI/ML capabilities for SEO intelligence

**Technologies**: BERT, LightGBM, LSTM, spaCy, Word2Vec, K-means

**Focus Areas**: NLP, Time-Series Prediction, Content Analysis, Recommendation Systems

---

**Service Port**: 8003
**API Version**: v1
**Framework**: FastAPI
**Python Version**: 3.11+
