"""
Observability utilities for DocOps Agent.
Provides LangSmith integration and latency tracking.
"""
import os
import time
import logging
import functools
from typing import Optional, Callable, Any
from datetime import datetime
from contextlib import contextmanager

from src.utils.config import get_settings

logger = logging.getLogger(__name__)


class LatencyTracker:
    """Track latency for operations."""

    def __init__(self):
        self.measurements = []

    @contextmanager
    def track(self, operation_name: str):
        """Context manager to track operation latency."""
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            self.measurements.append({
                "operation": operation_name,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
            })

    def get_stats(self) -> dict:
        """Get latency statistics."""
        if not self.measurements:
            return {}

        durations = [m["duration_ms"] for m in self.measurements]
        return {
            "total_operations": len(durations),
            "avg_latency_ms": sum(durations) / len(durations),
            "min_latency_ms": min(durations),
            "max_latency_ms": max(durations),
        }

    def clear(self):
        """Clear measurements."""
        self.measurements = []


def setup_langsmith_tracing():
    """
    Set up LangSmith tracing via environment variables.

    Returns:
        True if tracing is configured, False otherwise
    """
    # Check both config settings and direct environment variables
    # (LANGCHAIN_API_KEY and LANGCHAIN_TRACING_V2 are the standard env var names)
    settings = get_settings()

    # Get API key from either config or direct env var
    api_key = settings.langsmith_api_key or os.environ.get("LANGCHAIN_API_KEY", "")
    tracing_enabled = settings.langchain_tracing_v2 or os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true"

    if not tracing_enabled or not api_key:
        logger.info(f"LangSmith tracing not configured. tracing_enabled={tracing_enabled}, has_api_key={bool(api_key)}")
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

    logger.info("LangSmith tracing configured successfully")
    return True


def with_latency_tracking(operation_name: str):
    """
    Decorator to track latency for an operation.

    Args:
        operation_name: Name of the operation to track

    Returns:
        Decorated function with latency tracking
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                print(f"[LATENCY] {operation_name}: {duration_ms:.2f}ms")
        return wrapper
    return decorator


# Global latency tracker instance
latency_tracker = LatencyTracker()


__all__ = [
    "setup_langsmith_tracing",
    "with_latency_tracking",
    "LatencyTracker",
    "latency_tracker",
]
