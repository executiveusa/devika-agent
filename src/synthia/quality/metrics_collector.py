"""Quality metrics collector utility."""

from typing import Any, Dict


class MetricsCollector:
    """Collects lightweight quality metadata.

    Kept intentionally simple for deterministic CI usage.
    """

    def collect(self, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = context or {}
        return {
            "build_id": context.get("build_id", "local"),
            "commit": context.get("commit", "unknown"),
            "timestamp": context.get("timestamp", "unknown"),
        }
