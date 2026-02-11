"""
Logging configuration for DocOps Agent.
"""
import logging
import sys
import json
from typing import Optional, Any, Dict
from datetime import datetime


class TraceLogger:
    """Structured logger for agent traces."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.traces = []

    def trace(
        self,
        agent: str,
        action: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a trace event."""
        trace_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "action": action,
            "status": status,
            "metadata": metadata or {}
        }
        self.traces.append(trace_data)

        self.logger.info(
            f"[TRACE] {agent}: {action} - {status}",
            extra={"trace": trace_data}
        )

    def start_span(self, agent: str, action: str) -> Dict[str, Any]:
        """Start a tracing span."""
        return {
            "agent": agent,
            "action": action,
            "start_time": datetime.utcnow().isoformat()
        }

    def end_span(self, span: Dict[str, Any], status: str = "success"):
        """End a tracing span."""
        span["end_time"] = datetime.utcnow().isoformat()
        span["status"] = status
        self.trace(span["agent"], span["action"], status)

    def get_traces(self) -> list:
        """Get all recorded traces."""
        return self.traces

    def clear_traces(self):
        """Clear recorded traces."""
        self.traces = []


class LatencyLogger:
    """Logger for tracking operation latency."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.latency_records = []

    def log_latency(
        self,
        operation: str,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log operation latency."""
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "duration_ms": duration_ms,
            "metadata": metadata or {}
        }
        self.latency_records.append(record)

        self.logger.info(
            f"[LATENCY] {operation}: {duration_ms:.2f}ms",
            extra={"latency": record}
        )

    def get_latencies(self) -> list:
        """Get all latency records."""
        return self.latency_records

    def clear_latencies(self):
        """Clear latency records."""
        self.latency_records = []


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages

    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger("docops")
    logger.setLevel(getattr(logging, level.upper()))

    return logger


# Default logger instance
logger = setup_logging()

# Trace and latency loggers
trace_logger = TraceLogger(logger)
latency_logger = LatencyLogger(logger)
