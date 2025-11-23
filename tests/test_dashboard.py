"""
Integration tests for the Flask dashboard server.
Tests dashboard endpoints, badge APIs, and helper functions.
"""
import pytest
import json

# Import dashboard components
from dashboard_server import (
    app,
    is_pod_ready,
    get_deployment_stats,
    calculate_progress,
    deployment_state,
)


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_state():
    """Reset deployment state before each test."""
    deployment_state["argocd_apps"] = []
    deployment_state["pods"] = []
    deployment_state["progress"] = 0
    deployment_state["phase"] = "Initializing"
    yield


class TestIsPodReady:
    """Tests for the is_pod_ready helper function."""

    @pytest.mark.unit
    @pytest.mark.dashboard
    def test_pod_ready_all_containers(self):
        """Test pod with all containers ready."""
        pod = {"name": "test", "namespace": "test", "status": "Running", "ready": "2/2"}
        assert is_pod_ready(pod) is True

    @pytest.mark.unit
    @pytest.mark.dashboard
    def test_pod_not_ready_partial(self):
        """Test pod with some containers not ready."""
        pod = {"name": "test", "namespace": "test", "status": "Running", "ready": "1/2"}
        assert is_pod_ready(pod) is False

    @pytest.mark.unit
    @pytest.mark.dashboard
    def test_pod_not_ready_zero(self):
        """Test pod with no containers ready."""
        pod = {"name": "test", "namespace": "test", "status": "Pending", "ready": "0/1"}
        assert is_pod_ready(pod) is False

    @pytest.mark.unit
    @pytest.mark.dashboard
    def test_pod_ready_zero_zero(self):
        """Test pod with 0/0 ready (init containers)."""
        pod = {"name": "test", "namespace": "test", "status": "Init", "ready": "0/0"}
        assert is_pod_ready(pod) is False

    @pytest.mark.unit
    @pytest.mark.dashboard
    def test_pod_ready_single_container(self):
        """Test pod with single ready container."""
        pod = {"name": "test", "namespace": "test", "status": "Running", "ready": "1/1"}
        assert is_pod_ready(pod) is True


class TestGetDeploymentStats:
    """Tests for the get_deployment_stats function."""

    @pytest.mark.unit
    @pytest.mark.dashboard
    def test_stats_empty_inputs(self):
        """Test stats with empty inputs."""
        stats = get_deployment_stats([], [])
        assert stats["total_apps"] == 0
        assert stats["total_pods"] == 0

    @pytest.mark.unit
    @pytest.mark.dashboard
    def test_stats_all_healthy(self, mock_argocd_apps, mock_pods):
        """Test stats with all healthy apps and pods."""
        stats = get_deployment_stats(mock_argocd_apps, mock_pods)
        assert stats["total_apps"] == 2
        assert stats["synced_apps"] == 2
        assert stats["healthy_apps"] == 2
        assert stats["total_pods"] == 3
        assert stats["running_pods"] == 3
        assert stats["ready_pods"] == 3

    @pytest.mark.unit
    @pytest.mark.dashboard
    def test_stats_mixed_health(self):
        """Test stats with mixed health states."""
        apps = [
            {"name": "app1", "sync": "Synced", "health": "Healthy"},
            {"name": "app2", "sync": "OutOfSync", "health": "Degraded"},
        ]
        pods = [
            {"namespace": "ns", "name": "pod1", "status": "Running", "ready": "1/1"},
            {"namespace": "ns", "name": "pod2", "status": "Pending", "ready": "0/1"},
        ]
        stats = get_deployment_stats(apps, pods)
        assert stats["synced_apps"] == 1
        assert stats["healthy_apps"] == 1
        assert stats["running_pods"] == 1
        assert stats["ready_pods"] == 1


class TestCalculateProgress:
    """Tests for the calculate_progress function."""

    @pytest.mark.unit
    @pytest.mark.dashboard
    def test_progress_no_apps(self):
        """Test progress with no apps returns 10."""
        deployment_state["argocd_apps"] = []
        deployment_state["pods"] = []
        progress = calculate_progress()
        assert progress == 10

    @pytest.mark.unit
    @pytest.mark.dashboard
    def test_progress_all_complete(self, mock_argocd_apps, mock_pods):
        """Test progress with all apps synced and healthy."""
        deployment_state["argocd_apps"] = mock_argocd_apps
        deployment_state["pods"] = mock_pods
        progress = calculate_progress()
        assert progress == 100

    @pytest.mark.unit
    @pytest.mark.dashboard
    def test_progress_partial(self):
        """Test progress with partial completion."""
        deployment_state["argocd_apps"] = [
            {"name": "app1", "sync": "Synced", "health": "Healthy"},
            {"name": "app2", "sync": "OutOfSync", "health": "Progressing"},
        ]
        deployment_state["pods"] = []
        progress = calculate_progress()
        assert 0 < progress < 100

    @pytest.mark.unit
    @pytest.mark.dashboard
    def test_progress_max_100(self, mock_argocd_apps, mock_pods):
        """Test that progress never exceeds 100."""
        deployment_state["argocd_apps"] = mock_argocd_apps
        deployment_state["pods"] = mock_pods
        progress = calculate_progress()
        assert progress <= 100


