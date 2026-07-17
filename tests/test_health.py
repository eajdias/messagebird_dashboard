"""
Health check test
"""

from fastapi.testclient import TestClient

from api.main import app


def test_health_check():
    """Test health endpoint returns healthy."""
    client = TestClient(app)
    response = client.get("/api/v1/admin/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
