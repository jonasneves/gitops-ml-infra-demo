"""
Integration tests for the FastAPI ML inference endpoints.
Tests all API endpoints including health checks, predictions, and metrics.
"""
import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from app import app, PredictionRequest, BatchPredictionRequest


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint."""

    @pytest.mark.api
    @pytest.mark.integration
    def test_root_returns_200(self, client):
        """Test that root endpoint returns 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    @pytest.mark.api
    @pytest.mark.integration
    def test_root_contains_service_info(self, client):
        """Test that root returns service information."""
        response = client.get("/")
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    @pytest.mark.api
    @pytest.mark.integration
    def test_root_contains_endpoints(self, client):
        """Test that root lists available endpoints."""
        response = client.get("/")
        data = response.json()
        assert "endpoints" in data
        endpoints = data["endpoints"]
        assert "health" in endpoints
        assert "ready" in endpoints
        assert "predict" in endpoints
        assert "metrics" in endpoints


class TestHealthEndpoints:
    """Tests for health and readiness endpoints."""

    @pytest.mark.api
    @pytest.mark.integration
    def test_health_endpoint_returns_200(self, client):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    @pytest.mark.api
    @pytest.mark.integration
    def test_health_status_is_healthy(self, client):
        """Test health endpoint reports healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ml-inference"

    @pytest.mark.api
    @pytest.mark.integration
    def test_ready_endpoint_returns_200(self, client):
        """Test readiness endpoint returns 200."""
        response = client.get("/ready")
        assert response.status_code == 200

    @pytest.mark.api
    @pytest.mark.integration
    def test_ready_status_is_ready(self, client):
        """Test readiness endpoint reports ready status."""
        response = client.get("/ready")
        data = response.json()
        assert data["status"] == "ready"

    @pytest.mark.api
    @pytest.mark.integration
    def test_health_contains_timestamp(self, client):
        """Test health response contains timestamp."""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data
        assert len(data["timestamp"]) > 0

    @pytest.mark.api
    @pytest.mark.integration
    def test_health_contains_version(self, client):
        """Test health response contains version."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "1.0.0"


class TestPredictEndpoint:
    """Tests for the single prediction endpoint."""

    @pytest.mark.api
    @pytest.mark.integration
    def test_predict_positive_sentiment(self, client):
        """Test prediction with positive text."""
        response = client.post("/predict", json={"text": "This is amazing"})
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "positive"

    @pytest.mark.api
    @pytest.mark.integration
    def test_predict_negative_sentiment(self, client):
        """Test prediction with negative text."""
        response = client.post("/predict", json={"text": "This is terrible"})
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "negative"

    @pytest.mark.api
    @pytest.mark.integration
    def test_predict_neutral_sentiment(self, client):
        """Test prediction with neutral text."""
        response = client.post("/predict", json={"text": "The weather is cloudy"})
        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "neutral"

    @pytest.mark.api
    @pytest.mark.integration
    def test_predict_response_structure(self, client):
        """Test prediction response has all required fields."""
        response = client.post("/predict", json={"text": "Test text"})
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "sentiment" in data
        assert "confidence" in data
        assert "processing_time_ms" in data
        assert "timestamp" in data

    @pytest.mark.api
    @pytest.mark.integration
    def test_predict_returns_original_text(self, client):
        """Test that response includes the original text."""
        original_text = "This is a test message"
        response = client.post("/predict", json={"text": original_text})
        data = response.json()
        assert data["text"] == original_text

    @pytest.mark.api
    @pytest.mark.integration
    def test_predict_confidence_in_valid_range(self, client):
        """Test that confidence is between 0 and 1."""
        response = client.post("/predict", json={"text": "amazing"})
        data = response.json()
        assert 0 <= data["confidence"] <= 1

    @pytest.mark.api
    @pytest.mark.integration
    def test_predict_processing_time_positive(self, client):
        """Test that processing time is positive."""
        response = client.post("/predict", json={"text": "test"})
        data = response.json()
        assert data["processing_time_ms"] > 0

    @pytest.mark.api
    @pytest.mark.integration
    def test_predict_empty_text_rejected(self, client):
        """Test that empty text is rejected."""
        response = client.post("/predict", json={"text": ""})
        assert response.status_code == 422

    @pytest.mark.api
    @pytest.mark.integration
    def test_predict_missing_text_rejected(self, client):
        """Test that missing text field is rejected."""
        response = client.post("/predict", json={})
        assert response.status_code == 422


