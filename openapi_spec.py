"""
OpenAPI specification for Fantasy League Assistant API
"""

OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Fantasy League AI Assistant API",
        "version": "1.0.0",
        "description": """
AI-powered assistant for Sleeper fantasy football leagues.
Ask questions in natural language and get instant answers about your league.

**Features:**
- Natural language querying
- League standings and statistics
- Player ownership lookup
- Trade history and analysis
- Real-time NFL stats integration
""",
        "contact": {
            "name": "API Support",
            "url": "https://github.com/yourusername/fantasy-assistant",
        },
        "license": {"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    },
    "servers": [
        {"url": "http://localhost:5001", "description": "Local development server"},
        {"url": "https://api.yourdomain.com", "description": "Production server"},
    ],
    "tags": [
        {"name": "Health", "description": "Service health and monitoring"},
        {"name": "Chat", "description": "AI chat interface"},
        {"name": "League Data", "description": "Fantasy league information"},
    ],
    "paths": {
        "/api/health": {
            "get": {
                "tags": ["Health"],
                "summary": "Basic health check",
                "description": "Fast health check without external dependencies",
                "responses": {
                    "200": {
                        "description": "Service is healthy",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HealthResponse"}
                            }
                        },
                    }
                },
            }
        },
        "/api/health/detailed": {
            "get": {
                "tags": ["Health"],
                "summary": "Detailed health check",
                "description": "Comprehensive health check including external dependencies",
                "parameters": [
                    {
                        "name": "include_external",
                        "in": "query",
                        "description": "Include checks for database and external APIs",
                        "required": False,
                        "schema": {"type": "boolean", "default": False},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Service is healthy or degraded",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DetailedHealthResponse"
                                }
                            }
                        },
                    },
                    "503": {
                        "description": "Service is unhealthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DetailedHealthResponse"
                                }
                            }
                        },
                    },
                },
            }
        },
        "/api/chat": {
            "post": {
                "tags": ["Chat"],
                "summary": "Send message to AI assistant",
                "description": "Chat with the AI assistant about your fantasy league",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ChatRequest"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ChatResponse"}
                            }
                        },
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        },
                    },
                    "429": {
                        "description": "Rate limit exceeded",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/RateLimitResponse"
                                }
                            }
                        },
                    },
                    "500": {
                        "description": "Internal server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        },
                    },
                },
            }
        },
        "/api/reset": {
            "post": {
                "tags": ["Chat"],
                "summary": "Reset conversation",
                "description": "Clear conversation history for a session",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ResetRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Conversation reset successful",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ResetResponse"}
                            }
                        },
                    }
                },
            }
        },
        "/api/league": {
            "get": {
                "tags": ["League Data"],
                "summary": "Get league information",
                "description": "Retrieve basic league metadata",
                "responses": {
                    "200": {
                        "description": "League information",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/LeagueInfo"}
                            }
                        },
                    },
                    "500": {
                        "description": "Failed to fetch league data",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        },
                    },
                },
            }
        },
        "/api/standings": {
            "get": {
                "tags": ["League Data"],
                "summary": "Get league standings",
                "description": "Retrieve current league standings with records and points",
                "responses": {
                    "200": {
                        "description": "League standings",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Standing"},
                                }
                            }
                        },
                    },
                    "500": {
                        "description": "Failed to fetch standings",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        },
                    },
                },
            }
        },
    },
    "components": {
        "schemas": {
            "HealthResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "ok"},
                    "service": {
                        "type": "string",
                        "example": "Fantasy League Assistant API",
                    },
                    "version": {"type": "string", "example": "1.0.0"},
                    "port": {"type": "integer", "example": 5001},
                    "environment": {"type": "string", "example": "production"},
                    "active_sessions": {"type": "integer", "example": 5},
                },
            },
            "DetailedHealthResponse": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["healthy", "degraded", "unhealthy"],
                    },
                    "timestamp": {"type": "string", "format": "date-time"},
                    "checks": {
                        "type": "object",
                        "properties": {
                            "database": {"$ref": "#/components/schemas/HealthCheck"},
                            "openai": {"$ref": "#/components/schemas/HealthCheck"},
                            "memory": {"$ref": "#/components/schemas/HealthCheck"},
                            "disk": {"$ref": "#/components/schemas/HealthCheck"},
                        },
                    },
                },
            },
            "HealthCheck": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["healthy", "degraded", "unhealthy"],
                    },
                    "message": {"type": "string"},
                    "latency_ms": {"type": "number"},
                },
            },
            "ChatRequest": {
                "type": "object",
                "required": ["message"],
                "properties": {
                    "message": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 5000,
                        "example": "What are the current standings?",
                    },
                    "session_id": {
                        "type": "string",
                        "maxLength": 100,
                        "example": "user-123-session",
                    },
                },
            },
            "ChatResponse": {
                "type": "object",
                "properties": {
                    "response": {
                        "type": "string",
                        "example": "Here are the current standings:\n\n| Rank | Team | Record |...",
                    },
                    "session_id": {"type": "string", "example": "user-123-session"},
                    "message_count": {"type": "integer", "example": 5},
                },
            },
            "ResetRequest": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "maxLength": 100,
                        "example": "user-123-session",
                    }
                },
            },
            "ResetResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Conversation reset successfully",
                    },
                    "session_id": {"type": "string", "example": "user-123-session"},
                    "messages_cleared": {"type": "integer", "example": 10},
                },
            },
            "LeagueInfo": {
                "type": "object",
                "properties": {
                    "league_id": {"type": "string"},
                    "name": {"type": "string"},
                    "season": {"type": "string"},
                    "status": {"type": "string"},
                },
            },
            "Standing": {
                "type": "object",
                "properties": {
                    "rank": {"type": "integer"},
                    "team_name": {"type": "string"},
                    "owner": {"type": "string"},
                    "wins": {"type": "integer"},
                    "losses": {"type": "integer"},
                    "points_for": {"type": "number"},
                    "points_against": {"type": "number"},
                },
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "message": {"type": "string"},
                    "field": {"type": "string"},
                },
            },
            "RateLimitResponse": {
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "Rate limit exceeded"},
                    "message": {
                        "type": "string",
                        "example": "Too many requests. Limit: 30 per 60s",
                    },
                    "retry_after": {"type": "integer", "example": 45},
                },
            },
        }
    },
}

