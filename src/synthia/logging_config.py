"""Structured logging configuration for SYNTHIA.

Provides:
- JSON-formatted structured logs
- Log level configuration
- Context-aware logging
- Error taxonomy integration
"""

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class LogLevel(Enum):
    """Log levels for SYNTHIA."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """Error categories for classification."""
    CONFIGURATION = "configuration"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    INTERNAL = "internal"
    EXTERNAL = "external"
    DEPENDENCY = "dependency"
    SECURITY = "security"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorTaxonomy:
    """Structured error classification."""
    code: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    remediation: Optional[str] = None
    documentation_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "remediation": self.remediation,
            "documentation_url": self.documentation_url,
        }


# Predefined error codes
ERROR_TAXONOMY: Dict[str, ErrorTaxonomy] = {
    # Configuration errors (CFG-xxx)
    "CFG-001": ErrorTaxonomy(
        code="CFG-001",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        message="Missing required configuration",
        remediation="Set the required environment variable or configuration value",
    ),
    "CFG-002": ErrorTaxonomy(
        code="CFG-002",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.MEDIUM,
        message="Invalid configuration value",
        remediation="Check the configuration format and valid options",
    ),
    "CFG-003": ErrorTaxonomy(
        code="CFG-003",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.LOW,
        message="Using default configuration",
        remediation="Review and customize configuration for production use",
    ),

    # Network errors (NET-xxx)
    "NET-001": ErrorTaxonomy(
        code="NET-001",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.HIGH,
        message="Connection refused",
        remediation="Check if the target service is running and accessible",
    ),
    "NET-002": ErrorTaxonomy(
        code="NET-002",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.MEDIUM,
        message="DNS resolution failed",
        remediation="Check DNS configuration and network connectivity",
    ),
    "NET-003": ErrorTaxonomy(
        code="NET-003",
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.HIGH,
        message="SSL/TLS certificate error",
        remediation="Verify certificate validity or update CA certificates",
    ),

    # Authentication errors (AUTH-xxx)
    "AUTH-001": ErrorTaxonomy(
        code="AUTH-001",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        message="Invalid credentials",
        remediation="Verify API keys, tokens, or passwords are correct",
    ),
    "AUTH-002": ErrorTaxonomy(
        code="AUTH-002",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.MEDIUM,
        message="Token expired",
        remediation="Refresh or regenerate the authentication token",
    ),
    "AUTH-003": ErrorTaxonomy(
        code="AUTH-003",
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        message="Insufficient permissions",
        remediation="Check user roles and permissions for the requested action",
    ),

    # Validation errors (VAL-xxx)
    "VAL-001": ErrorTaxonomy(
        code="VAL-001",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        message="Invalid input format",
        remediation="Check input format against expected schema",
    ),
    "VAL-002": ErrorTaxonomy(
        code="VAL-002",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        message="Required field missing",
        remediation="Provide all required fields in the request",
    ),
    "VAL-003": ErrorTaxonomy(
        code="VAL-003",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        message="Value out of range",
        remediation="Ensure values are within acceptable bounds",
    ),

    # Resource errors (RES-xxx)
    "RES-001": ErrorTaxonomy(
        code="RES-001",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.HIGH,
        message="Resource not found",
        remediation="Verify the resource identifier and access permissions",
    ),
    "RES-002": ErrorTaxonomy(
        code="RES-002",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.CRITICAL,
        message="Out of memory",
        remediation="Increase available memory or optimize resource usage",
    ),
    "RES-003": ErrorTaxonomy(
        code="RES-003",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.HIGH,
        message="Disk space exhausted",
        remediation="Free up disk space or expand storage capacity",
    ),

    # Timeout errors (TIM-xxx)
    "TIM-001": ErrorTaxonomy(
        code="TIM-001",
        category=ErrorCategory.TIMEOUT,
        severity=ErrorSeverity.MEDIUM,
        message="Operation timed out",
        remediation="Increase timeout value or check system performance",
    ),
    "TIM-002": ErrorTaxonomy(
        code="TIM-002",
        category=ErrorCategory.TIMEOUT,
        severity=ErrorSeverity.HIGH,
        message="Deadline exceeded",
        remediation="Optimize operation or increase deadline threshold",
    ),

    # Internal errors (INT-xxx)
    "INT-001": ErrorTaxonomy(
        code="INT-001",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.CRITICAL,
        message="Internal server error",
        remediation="Check logs for details and report if persistent",
    ),
    "INT-002": ErrorTaxonomy(
        code="INT-002",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.HIGH,
        message="Unexpected exception",
        remediation="Review exception details and handle appropriately",
    ),
    "INT-003": ErrorTaxonomy(
        code="INT-003",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.MEDIUM,
        message="Feature not implemented",
        remediation="Check documentation for feature availability",
    ),

    # External errors (EXT-xxx)
    "EXT-001": ErrorTaxonomy(
        code="EXT-001",
        category=ErrorCategory.EXTERNAL,
        severity=ErrorSeverity.HIGH,
        message="External service unavailable",
        remediation="Check external service status and try again later",
    ),
    "EXT-002": ErrorTaxonomy(
        code="EXT-002",
        category=ErrorCategory.EXTERNAL,
        severity=ErrorSeverity.MEDIUM,
        message="Rate limit exceeded",
        remediation="Reduce request frequency or implement backoff",
    ),
    "EXT-003": ErrorTaxonomy(
        code="EXT-003",
        category=ErrorCategory.EXTERNAL,
        severity=ErrorSeverity.HIGH,
        message="External API error",
        remediation="Check API documentation and error response details",
    ),

    # Dependency errors (DEP-xxx)
    "DEP-001": ErrorTaxonomy(
        code="DEP-001",
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.HIGH,
        message="Missing dependency",
        remediation="Install required dependency with pip install",
    ),
    "DEP-002": ErrorTaxonomy(
        code="DEP-002",
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.MEDIUM,
        message="Incompatible dependency version",
        remediation="Update or downgrade dependency to compatible version",
    ),
    "DEP-003": ErrorTaxonomy(
        code="DEP-003",
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.HIGH,
        message="Dependency vulnerability detected",
        remediation="Update dependency to patched version",
    ),

    # Security errors (SEC-xxx)
    "SEC-001": ErrorTaxonomy(
        code="SEC-001",
        category=ErrorCategory.SECURITY,
        severity=ErrorSeverity.CRITICAL,
        message="Security vulnerability detected",
        remediation="Apply security patch immediately",
    ),
    "SEC-002": ErrorTaxonomy(
        code="SEC-002",
        category=ErrorCategory.SECURITY,
        severity=ErrorSeverity.HIGH,
        message="Suspicious activity detected",
        remediation="Review activity logs and implement additional controls",
    ),
    "SEC-003": ErrorTaxonomy(
        code="SEC-003",
        category=ErrorCategory.SECURITY,
        severity=ErrorSeverity.MEDIUM,
        message="Insecure configuration",
        remediation="Update configuration to follow security best practices",
    ),
}


class StructuredLogFormatter(logging.Formatter):
    """JSON-formatted structured log formatter."""

    def __init__(self, include_extra: bool = True):
        """Initialize formatter.

        Args:
            include_extra: Whether to include extra fields in output
        """
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add error code if present
        if hasattr(record, "error_code"):
            error_code = record.error_code
            if error_code in ERROR_TAXONOMY:
                log_data["error"] = ERROR_TAXONOMY[error_code].to_dict()
            else:
                log_data["error_code"] = error_code

        # Add extra fields
        if self.include_extra:
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in {
                    "name", "msg", "args", "created", "filename", "funcName",
                    "levelname", "levelno", "lineno", "module", "msecs",
                    "pathname", "process", "processName", "relativeCreated",
                    "stack_info", "exc_info", "exc_text", "thread", "threadName",
                    "message", "error_code",
                }:
                    try:
                        # Try to serialize the value
                        json.dumps(value)
                        extra_fields[key] = value
                    except (TypeError, ValueError):
                        extra_fields[key] = str(value)

            if extra_fields:
                log_data["extra"] = extra_fields

        return json.dumps(log_data)


class StructuredLogger:
    """Context-aware structured logger."""

    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize structured logger.

        Args:
            name: Logger name
            level: Minimum log level
            context: Default context fields
        """
        self.logger = logging.getLogger(name)
        self.context = context or {}
        self._configure_logger(level)

    def _configure_logger(self, level: LogLevel) -> None:
        """Configure logger with structured formatter.

        Args:
            level: Minimum log level
        """
        self.logger.setLevel(getattr(logging, level.value))

        # Remove existing handlers
        self.logger.handlers = []

        # Add structured handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredLogFormatter())
        self.logger.addHandler(handler)

    def _log(
        self,
        level: int,
        message: str,
        error_code: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """Log a message with optional error code and extra fields.

        Args:
            level: Log level
            message: Log message
            error_code: Optional error code from taxonomy
            **kwargs: Additional fields to include
        """
        extra = {**self.context, **kwargs}
        if error_code:
            extra["error_code"] = error_code

        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, error_code: Optional[str] = None, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, error_code=error_code, **kwargs)

    def error(self, message: str, error_code: Optional[str] = None, **kwargs: Any) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, error_code=error_code, **kwargs)

    def critical(self, message: str, error_code: Optional[str] = None, **kwargs: Any) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, error_code=error_code, **kwargs)

    def with_context(self, **kwargs: Any) -> "StructuredLogger":
        """Create a new logger with additional context.

        Args:
            **kwargs: Context fields to add

        Returns:
            New StructuredLogger with merged context
        """
        new_context = {**self.context, **kwargs}
        return StructuredLogger(
            self.logger.name,
            level=LogLevel(self.logger.level),
            context=new_context
        )


