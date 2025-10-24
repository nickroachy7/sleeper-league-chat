"""
Centralized error handling for Flask application
Provides consistent error responses and logging
"""
import traceback
from typing import Tuple
from flask import jsonify, Flask
from logger_config import setup_logger

logger = setup_logger("error_handlers")


class APIError(Exception):
    """Base class for API errors"""

    def __init__(
        self, message: str, status_code: int = 500, payload: dict = None
    ):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}

    def to_dict(self):
        rv = dict(self.payload)
        rv["error"] = self.message
        rv["status_code"] = self.status_code
        return rv


class BadRequestError(APIError):
    """400 Bad Request"""

    def __init__(self, message: str = "Bad request", payload: dict = None):
        super().__init__(message, 400, payload)


class UnauthorizedError(APIError):
    """401 Unauthorized"""

    def __init__(self, message: str = "Unauthorized", payload: dict = None):
        super().__init__(message, 401, payload)


class ForbiddenError(APIError):
    """403 Forbidden"""

    def __init__(self, message: str = "Forbidden", payload: dict = None):
        super().__init__(message, 403, payload)


class NotFoundError(APIError):
    """404 Not Found"""

    def __init__(self, message: str = "Resource not found", payload: dict = None):
        super().__init__(message, 404, payload)


class RateLimitError(APIError):
    """429 Too Many Requests"""

    def __init__(
        self, message: str = "Rate limit exceeded", payload: dict = None
    ):
        super().__init__(message, 429, payload)


class InternalServerError(APIError):
    """500 Internal Server Error"""

    def __init__(
        self, message: str = "Internal server error", payload: dict = None
    ):
        super().__init__(message, 500, payload)


def register_error_handlers(app: Flask):
    """
    Register error handlers with Flask app

    Args:
        app: Flask application instance
    """

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError) -> Tuple[dict, int]:
        """Handle custom API errors"""
        logger.error(
            f"API Error: {error.message}",
            extra={"status_code": error.status_code, "payload": error.payload},
        )
        response = jsonify(error.to_dict())
        return response, error.status_code

    @app.errorhandler(400)
    def handle_bad_request(error) -> Tuple[dict, int]:
        """Handle 400 Bad Request"""
        logger.warning(f"Bad request: {error}")
        return jsonify({"error": "Bad request", "message": str(error)}), 400

    @app.errorhandler(404)
    def handle_not_found(error) -> Tuple[dict, int]:
        """Handle 404 Not Found"""
        logger.warning(f"Not found: {error}")
        return jsonify({"error": "Not found", "message": str(error)}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error) -> Tuple[dict, int]:
        """Handle 405 Method Not Allowed"""
        logger.warning(f"Method not allowed: {error}")
        return (
            jsonify({"error": "Method not allowed", "message": str(error)}),
            405,
        )

    @app.errorhandler(500)
    def handle_internal_error(error) -> Tuple[dict, int]:
        """Handle 500 Internal Server Error"""
        logger.error(
            f"Internal server error: {error}",
            exc_info=True,
            extra={"traceback": traceback.format_exc()},
        )
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                }
            ),
            500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception) -> Tuple[dict, int]:
        """Handle any unexpected exceptions"""
        logger.error(
            f"Unexpected error: {error}",
            exc_info=True,
            extra={"traceback": traceback.format_exc()},
        )
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                }
            ),
            500,
        )

