"""
Comprehensive health checks for application components
Monitors database, external APIs, and system resources
"""
import time
from typing import Dict, Any, List
import os
from datetime import datetime
from logger_config import setup_logger

logger = setup_logger("health_checks")


class HealthStatus:
    """Health check status constants"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


def check_database() -> Dict[str, Any]:
    """
    Check Supabase database connection

    Returns:
        Dict with status and details
    """
    start_time = time.time()

    try:
        from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
        from supabase import create_client

        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

        # Try a simple query
        response = supabase.table("leagues").select("league_id").limit(1).execute()

        latency_ms = (time.time() - start_time) * 1000

        if latency_ms > 1000:
            status = HealthStatus.DEGRADED
            message = "Database responding slowly"
        else:
            status = HealthStatus.HEALTHY
            message = "Database connection OK"

        return {
            "status": status,
            "message": message,
            "latency_ms": round(latency_ms, 2),
            "url": SUPABASE_URL,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"Database connection failed: {str(e)}",
            "latency_ms": round((time.time() - start_time) * 1000, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }


def check_openai() -> Dict[str, Any]:
    """
    Check OpenAI API connectivity

    Returns:
        Dict with status and details
    """
    start_time = time.time()

    try:
        from config import OPENAI_API_KEY
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)

        # Simple models list call to verify API key and connectivity
        models = client.models.list()

        latency_ms = (time.time() - start_time) * 1000

        return {
            "status": HealthStatus.HEALTHY,
            "message": "OpenAI API accessible",
            "latency_ms": round(latency_ms, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"OpenAI API check failed: {str(e)}",
            "latency_ms": round((time.time() - start_time) * 1000, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }


def check_memory() -> Dict[str, Any]:
    """
    Check system memory usage

    Returns:
        Dict with memory statistics
    """
    try:
        import psutil

        memory = psutil.virtual_memory()

        if memory.percent > 90:
            status = HealthStatus.UNHEALTHY
            message = "Critical memory usage"
        elif memory.percent > 75:
            status = HealthStatus.DEGRADED
            message = "High memory usage"
        else:
            status = HealthStatus.HEALTHY
            message = "Memory usage normal"

        return {
            "status": status,
            "message": message,
            "total_mb": round(memory.total / (1024 * 1024), 2),
            "used_mb": round(memory.used / (1024 * 1024), 2),
            "available_mb": round(memory.available / (1024 * 1024), 2),
            "percent": memory.percent,
        }

    except ImportError:
        # psutil not installed
        return {
            "status": HealthStatus.HEALTHY,
            "message": "Memory monitoring not available (psutil not installed)",
        }
    except Exception as e:
        logger.error(f"Memory check failed: {e}")
        return {"status": HealthStatus.DEGRADED, "message": f"Memory check error: {str(e)}"}


def check_disk() -> Dict[str, Any]:
    """
    Check disk space

    Returns:
        Dict with disk statistics
    """
    try:
        import psutil

        disk = psutil.disk_usage("/")

        if disk.percent > 90:
            status = HealthStatus.UNHEALTHY
            message = "Critical disk space"
        elif disk.percent > 75:
            status = HealthStatus.DEGRADED
            message = "Low disk space"
        else:
            status = HealthStatus.HEALTHY
            message = "Disk space OK"

        return {
            "status": status,
            "message": message,
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent,
        }

    except ImportError:
        return {
            "status": HealthStatus.HEALTHY,
            "message": "Disk monitoring not available (psutil not installed)",
        }
    except Exception as e:
        logger.error(f"Disk check failed: {e}")
        return {"status": HealthStatus.DEGRADED, "message": f"Disk check error: {str(e)}"}


def run_all_health_checks(include_external: bool = False) -> Dict[str, Any]:
    """
    Run all health checks

    Args:
        include_external: Include external service checks (database, OpenAI)

    Returns:
        Dict with overall status and individual check results
    """
    checks = {
        "memory": check_memory(),
        "disk": check_disk(),
    }

    if include_external:
        checks["database"] = check_database()
        checks["openai"] = check_openai()

    # Determine overall status
    statuses = [check["status"] for check in checks.values()]

    if any(s == HealthStatus.UNHEALTHY for s in statuses):
        overall_status = HealthStatus.UNHEALTHY
    elif any(s == HealthStatus.DEGRADED for s in statuses):
        overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.HEALTHY

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }

