"""
Shared fixtures and configuration for the test suite.
"""
import pytest
import sys
from pathlib import Path

# Add application directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app" / "ml-inference"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


@pytest.fixture
def sample_positive_text():
    """Sample text with positive sentiment."""
    return "This is amazing and wonderful"


@pytest.fixture
def sample_negative_text():
    """Sample text with negative sentiment."""
    return "This is terrible and awful"


@pytest.fixture
def sample_neutral_text():
    """Sample text with neutral sentiment."""
    return "The weather is cloudy today"


@pytest.fixture
def mock_argocd_apps():
    """Mock ArgoCD application list."""
    return [
        {"name": "ml-inference", "sync": "Synced", "health": "Healthy"},
        {"name": "monitoring", "sync": "Synced", "health": "Healthy"},
    ]


@pytest.fixture
def mock_pods():
    """Mock Kubernetes pod list."""
    return [
        {"namespace": "ml-inference", "name": "ml-api-abc123", "status": "Running", "ready": "1/1"},
        {"namespace": "monitoring", "name": "prometheus-xyz789", "status": "Running", "ready": "1/1"},
        {"namespace": "argocd", "name": "argocd-server-def456", "status": "Running", "ready": "1/1"},
    ]


@pytest.fixture
def mock_pending_pods():
    """Mock Kubernetes pods with some pending."""
    return [
        {"namespace": "ml-inference", "name": "ml-api-abc123", "status": "Running", "ready": "1/1"},
        {"namespace": "monitoring", "name": "prometheus-xyz789", "status": "Pending", "ready": "0/1"},
    ]
