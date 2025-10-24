"""
Middleware for Flask application
Includes rate limiting and authentication
"""
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import os
from logger_config import setup_logger

logger = setup_logger("middleware")

# Simple in-memory rate limiter
# In production, use Redis for distributed rate limiting
rate_limit_storage: Dict[str, list] = defaultdict(list)


def get_client_ip() -> str:
    """
    Get client IP address from request

    Returns:
        Client IP address
    """
    # Check for X-Forwarded-For header (proxy/load balancer)
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()

    # Check for X-Real-IP header
    if request.headers.get("X-Real-IP"):
        return request.headers.get("X-Real-IP")

    # Fall back to remote_addr
    return request.remote_addr or "unknown"


def rate_limit(
    max_requests: int = 60, window_seconds: int = 60, key_prefix: str = "default"
):
    """
    Rate limiting decorator

    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
        key_prefix: Prefix for rate limit key

    Usage:
        @rate_limit(max_requests=10, window_seconds=60)
        def my_endpoint():
            ...
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Get client identifier
            client_ip = get_client_ip()
            rate_key = f"{key_prefix}:{client_ip}"

            # Get current timestamp
            now = datetime.now()

            # Clean old requests outside the window
            cutoff_time = now - timedelta(seconds=window_seconds)
            rate_limit_storage[rate_key] = [
                req_time
                for req_time in rate_limit_storage[rate_key]
                if req_time > cutoff_time
            ]

            # Check if rate limit exceeded
            request_count = len(rate_limit_storage[rate_key])

            if request_count >= max_requests:
                # Calculate retry-after time
                oldest_request = rate_limit_storage[rate_key][0]
                retry_after = int(
                    (oldest_request + timedelta(seconds=window_seconds) - now).total_seconds()
                )

                logger.warning(
                    f"Rate limit exceeded for {client_ip} on {key_prefix} "
                    f"({request_count}/{max_requests} requests)"
                )

                return (
                    jsonify(
                        {
                            "error": "Rate limit exceeded",
                            "message": f"Too many requests. Limit: {max_requests} per {window_seconds}s",
                            "retry_after": max(retry_after, 1),
                        }
                    ),
                    429,
                    {"Retry-After": str(max(retry_after, 1))},
                )

            # Add current request to storage
            rate_limit_storage[rate_key].append(now)

            # Add rate limit headers to response
            response = f(*args, **kwargs)

            # If response is a tuple (response, status_code), extract it
            if isinstance(response, tuple):
                response_obj, status_code = response[0], response[1]
            else:
                response_obj, status_code = response, 200

            # Add rate limit headers if response is a Flask response object
            if hasattr(response_obj, "headers"):
                response_obj.headers["X-RateLimit-Limit"] = str(max_requests)
                response_obj.headers["X-RateLimit-Remaining"] = str(
                    max(0, max_requests - len(rate_limit_storage[rate_key]))
                )
                response_obj.headers["X-RateLimit-Reset"] = str(
                    int((now + timedelta(seconds=window_seconds)).timestamp())
                )

            return (response_obj, status_code) if isinstance(response, tuple) else response_obj

        return wrapper

    return decorator


def require_api_key(f):
    """
    Decorator to require API key for endpoint

    Checks for API key in:
    1. X-API-Key header
    2. Authorization: Bearer <key> header
    3. api_key query parameter

    Set API_KEY environment variable to enable authentication.
    If not set, authentication is disabled (development mode).

    Usage:
        @require_api_key
        def protected_endpoint():
            ...
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        # Check if API key is configured
        configured_api_key = os.getenv("API_KEY")

        # If no API key configured, skip authentication (development mode)
        if not configured_api_key:
            logger.debug("API key authentication disabled (no API_KEY configured)")
            return f(*args, **kwargs)

        # Get API key from request
        api_key = None

        # Check X-API-Key header
        if request.headers.get("X-API-Key"):
            api_key = request.headers.get("X-API-Key")

        # Check Authorization header
        elif request.headers.get("Authorization"):
            auth_header = request.headers.get("Authorization")
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]

        # Check query parameter
        elif request.args.get("api_key"):
            api_key = request.args.get("api_key")

        # Validate API key
        if not api_key:
            logger.warning(
                f"Missing API key from {get_client_ip()} for {request.endpoint}"
            )
            return (
                jsonify(
                    {
                        "error": "Authentication required",
                        "message": "API key required. Provide via X-API-Key header, "
                        "Authorization: Bearer header, or api_key query param",
                    }
                ),
                401,
            )

        if api_key != configured_api_key:
            logger.warning(
                f"Invalid API key from {get_client_ip()} for {request.endpoint}"
            )
            return jsonify({"error": "Invalid API key"}), 401

        # API key valid, proceed
        logger.debug(f"API key validated for {request.endpoint}")
        return f(*args, **kwargs)

    return wrapper


def request_logger(f):
    """
    Decorator to log request details

    Usage:
        @request_logger
        def my_endpoint():
            ...
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()

        # Log request
        logger.info(
            f"Request: {request.method} {request.path}",
            extra={
                "method": request.method,
                "path": request.path,
                "client_ip": get_client_ip(),
                "user_agent": request.headers.get("User-Agent"),
            },
        )

        # Execute endpoint
        response = f(*args, **kwargs)

        # Log response time
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        status_code = response[1] if isinstance(response, tuple) else 200

        logger.info(
            f"Response: {status_code} ({duration_ms:.2f}ms)",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )

        return response

    return wrapper

