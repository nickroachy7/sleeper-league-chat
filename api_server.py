"""
Flask API Server for Fantasy League Assistant
Provides REST API endpoints for the web UI
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from fantasy_assistant import chat
from logger_config import setup_logger
from config import API_PORT, FLASK_ENV, LOG_FILE
from validators import validate_request, validate_chat_request, ValidationError
from error_handlers import register_error_handlers, InternalServerError
from middleware import rate_limit, require_api_key, request_logger
from openapi_spec import OPENAPI_SPEC
import json
import os

# Setup logging
logger = setup_logger("api_server")

app = Flask(__name__)

# Configure CORS for security
CORS(
    app,
    resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:3001"]}},
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Register error handlers
register_error_handlers(app)

# Store conversation history per session
# In production, use Redis or a proper session store
conversations = {}


@app.route("/api/health", methods=["GET"])
def health():
    """
    Basic health check endpoint (fast, no external dependencies)

    Returns:
        JSON with service status and metadata
    """
    logger.debug("Health check requested")
    return jsonify(
        {
            "status": "ok",
            "service": "Fantasy League Assistant API",
            "version": "1.0.0",
            "port": API_PORT,
            "environment": FLASK_ENV,
            "active_sessions": len(conversations),
        }
    )


@app.route("/api/health/detailed", methods=["GET"])
@rate_limit(max_requests=10, window_seconds=60, key_prefix="health_detailed")
def health_detailed():
    """
    Detailed health check with external dependencies

    Query params:
        - include_external: Check database and external APIs (default: false)

    Returns:
        JSON with comprehensive health status
    """
    from health_checks import run_all_health_checks

    include_external = request.args.get("include_external", "false").lower() == "true"

    logger.debug(
        f"Detailed health check requested (include_external={include_external})"
    )

    health_status = run_all_health_checks(include_external=include_external)

    status_code = 200
    if health_status["status"] == "unhealthy":
        status_code = 503
    elif health_status["status"] == "degraded":
        status_code = 200  # Still operational

    return jsonify(health_status), status_code


@app.route("/api/chat", methods=["POST"])
@rate_limit(max_requests=30, window_seconds=60, key_prefix="chat")
@request_logger
@validate_request(validate_chat_request)
def chat_endpoint():
    """
    Chat endpoint for sending messages to the assistant

    Request body:
    {
        "message": "What are the current standings?",
        "session_id": "unique-session-id" (optional)
    }

    Response:
    {
        "response": "Here are the current standings...",
        "session_id": "unique-session-id",
        "message_count": 5
    }
    """
    try:
        # Get validated data from validator decorator
        validated_data = request.validated_data
        message = validated_data["message"]
        session_id = validated_data["session_id"]

        logger.info(f"Processing message from session {session_id}: {message[:50]}...")

        # Get or create conversation history for this session
        conversation_history = conversations.get(session_id)

        # Get response from assistant
        response, updated_history = chat(message, conversation_history)

        # Store updated conversation history
        conversations[session_id] = updated_history

        # Count messages (excluding system messages)
        message_count = sum(
            1 for msg in updated_history if msg.get("role") in ["user", "assistant"]
        )

        logger.info(
            f"Successfully processed message for session {session_id} "
            f"(total messages: {message_count})"
        )

        return jsonify(
            {
                "response": response,
                "session_id": session_id,
                "message_count": message_count,
            }
        )

    except Exception as e:
        logger.error(
            f"Error processing chat request: {str(e)}",
            exc_info=True,
            extra={
                "session_id": validated_data.get("session_id"),
                "user_message": validated_data.get("message", "")[:100],
            },
        )
        raise InternalServerError("Failed to process chat message")


@app.route("/api/reset", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60, key_prefix="reset")
def reset_conversation():
    """
    Reset conversation history for a session

    Request body:
    {
        "session_id": "unique-session-id" (optional, defaults to "default")
    }

    Response:
    {
        "message": "Conversation reset successfully",
        "session_id": "unique-session-id"
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id", "default")

        # Validate session_id if provided
        if session_id and not isinstance(session_id, str):
            return jsonify({"error": "session_id must be a string"}), 400

        if len(session_id) > 100:
            return jsonify({"error": "session_id too long (max 100 chars)"}), 400

        messages_cleared = 0
        if session_id in conversations:
            messages_cleared = len(conversations[session_id])
            del conversations[session_id]
            logger.info(
                f"Reset conversation for session {session_id} "
                f"({messages_cleared} messages cleared)"
            )

        return jsonify(
            {
                "message": "Conversation reset successfully",
                "session_id": session_id,
                "messages_cleared": messages_cleared,
            }
        )

    except Exception as e:
        logger.error(f"Error resetting conversation: {str(e)}", exc_info=True)
        raise InternalServerError("Failed to reset conversation")


@app.route("/api/league", methods=["GET"])
@rate_limit(max_requests=60, window_seconds=60, key_prefix="league")
def get_league():
    """
    Get basic league information

    Response:
    {
        "league_id": "...",
        "name": "...",
        "season": "...",
        ...
    }
    """
    try:
        from league_queries import get_league_info

        league_info = get_league_info()
        logger.debug("League info requested")
        return jsonify(league_info)
    except Exception as e:
        logger.error(f"Error fetching league info: {str(e)}", exc_info=True)
        raise InternalServerError("Failed to fetch league information")


@app.route("/api/standings", methods=["GET"])
@rate_limit(max_requests=60, window_seconds=60, key_prefix="standings")
def get_standings_endpoint():
    """
    Get current league standings

    Response:
    {
        "standings": [
            {
                "rank": 1,
                "team_name": "...",
                "wins": 6,
                "losses": 1,
                ...
            },
            ...
        ]
    }
    """
    try:
        from league_queries import get_standings

        standings = get_standings()
        logger.debug("Standings requested")
        return jsonify(standings)
    except Exception as e:
        logger.error(f"Error fetching standings: {str(e)}", exc_info=True)
        raise InternalServerError("Failed to fetch standings")


# API Documentation Endpoints
@app.route("/api/docs", methods=["GET"])
def api_docs():
    """
    Redirect to Swagger UI documentation

    Returns:
        Redirect to /api/docs/swagger
    """
    from flask import redirect

    return redirect("/api/docs/swagger", code=302)


@app.route("/api/docs/openapi.json", methods=["GET"])
def openapi_spec():
    """
    Get OpenAPI specification

    Returns:
        OpenAPI 3.0 specification in JSON format
    """
    return jsonify(OPENAPI_SPEC)


@app.route("/api/docs/swagger", methods=["GET"])
def swagger_ui():
    """
    Serve Swagger UI for API documentation

    Returns:
        HTML page with Swagger UI
    """
    swagger_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Fantasy League AI Assistant API - Documentation</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" />
        <style>
            body { margin: 0; padding: 0; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                SwaggerUIBundle({
                    url: "/api/docs/openapi.json",
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout"
                });
            };
        </script>
    </body>
    </html>
    """
    from flask import Response

    return Response(swagger_html, mimetype="text/html")


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("🚀 FANTASY LEAGUE ASSISTANT API SERVER")
    logger.info("=" * 70)
    logger.info(f"Server starting on http://localhost:{API_PORT}")
    logger.info(f"Environment: {FLASK_ENV}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("\nEndpoints:")
    logger.info("  GET  /api/health                - Basic health check")
    logger.info("  GET  /api/health/detailed       - Detailed health with dependencies")
    logger.info("  POST /api/chat                  - Send message to assistant")
    logger.info("  POST /api/reset                 - Reset conversation")
    logger.info("  GET  /api/league                - Get league info")
    logger.info("  GET  /api/standings             - Get standings")
    logger.info("  GET  /api/docs                  - API documentation (Swagger UI)")
    logger.info("=" * 70)
    logger.info(f"\n📚 API Documentation: http://localhost:{API_PORT}/api/docs")
    logger.info("=" * 70)

    # Debug mode based on environment
    debug_mode = FLASK_ENV == "development"

    logger.info(f"Starting Flask server (debug={debug_mode})...")
    app.run(host="0.0.0.0", port=API_PORT, debug=debug_mode, use_reloader=False)

