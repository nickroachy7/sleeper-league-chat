"""
Security utilities and configurations
"""
import re
from typing import List
import os
from logger_config import setup_logger

logger = setup_logger("security")


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks

    Args:
        text: User input text

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove null bytes
    text = text.replace("\x00", "")

    # Remove potential script tags (basic XSS prevention)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove potential HTML tags (for text-only fields)
    # Keep markdown formatting safe
    dangerous_tags = [
        "script",
        "iframe",
        "object",
        "embed",
        "form",
        "input",
        "button",
    ]
    for tag in dangerous_tags:
        text = re.sub(
            f"<{tag}[^>]*>.*?</{tag}>", "", text, flags=re.DOTALL | re.IGNORECASE
        )
        text = re.sub(f"<{tag}[^>]*>", "", text, flags=re.IGNORECASE)

    return text


def get_allowed_origins() -> List[str]:
    """
    Get list of allowed CORS origins from environment

    Returns:
        List of allowed origin URLs
    """
    # Default allowed origins for development
    default_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    # Get custom origins from environment
    custom_origins = os.getenv("ALLOWED_ORIGINS", "")
    if custom_origins:
        custom_list = [origin.strip() for origin in custom_origins.split(",")]
        logger.info(f"✅ Using custom CORS origins: {custom_list}")
        return custom_list

    logger.warning(f"⚠️  Using default CORS origins (localhost only): {default_origins}")
    logger.warning("⚠️  Set ALLOWED_ORIGINS environment variable for production!")
    return default_origins


def validate_environment_variables() -> dict:
    """
    Validate that required environment variables are set and valid

    Returns:
        Dict with validation results and warnings
    """
    warnings = []
    errors = []

    # Check required variables
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "OPENAI_API_KEY",
        "SLEEPER_LEAGUE_ID",
    ]

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            errors.append(f"Missing required environment variable: {var}")
        elif var.endswith("_KEY") and len(value) < 20:
            warnings.append(f"{var} seems too short (possible invalid key)")

    # Check security settings
    if os.getenv("FLASK_ENV") == "production":
        if not os.getenv("API_KEY"):
            warnings.append(
                "API_KEY not set in production mode. Consider enabling authentication."
            )

        if not os.getenv("ALLOWED_ORIGINS"):
            warnings.append(
                "ALLOWED_ORIGINS not set. Using default localhost origins (not suitable for production)"
            )

    # Check URL formats
    supabase_url = os.getenv("SUPABASE_URL", "")
    if supabase_url and not supabase_url.startswith("https://"):
        warnings.append("SUPABASE_URL should use HTTPS in production")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def check_security_headers(response):
    """
    Add security headers to Flask response

    Args:
        response: Flask response object

    Returns:
        Response with security headers added
    """
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    # Prevent MIME sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # XSS Protection
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Content Security Policy (CSP)
    # Adjust as needed based on your frontend requirements
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https:; "
        "font-src 'self' data:; "
    )
    response.headers["Content-Security-Policy"] = csp

    # Strict Transport Security (only in production with HTTPS)
    if os.getenv("FLASK_ENV") == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    return response