class TestBatchPredictEndpoint:
    """Tests for the batch prediction endpoint."""

    @pytest.mark.api
    @pytest.mark.integration
    def test_batch_predict_multiple_texts(self, client):
        """Test batch prediction with multiple texts."""
        texts = ["amazing", "terrible", "neutral"]
        response = client.post("/predict/batch", json={"texts": texts})
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 3

    @pytest.mark.api
    @pytest.mark.integration
    def test_batch_predict_response_structure(self, client):
        """Test batch response has required fields."""
        response = client.post("/predict/batch", json={"texts": ["test"]})
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "total_processing_time_ms" in data

    @pytest.mark.api
    @pytest.mark.integration
    def test_batch_predict_preserves_order(self, client):
        """Test that batch predictions maintain input order."""
        texts = ["amazing", "terrible", "wonderful"]
        response = client.post("/predict/batch", json={"texts": texts})
        data = response.json()
        for i, pred in enumerate(data["predictions"]):
            assert pred["text"] == texts[i]

    @pytest.mark.api
    @pytest.mark.integration
    def test_batch_predict_single_item(self, client):
        """Test batch prediction with single item."""
        response = client.post("/predict/batch", json={"texts": ["test"]})
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 1

    @pytest.mark.api
    @pytest.mark.integration
    def test_batch_predict_empty_list_rejected(self, client):
        """Test that empty texts list is rejected."""
        response = client.post("/predict/batch", json={"texts": []})
        assert response.status_code == 422

    @pytest.mark.api
    @pytest.mark.integration
    def test_batch_total_time_positive(self, client):
        """Test that total processing time is positive."""
        response = client.post("/predict/batch", json={"texts": ["a", "b"]})
        data = response.json()
        assert data["total_processing_time_ms"] > 0


class TestMetricsEndpoint:
    """Tests for the Prometheus metrics endpoint."""

    @pytest.mark.api
    @pytest.mark.integration
    def test_metrics_endpoint_returns_200(self, client):
        """Test metrics endpoint returns 200."""
        response = client.get("/metrics")
        assert response.status_code == 200

    @pytest.mark.api
    @pytest.mark.integration
    def test_metrics_content_type(self, client):
        """Test metrics endpoint returns correct content type."""
        response = client.get("/metrics")
        assert "text/plain" in response.headers.get("content-type", "")

    @pytest.mark.api
    @pytest.mark.integration
    def test_metrics_contains_inference_metrics(self, client):
        """Test metrics contain inference-related metrics."""
        # Make a prediction first to generate metrics
        client.post("/predict", json={"text": "test"})
        response = client.get("/metrics")
        content = response.text
        assert "inference" in content.lower()


class TestInputValidation:
    """Tests for input validation."""

    @pytest.mark.api
    @pytest.mark.integration
    def test_predict_text_too_long(self, client):
        """Test that text exceeding max length is rejected."""
        long_text = "a" * 600  # Max is 500
        response = client.post("/predict", json={"text": long_text})
        assert response.status_code == 422

    @pytest.mark.api
    @pytest.mark.integration
    def test_batch_too_many_items(self, client):
        """Test that batch with too many items is rejected."""
        texts = ["test"] * 25  # Max is 20
        response = client.post("/predict/batch", json={"texts": texts})
        assert response.status_code == 422

    @pytest.mark.api
    @pytest.mark.integration
    def test_predict_invalid_json(self, client):
        """Test that invalid JSON is rejected."""
        response = client.post(
            "/predict",
            content="not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    @pytest.mark.api
    @pytest.mark.integration
    def test_predict_wrong_method(self, client):
        """Test that GET on predict endpoint is rejected."""
        response = client.get("/predict")
        assert response.status_code == 405


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.api
    @pytest.mark.integration
    def test_not_found_endpoint(self, client):
        """Test 404 for non-existent endpoint."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
