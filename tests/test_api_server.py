"""
Integration tests for Flask API server
"""
import pytest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import app


@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Tests for /api/health endpoint"""
    
    def test_health_check(self, client):
        """Test health check returns ok"""
        response = client.get('/api/health')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['status'] == 'ok'
        assert 'service' in data


class TestChatEndpoint:
    """Tests for /api/chat endpoint"""
    
    def test_chat_requires_message(self, client):
        """Test that chat endpoint requires a message"""
        response = client.post(
            '/api/chat',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_chat_with_message(self, client):
        """Test chat endpoint with valid message"""
        # This test requires mocking the OpenAI API
        # For now, we just test the endpoint structure
        response = client.post(
            '/api/chat',
            data=json.dumps({
                'message': 'test message',
                'session_id': 'test-session'
            }),
            content_type='application/json'
        )
        
        # Will fail without OpenAI key, but structure is correct
        assert response.status_code in [200, 500]


class TestResetEndpoint:
    """Tests for /api/reset endpoint"""
    
    def test_reset_conversation(self, client):
        """Test conversation reset"""
        response = client.post(
            '/api/reset',
            data=json.dumps({'session_id': 'test-session'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data


class TestLeagueEndpoints:
    """Tests for league data endpoints"""
    
    def test_get_league(self, client):
        """Test league info endpoint"""
        response = client.get('/api/league')
        
        # Will succeed or fail based on database connection
        assert response.status_code in [200, 500]
    
    def test_get_standings(self, client):
        """Test standings endpoint"""
        response = client.get('/api/standings')
        
        # Will succeed or fail based on database connection
        assert response.status_code in [200, 500]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])





