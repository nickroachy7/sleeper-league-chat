"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
import os
from unittest.mock import Mock, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """Create Flask app for testing"""
    from api_server import app as flask_app

    flask_app.config["TESTING"] = True
    yield flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "This is a test response"
    mock_response.choices[0].message.tool_calls = None
    return mock_response


@pytest.fixture
def mock_supabase_response():
    """Mock Supabase query response"""
    mock_response = Mock()
    mock_response.data = [
        {
            "roster_id": 1,
            "wins": 6,
            "losses": 1,
            "fpts": 88964,
            "fpts_decimal": 0,
        }
    ]
    return mock_response


@pytest.fixture
def sample_chat_request():
    """Sample chat request data"""
    return {"message": "What are the standings?", "session_id": "test-session"}


@pytest.fixture
def sample_league_data():
    """Sample league data"""
    return {
        "league_id": "1180365427496943616",
        "name": "Dynasty Reloaded",
        "season": "2025",
        "status": "in_season",
    }


@pytest.fixture
def sample_standings_data():
    """Sample standings data"""
    return [
        {
            "rank": 1,
            "team_name": "The Jaxon 5",
            "wins": 6,
            "losses": 1,
            "points_for": 889.64,
        },
        {
            "rank": 2,
            "team_name": "Horse Cock Churchill",
            "wins": 5,
            "losses": 2,
            "points_for": 886.57,
        },
    ]


@pytest.fixture
def clear_rate_limits():
    """Clear rate limit storage between tests"""
    from middleware import rate_limit_storage

    rate_limit_storage.clear()
    yield
    rate_limit_storage.clear()

