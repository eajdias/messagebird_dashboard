"""
Pytest Fixtures
"""

import asyncio

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db():
    """Mock database session for unit tests."""
    # TODO: Implement mock database
    yield None


@pytest.fixture
def sample_conversation():
    """Sample conversation data for tests."""
    return {
        "id": 1,
        "contact": "João Silva",
        "phone": "+5511999887766",
        "created_at": "2026-06-01T10:00:00",
        "updated_at": "2026-06-01T10:30:00",
        "status": "archived",
        "channel": "WhatsApp",
        "department": "Suporte",
        "agent": "Ana Santos",
        "rating": 5,
        "nps": 9,
    }


@pytest.fixture
def sample_metrics():
    """Sample metrics data for tests."""
    return {
        "total_conversations": 100,
        "nps_score": 75,
        "frt_avg_minutes": 5.2,
        "art_avg_minutes": 120.5,
        "rating_avg": 4.3,
    }
