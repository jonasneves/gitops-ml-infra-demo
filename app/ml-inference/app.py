"""
Lightweight ML Inference Service for GitOps Demo
A simple sentiment analysis API using rule-based classification
"""

import time
import logging
from typing import List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'inference_requests_total',
    'Total number of inference requests',
    ['endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'inference_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint']
)
INFERENCE_DURATION = Histogram(
    'model_inference_duration_seconds',
    'Model inference duration in seconds'
)
ACTIVE_REQUESTS = Gauge(
    'inference_active_requests',
    'Number of active inference requests'
)

# Create FastAPI app
app = FastAPI(
    title="ML Inference Service - GitOps Demo",
    description="Lightweight sentiment analysis API for demonstrating GitOps with ArgoCD",
    version="1.0.0"
)

# Simple sentiment analysis (rule-based for demo purposes)
POSITIVE_WORDS = {
    'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
    'love', 'best', 'perfect', 'awesome', 'incredible', 'outstanding',
    'brilliant', 'superb', 'magnificent', 'impressive', 'lovely'
}

NEGATIVE_WORDS = {
    'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst',
    'hate', 'disappointing', 'disappointed', 'sad', 'angry', 'frustrating',
    'useless', 'pathetic', 'disgusting', 'miserable', 'dreadful'
}


class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, description="Text to analyze")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "This GitOps demo is amazing!"
            }
        }


class PredictionResponse(BaseModel):
    text: str
    sentiment: str
    confidence: float
    processing_time_ms: float
    timestamp: str


class BatchPredictionRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, max_items=20)


class BatchPredictionResponse(BaseModel):
    predictions: List[PredictionResponse]
    total_processing_time_ms: float


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


def analyze_sentiment(text: str) -> tuple:
    """
    Simple rule-based sentiment analysis
    Returns: (sentiment, confidence)
    """
    text_lower = text.lower()
    words = set(text_lower.split())

    positive_count = len(words & POSITIVE_WORDS)
    negative_count = len(words & NEGATIVE_WORDS)

    if positive_count > negative_count:
        sentiment = "positive"
        confidence = min(0.95, 0.6 + (positive_count * 0.1))
    elif negative_count > positive_count:
        sentiment = "negative"
        confidence = min(0.95, 0.6 + (negative_count * 0.1))
    else:
        sentiment = "neutral"
        confidence = 0.5 + (len(words) * 0.01)

    confidence = min(confidence, 0.95)
    return sentiment, round(confidence, 2)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "service": "ML Inference Service - GitOps Demo",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "predict": "/predict",
            "batch": "/predict/batch",
            "metrics": "/metrics"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Kubernetes liveness probe"""
    return HealthResponse(
        status="healthy",
        service="ml-inference",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness check endpoint for Kubernetes readiness probe"""
    return HealthResponse(
        status="ready",
        service="ml-inference",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Predict sentiment for a single text
    """
    ACTIVE_REQUESTS.inc()
    start_time = time.time()

    try:
        # Simulate processing time
        with INFERENCE_DURATION.time():
            sentiment, confidence = analyze_sentiment(request.text)
            time.sleep(0.01)  # Simulate model inference time

        processing_time = (time.time() - start_time) * 1000

        REQUEST_COUNT.labels(endpoint='predict', status='success').inc()
        REQUEST_DURATION.labels(endpoint='predict').observe(time.time() - start_time)

        return PredictionResponse(
            text=request.text,
            sentiment=sentiment,
            confidence=confidence,
            processing_time_ms=round(processing_time, 2),
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        REQUEST_COUNT.labels(endpoint='predict', status='error').inc()
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    finally:
        ACTIVE_REQUESTS.dec()


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest):
    """
    Predict sentiment for multiple texts in a batch
    """
    ACTIVE_REQUESTS.inc()
    start_time = time.time()
    predictions = []

    try:
        for text in request.texts:
            pred_start = time.time()
            sentiment, confidence = analyze_sentiment(text)
            pred_time = (time.time() - pred_start) * 1000

            predictions.append(PredictionResponse(
                text=text,
                sentiment=sentiment,
                confidence=confidence,
                processing_time_ms=round(pred_time, 2),
                timestamp=datetime.utcnow().isoformat()
            ))

        total_time = (time.time() - start_time) * 1000

        REQUEST_COUNT.labels(endpoint='batch', status='success').inc()
        REQUEST_DURATION.labels(endpoint='batch').observe(time.time() - start_time)

        return BatchPredictionResponse(
            predictions=predictions,
            total_processing_time_ms=round(total_time, 2)
        )

    except Exception as e:
        REQUEST_COUNT.labels(endpoint='batch', status='error').inc()
        logger.error(f"Batch prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

    finally:
        ACTIVE_REQUESTS.dec()


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting ML Inference Service...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