def configure_logging(
    level: LogLevel = LogLevel.INFO,
    log_format: str = "json"
) -> None:
    """Configure global logging for SYNTHIA.

    Args:
        level: Minimum log level
        log_format: Output format ("json" or "text")
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.value))

    # Remove existing handlers
    root_logger.handlers = []

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    if log_format == "json":
        handler.setFormatter(StructuredLogFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

    root_logger.addHandler(handler)


def get_logger(
    name: str,
    level: Optional[LogLevel] = None,
    context: Optional[Dict[str, Any]] = None
) -> StructuredLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name
        level: Optional minimum log level
        context: Optional default context

    Returns:
        StructuredLogger instance
    """
    log_level = level or LogLevel(os.environ.get("SYNTHIA_LOG_LEVEL", "INFO").upper())
    return StructuredLogger(name, level=log_level, context=context)


def get_error_taxonomy(code: str) -> Optional[ErrorTaxonomy]:
    """Get error taxonomy by code.

    Args:
        code: Error code

    Returns:
        ErrorTaxonomy if found, None otherwise
    """
    return ERROR_TAXONOMY.get(code)


def classify_error(error: Exception) -> ErrorTaxonomy:
    """Classify an exception into error taxonomy.

    Args:
        error: Exception to classify

    Returns:
        ErrorTaxonomy for the exception
    """
    error_type = type(error).__name__
    error_message = str(error)

    # Map common exceptions to taxonomy
    if "connection" in error_message.lower() or "refused" in error_message.lower():
        return ERROR_TAXONOMY.get("NET-001", ERROR_TAXONOMY["INT-002"])
    elif "timeout" in error_message.lower():
        return ERROR_TAXONOMY.get("TIM-001", ERROR_TAXONOMY["INT-002"])
    elif "auth" in error_message.lower() or "credential" in error_message.lower():
        return ERROR_TAXONOMY.get("AUTH-001", ERROR_TAXONOMY["INT-002"])
    elif "not found" in error_message.lower():
        return ERROR_TAXONOMY.get("RES-001", ERROR_TAXONOMY["INT-002"])
    elif "permission" in error_message.lower() or "forbidden" in error_message.lower():
        return ERROR_TAXONOMY.get("AUTH-003", ERROR_TAXONOMY["INT-002"])
    elif "config" in error_message.lower():
        return ERROR_TAXONOMY.get("CFG-001", ERROR_TAXONOMY["INT-002"])
    elif "validation" in error_message.lower() or "invalid" in error_message.lower():
        return ERROR_TAXONOMY.get("VAL-001", ERROR_TAXONOMY["INT-002"])
    else:
        return ERROR_TAXONOMY["INT-002"]