class TestDashboardEndpoints:
    """Tests for dashboard HTTP endpoints."""

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_index_returns_200(self, client):
        """Test index endpoint returns 200."""
        response = client.get("/")
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_index_returns_html(self, client):
        """Test index endpoint returns HTML."""
        response = client.get("/")
        assert "text/html" in response.content_type

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_index_contains_title(self, client):
        """Test index page contains expected title."""
        response = client.get("/")
        assert b"GitOps Infrastructure Dashboard" in response.data

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_status_endpoint_returns_200(self, client):
        """Test status endpoint returns 200."""
        response = client.get("/api/status")
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_status_endpoint_returns_json(self, client):
        """Test status endpoint returns JSON."""
        response = client.get("/api/status")
        assert response.content_type == "application/json"

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_status_endpoint_structure(self, client):
        """Test status endpoint response structure."""
        response = client.get("/api/status")
        data = json.loads(response.data)
        assert "argocd_apps" in data
        assert "pods" in data
        assert "progress" in data
        assert "phase" in data
        assert "elapsed" in data

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_debug_endpoint_returns_200(self, client):
        """Test debug endpoint returns 200."""
        response = client.get("/api/debug")
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_debug_endpoint_structure(self, client):
        """Test debug endpoint response structure."""
        response = client.get("/api/debug")
        data = json.loads(response.data)
        assert "argocd_apps" in data
        assert "pods" in data
        assert "summary" in data


class TestBadgeEndpoints:
    """Tests for badge API endpoints."""

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_badge_argocd_returns_200(self, client):
        """Test ArgoCD badge endpoint returns 200."""
        response = client.get("/api/badge/argocd")
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_badge_argocd_structure(self, client):
        """Test ArgoCD badge response structure."""
        response = client.get("/api/badge/argocd")
        data = json.loads(response.data)
        assert data["schemaVersion"] == 1
        assert data["label"] == "ArgoCD"
        assert "message" in data
        assert "color" in data

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_badge_pods_returns_200(self, client):
        """Test Pods badge endpoint returns 200."""
        response = client.get("/api/badge/pods")
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_badge_pods_structure(self, client):
        """Test Pods badge response structure."""
        response = client.get("/api/badge/pods")
        data = json.loads(response.data)
        assert data["schemaVersion"] == 1
        assert data["label"] == "Pods"
        assert "message" in data
        assert "color" in data

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_badge_health_returns_200(self, client):
        """Test Health badge endpoint returns 200."""
        response = client.get("/api/badge/health")
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_badge_health_structure(self, client):
        """Test Health badge response structure."""
        response = client.get("/api/badge/health")
        data = json.loads(response.data)
        assert data["schemaVersion"] == 1
        assert data["label"] == "Health"
        assert "message" in data
        assert "color" in data

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_badge_deployment_returns_200(self, client):
        """Test Deployment badge endpoint returns 200."""
        response = client.get("/api/badge/deployment")
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_badge_deployment_structure(self, client):
        """Test Deployment badge response structure."""
        response = client.get("/api/badge/deployment")
        data = json.loads(response.data)
        assert data["schemaVersion"] == 1
        assert data["label"] == "Deployment"
        assert "message" in data
        assert "color" in data


class TestBadgeColors:
    """Tests for badge color logic."""

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_badge_argocd_no_apps_inactive(self, client):
        """Test ArgoCD badge shows inactive with no apps."""
        deployment_state["argocd_apps"] = []
        response = client.get("/api/badge/argocd")
        data = json.loads(response.data)
        assert data["color"] == "inactive"

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_badge_argocd_all_synced_success(self, client, mock_argocd_apps):
        """Test ArgoCD badge shows success when all synced."""
        deployment_state["argocd_apps"] = mock_argocd_apps
        response = client.get("/api/badge/argocd")
        data = json.loads(response.data)
        assert data["color"] == "success"

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_badge_deployment_complete_success(self, client, mock_argocd_apps, mock_pods):
        """Test Deployment badge shows success at 100%."""
        deployment_state["argocd_apps"] = mock_argocd_apps
        deployment_state["pods"] = mock_pods
        deployment_state["progress"] = 100
        response = client.get("/api/badge/deployment")
        data = json.loads(response.data)
        assert data["color"] == "success"
        assert data["message"] == "Complete"

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_badge_deployment_in_progress_colors(self, client):
        """Test Deployment badge color at different progress levels."""
        # Test blue color (0-30%)
        deployment_state["progress"] = 25
        response = client.get("/api/badge/deployment")
        data = json.loads(response.data)
        assert data["color"] == "blue"

        # Test orange color (30-70%)
        deployment_state["progress"] = 50
        response = client.get("/api/badge/deployment")
        data = json.loads(response.data)
        assert data["color"] == "orange"

        # Test yellow color (70-100%)
        deployment_state["progress"] = 80
        response = client.get("/api/badge/deployment")
        data = json.loads(response.data)
        assert data["color"] == "yellow"


class TestStreamEndpoint:
    """Tests for the SSE stream endpoint."""

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_stream_endpoint_returns_200(self, client):
        """Test stream endpoint returns 200."""
        # Note: We just test that the endpoint exists and returns the right type
        response = client.get("/api/stream")
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.dashboard
    def test_stream_content_type(self, client):
        """Test stream endpoint returns event-stream content type."""
        response = client.get("/api/stream")
        assert "text/event-stream" in response.content_type
