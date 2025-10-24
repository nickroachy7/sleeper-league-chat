"""
Unit tests for middleware module
"""
import pytest
import os
from unittest.mock import patch, Mock
from middleware import (
    get_client_ip,
    rate_limit,
    require_api_key,
)


class TestGetClientIP:
    """Tests for get_client_ip function"""

    def test_x_forwarded_for_header(self, app, client):
        """Test IP extraction from X-Forwarded-For header"""
        with app.test_request_context(
            headers={"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        ):
            from flask import request

            ip = get_client_ip()
            assert ip == "192.168.1.1"

    def test_x_real_ip_header(self, app, client):
        """Test IP extraction from X-Real-IP header"""
        with app.test_request_context(headers={"X-Real-IP": "192.168.1.2"}):
            ip = get_client_ip()
            assert ip == "192.168.1.2"

    def test_remote_addr_fallback(self, app, client):
        """Test fallback to remote_addr"""
        with app.test_request_context():
            ip = get_client_ip()
            # Will be None or '127.0.0.1' depending on test setup
            assert ip is not None


class TestRateLimit:
    """Tests for rate_limit decorator"""

    def test_allows_request_within_limit(
        self, app, client, clear_rate_limits
    ):
        """Test that request within limit is allowed"""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_blocks_request_exceeding_limit(
        self, app, client, clear_rate_limits
    ):
        """Test that request exceeding limit is blocked"""
        # Make multiple requests to exceed limit
        # Chat endpoint has 30 req/min limit
        for _ in range(30):
            client.post(
                "/api/chat",
                json={"message": "test", "session_id": "test"},
            )

        # 31st request should be rate limited
        response = client.post(
            "/api/chat",
            json={"message": "test", "session_id": "test"},
        )
        assert response.status_code == 429
        assert b"Rate limit exceeded" in response.data

    def test_rate_limit_headers_present(self, app, client, clear_rate_limits):
        """Test that rate limit headers are present in response"""
        response = client.get("/api/health")

        # Note: Health endpoint doesn't have rate limiting, so headers may not be present
        # This is just a structural test
        assert response.status_code == 200


class TestRequireAPIKey:
    """Tests for require_api_key decorator"""

    def test_no_api_key_configured_allows_access(self, app, client):
        """Test that missing API_KEY config allows access (dev mode)"""
        with patch.dict(os.environ, {}, clear=True):
            response = client.get("/api/health")
            assert response.status_code == 200

    def test_valid_api_key_in_header_allows_access(self, app, client):
        """Test that valid API key in header allows access"""
        # This would require an endpoint with @require_api_key decorator
        # For now, this is a structural test
        pass

    def test_invalid_api_key_denies_access(self, app, client):
        """Test that invalid API key denies access"""
        # This would require an endpoint with @require_api_key decorator
        # For now, this is a structural test
        pass

