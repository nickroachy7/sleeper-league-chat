"""
Input validation utilities for API endpoints
Ensures data integrity and security
"""
from typing import Any, Dict, Optional
from functools import wraps
from flask import request, jsonify


class ValidationError(Exception):
    """Custom exception for validation errors"""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def validate_string(
    value: Any, field_name: str, min_length: int = 1, max_length: int = 10000
) -> str:
    """
    Validate string input

    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_length: Minimum allowed length
        max_length: Maximum allowed length

    Returns:
        Validated string

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name)

    if not value or not value.strip():
        raise ValidationError(f"{field_name} cannot be empty", field_name)

    if len(value) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters", field_name
        )

    if len(value) > max_length:
        raise ValidationError(
            f"{field_name} must be at most {max_length} characters", field_name
        )

    return value.strip()


def validate_session_id(session_id: Any) -> str:
    """
    Validate session ID

    Args:
        session_id: Session ID to validate

    Returns:
        Validated session ID

    Raises:
        ValidationError: If validation fails
    """
    if not session_id:
        return "default"

    return validate_string(session_id, "session_id", min_length=1, max_length=100)


def validate_chat_request(data: Dict[str, Any]) -> Dict[str, str]:
    """
    Validate chat endpoint request data

    Args:
        data: Request data dictionary

    Returns:
        Validated data dictionary

    Raises:
        ValidationError: If validation fails
    """
    if not data:
        raise ValidationError("Request body is required")

    message = data.get("message")
    if not message:
        raise ValidationError("Message is required", "message")

    validated_message = validate_string(
        message, "message", min_length=1, max_length=5000
    )

    session_id = validate_session_id(data.get("session_id"))

    return {"message": validated_message, "session_id": session_id}


def validate_request(validator_func):
    """
    Decorator to validate request data using a validator function

    Args:
        validator_func: Function that takes request data and returns validated data

    Usage:
        @validate_request(validate_chat_request)
        def chat_endpoint():
            validated_data = request.validated_data
            ...
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json(silent=True)
                validated_data = validator_func(data)
                request.validated_data = validated_data
                return f(*args, **kwargs)
            except ValidationError as e:
                return (
                    jsonify({"error": e.message, "field": e.field}),
                    400,
                )
            except Exception as e:
                return jsonify({"error": "Invalid request data"}), 400

        return wrapper

    return decorator

