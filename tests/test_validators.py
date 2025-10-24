"""
Unit tests for validators module
"""
import pytest
from validators import (
    validate_string,
    validate_session_id,
    validate_chat_request,
    ValidationError,
)


class TestValidateString:
    """Tests for validate_string function"""

    def test_valid_string(self):
        """Test validation of valid string"""
        result = validate_string("test message", "field")
        assert result == "test message"

    def test_strips_whitespace(self):
        """Test that whitespace is stripped"""
        result = validate_string("  test  ", "field")
        assert result == "test"

    def test_empty_string_raises_error(self):
        """Test that empty string raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_string("", "field")
        assert "cannot be empty" in str(exc_info.value.message)

    def test_whitespace_only_raises_error(self):
        """Test that whitespace-only string raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_string("   ", "field")
        assert "cannot be empty" in str(exc_info.value.message)

    def test_non_string_raises_error(self):
        """Test that non-string raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_string(123, "field")
        assert "must be a string" in str(exc_info.value.message)

    def test_too_short_raises_error(self):
        """Test that string below min_length raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_string("ab", "field", min_length=3)
        assert "at least 3 characters" in str(exc_info.value.message)

    def test_too_long_raises_error(self):
        """Test that string above max_length raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_string("abcdef", "field", max_length=5)
        assert "at most 5 characters" in str(exc_info.value.message)


class TestValidateSessionId:
    """Tests for validate_session_id function"""

    def test_valid_session_id(self):
        """Test validation of valid session ID"""
        result = validate_session_id("test-session-123")
        assert result == "test-session-123"

    def test_empty_returns_default(self):
        """Test that empty session ID returns 'default'"""
        result = validate_session_id("")
        assert result == "default"

    def test_none_returns_default(self):
        """Test that None returns 'default'"""
        result = validate_session_id(None)
        assert result == "default"


class TestValidateChatRequest:
    """Tests for validate_chat_request function"""

    def test_valid_request(self):
        """Test validation of valid chat request"""
        data = {"message": "Hello!", "session_id": "test-123"}
        result = validate_chat_request(data)
        assert result["message"] == "Hello!"
        assert result["session_id"] == "test-123"

    def test_missing_session_id_uses_default(self):
        """Test that missing session_id defaults to 'default'"""
        data = {"message": "Hello!"}
        result = validate_chat_request(data)
        assert result["session_id"] == "default"

    def test_empty_data_raises_error(self):
        """Test that empty data raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_chat_request(None)
        assert "Request body is required" in str(exc_info.value.message)

    def test_missing_message_raises_error(self):
        """Test that missing message raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_chat_request({})
        assert "Message is required" in str(exc_info.value.message)

    def test_empty_message_raises_error(self):
        """Test that empty message raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_chat_request({"message": ""})
        assert "cannot be empty" in str(exc_info.value.message)

    def test_message_too_long_raises_error(self):
        """Test that message exceeding max length raises error"""
        long_message = "a" * 5001
        with pytest.raises(ValidationError) as exc_info:
            validate_chat_request({"message": long_message})
        assert "at most 5000 characters" in str(exc_info.value.message)

