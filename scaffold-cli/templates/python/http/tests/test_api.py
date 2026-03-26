"""
Integration tests for Python web service template
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_index_endpoint(client):
    """Test index endpoint returns HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_api_hello_endpoint(client):
    """Test hello API endpoint."""
    response = client.get("/api/hello")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello from Python!"
    assert "service" in data
    assert "version" in data


def test_api_echo_endpoint(client):
    """Test echo API endpoint."""
    response = client.post("/api/echo", content="test content")
    assert response.status_code == 200
    assert response.text == "test content"


def test_not_found(client):
    """Test 404 for unknown routes."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
