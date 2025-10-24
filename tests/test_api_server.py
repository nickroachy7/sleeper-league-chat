"""
Integration tests for Flask API server
"""
import pytest
import json
from unittest.mock import patch, Mock


class TestHealthEndpoint:
    """Tests for /api/health endpoint"""

    def test_health_check(self, client):
        """Test health check returns ok"""
        response = client.get("/api/health")
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data["status"] == "ok"
        assert "service" in data
        assert "version" in data
        assert "active_sessions" in data

    def test_health_check_response_structure(self, client):
        """Test health check response has correct structure"""
        response = client.get("/api/health")
        data = json.loads(response.data)

        required_fields = [
            "status",
            "service",
            "version",
            "port",
            "environment",
            "active_sessions",
        ]
        for field in required_fields:
            assert field in data


class TestChatEndpoint:
    """Tests for /api/chat endpoint"""

    def test_chat_requires_message(self, client):
        """Test that chat endpoint requires a message"""
        response = client.post(
            "/api/chat", data=json.dumps({}), content_type="application/json"
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_chat_empty_message_rejected(self, client):
        """Test that empty message is rejected"""
        response = client.post(
            "/api/chat",
            data=json.dumps({"message": "", "session_id": "test"}),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_chat_whitespace_only_message_rejected(self, client):
        """Test that whitespace-only message is rejected"""
        response = client.post(
            "/api/chat",
            data=json.dumps({"message": "   ", "session_id": "test"}),
            content_type="application/json",
        )

        assert response.status_code == 400

    @patch("api_server.chat")
    def test_chat_with_valid_message(
        self, mock_chat, client, clear_rate_limits
    ):
        """Test chat endpoint with valid message"""
        # Mock the chat function to avoid calling OpenAI
        mock_chat.return_value = (
            "This is a test response",
            [{"role": "user", "content": "test"}],
        )

        response = client.post(
            "/api/chat",
            data=json.dumps({"message": "test message", "session_id": "test-session"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "response" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session"

    def test_chat_message_too_long_rejected(self, client):
        """Test that message exceeding max length is rejected"""
        long_message = "a" * 5001
        response = client.post(
            "/api/chat",
            data=json.dumps({"message": long_message, "session_id": "test"}),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_chat_invalid_json_rejected(self, client):
        """Test that invalid JSON is rejected"""
        response = client.post(
            "/api/chat",
            data="not valid json",
            content_type="application/json",
        )

        assert response.status_code == 400


class TestResetEndpoint:
    """Tests for /api/reset endpoint"""

    def test_reset_conversation(self, client):
        """Test conversation reset"""
        response = client.post(
            "/api/reset",
            data=json.dumps({"session_id": "test-session"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "message" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session"

    def test_reset_without_session_id(self, client):
        """Test reset without session ID uses default"""
        response = client.post(
            "/api/reset",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["session_id"] == "default"

    def test_reset_response_includes_cleared_count(self, client):
        """Test that reset response includes messages_cleared count"""
        response = client.post(
            "/api/reset",
            data=json.dumps({"session_id": "test"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "messages_cleared" in data


class TestLeagueEndpoints:
    """Tests for league data endpoints"""

    @patch("league_queries.get_league_info")
    def test_get_league_success(self, mock_get_league, client, sample_league_data):
        """Test successful league info retrieval"""
        mock_get_league.return_value = sample_league_data

        response = client.get("/api/league")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "league_id" in data

    @patch("league_queries.get_league_info")
    def test_get_league_error_handling(self, mock_get_league, client):
        """Test league endpoint error handling"""
        mock_get_league.side_effect = Exception("Database error")

        response = client.get("/api/league")

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data

    @patch("league_queries.get_standings")
    def test_get_standings_success(
        self, mock_get_standings, client, sample_standings_data
    ):
        """Test successful standings retrieval"""
        mock_get_standings.return_value = sample_standings_data

        response = client.get("/api/standings")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    @patch("league_queries.get_standings")
    def test_get_standings_error_handling(self, mock_get_standings, client):
        """Test standings endpoint error handling"""
        mock_get_standings.side_effect = Exception("Database error")

        response = client.get("/api/standings")

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data


class TestErrorHandling:
    """Tests for error handling"""

    def test_404_not_found(self, client):
        """Test 404 error handling"""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data

    def test_405_method_not_allowed(self, client):
        """Test 405 error for wrong HTTP method"""
        response = client.get("/api/chat")  # POST endpoint

        assert response.status_code == 405
        data = json.loads(response.data)
        assert "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])





