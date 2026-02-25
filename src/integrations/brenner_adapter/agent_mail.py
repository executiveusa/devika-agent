from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import os
import time
import logging
import requests

logger = logging.getLogger(__name__)


class BrennerAdapterError(RuntimeError):
    """Base Brenner adapter error."""


class BrennerNotConfiguredError(BrennerAdapterError):
    """Raised when Brenner is not configured for real transport."""


class BrennerConnectionError(BrennerAdapterError):
    """Raised when connection to Brenner fails."""


class BrennerAuthError(BrennerAdapterError):
    """Raised when authentication with Brenner fails."""


class BrennerStatus(Enum):
    """Status of Brenner adapter."""
    DISABLED = "disabled"
    SIMULATED = "simulated"
    CONFIGURED = "configured"
    ERROR = "error"


@dataclass
class BrennerConfig:
    endpoint: str
    token: str
    timeout_seconds: int = 30
    max_retries: int = 3
    enabled: bool = False
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        if self.enabled:
            if not self.endpoint:
                issues.append("BRENNER_HTTP_URL is required when enabled")
            if not self.token:
                issues.append("BRENNER_HTTP_TOKEN is recommended for authenticated requests")
            if self.timeout_seconds < 1:
                issues.append("BRENNER_HTTP_TIMEOUT must be at least 1 second")
            if self.max_retries < 0:
                issues.append("BRENNER_HTTP_RETRIES must be non-negative")
        return issues


@dataclass
class BrennerHealthCheck:
    """Result of a Brenner health check."""
    status: BrennerStatus
    message: str
    latency_ms: Optional[float] = None
    issues: List[str] = field(default_factory=list)


class BrennerAdapter:
    """Brenner adapter using authenticated HTTP transport.

    This adapter is disabled by default and only runs when explicitly configured.
    
    Environment Variables:
        BRENNER_HTTP_URL: HTTP endpoint for Brenner service (required for real transport)
        BRENNER_HTTP_TOKEN: Authentication token (recommended)
        BRENNER_HTTP_TIMEOUT: Request timeout in seconds (default: 30)
        BRENNER_HTTP_RETRIES: Maximum retry attempts (default: 3)
        BRENNER_SIMULATE: Set to "true" to enable simulation mode
    """

    def __init__(self, simulate: bool = False):
        cfg_sim = os.environ.get("BRENNER_SIMULATE")
        simulate_enabled = simulate
        if cfg_sim is not None:
            simulate_enabled = cfg_sim.lower() in ("1", "true", "yes")

        endpoint = os.environ.get("BRENNER_HTTP_URL", "").strip()
        token = os.environ.get("BRENNER_HTTP_TOKEN", "").strip()
        timeout_seconds = int(os.environ.get("BRENNER_HTTP_TIMEOUT", "30"))
        max_retries = int(os.environ.get("BRENNER_HTTP_RETRIES", "3"))

        self.config = BrennerConfig(
            endpoint=endpoint,
            token=token,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            enabled=bool(endpoint),
        )
        self.simulate = simulate_enabled
        self._startup_validated = False
        
        # Log configuration state at initialization
        self._log_configuration_state()

    def _log_configuration_state(self) -> None:
        """Log the current configuration state for debugging."""
        if self.simulate:
            logger.info("BrennerAdapter initialized in SIMULATION mode")
        elif self.config.enabled:
            logger.info(f"BrennerAdapter initialized with endpoint: {self._mask_endpoint()}")
            issues = self.config.validate()
            if issues:
                for issue in issues:
                    logger.warning(f"Brenner config issue: {issue}")
        else:
            logger.info("BrennerAdapter initialized in DISABLED state (no endpoint configured)")

    def _mask_endpoint(self) -> str:
        """Mask endpoint URL for safe logging."""
        if not self.config.endpoint:
            return "<not set>"
        # Show protocol and domain only
        parts = self.config.endpoint.split("/")
        if len(parts) >= 3:
            return f"{parts[0]}//{parts[2]}/***"
        return "***"

    def configured(self) -> bool:
        return self.config.enabled
    
    def get_status(self) -> BrennerStatus:
        """Get current adapter status."""
        if self.simulate:
            return BrennerStatus.SIMULATED
        elif self.config.enabled:
            return BrennerStatus.CONFIGURED
        else:
            return BrennerStatus.DISABLED
    
    def validate_startup(self, strict: bool = False) -> BrennerHealthCheck:
        """Validate configuration at startup.
        
        Args:
            strict: If True, raise exception on validation failures
            
        Returns:
            BrennerHealthCheck with validation results
            
        Raises:
            BrennerNotConfiguredError: If strict=True and configuration is invalid
        """
        self._startup_validated = True
        
        if self.simulate:
            return BrennerHealthCheck(
                status=BrennerStatus.SIMULATED,
                message="Running in simulation mode - no real transport"
            )
        
        if not self.config.enabled:
            msg = "Brenner adapter is disabled (no BRENNER_HTTP_URL configured)"
            if strict:
                raise BrennerNotConfiguredError(msg)
            return BrennerHealthCheck(
                status=BrennerStatus.DISABLED,
                message=msg
            )
        
        issues = self.config.validate()
        if issues:
            msg = f"Configuration issues: {'; '.join(issues)}"
            if strict:
                raise BrennerNotConfiguredError(msg)
            return BrennerHealthCheck(
                status=BrennerStatus.ERROR,
                message=msg,
                issues=issues
            )
        
        return BrennerHealthCheck(
            status=BrennerStatus.CONFIGURED,
            message="Configuration valid"
        )
    
    def health_check(self, timeout: int = 5) -> BrennerHealthCheck:
        """Perform a health check against the Brenner service.
        
        Args:
            timeout: Timeout for health check request in seconds
            
        Returns:
            BrennerHealthCheck with health check results
        """
        if self.simulate:
            return BrennerHealthCheck(
                status=BrennerStatus.SIMULATED,
                message="Simulation mode - health check not applicable"
            )
        
        if not self.config.enabled:
            return BrennerHealthCheck(
                status=BrennerStatus.DISABLED,
                message="Adapter disabled - no endpoint configured"
            )
        
        start_time = time.time()
        try:
            headers = {"Content-Type": "application/json"}
            if self.config.token:
                headers["Authorization"] = f"Bearer {self.config.token}"
            
            # Try a simple ping/health endpoint
            health_url = f"{self.config.endpoint.rstrip('/')}/health"
            resp = requests.get(
                health_url,
                headers=headers,
                timeout=timeout
            )
            latency_ms = (time.time() - start_time) * 1000
            
            if resp.status_code == 200:
                return BrennerHealthCheck(
                    status=BrennerStatus.CONFIGURED,
                    message="Brenner service is healthy",
                    latency_ms=latency_ms
                )
            elif resp.status_code == 401:
                return BrennerHealthCheck(
                    status=BrennerStatus.ERROR,
                    message="Authentication failed - check BRENNER_HTTP_TOKEN",
                    latency_ms=latency_ms
                )
            else:
                return BrennerHealthCheck(
                    status=BrennerStatus.ERROR,
                    message=f"Health check returned status {resp.status_code}",
                    latency_ms=latency_ms
                )
        except requests.exceptions.Timeout:
            return BrennerHealthCheck(
                status=BrennerStatus.ERROR,
                message=f"Health check timed out after {timeout}s"
            )
        except requests.exceptions.ConnectionError as e:
            return BrennerHealthCheck(
                status=BrennerStatus.ERROR,
                message=f"Connection failed: {str(e)[:100]}"
            )
        except Exception as e:
            return BrennerHealthCheck(
                status=BrennerStatus.ERROR,
                message=f"Health check failed: {str(e)[:100]}"
            )

    def send_query(self, query: str, stream: bool = False) -> Dict[str, Any]:
        """Send a query to Brenner and return a structured response."""
        if not query or not query.strip():
            raise BrennerAdapterError("query must not be empty")

        if self.simulate:
            return {
                "source": "brenner_sim",
                "query": query,
                "reply": f"[Simulated Brenner] {query}",
                "stream": stream,
                "status": "simulated",
            }

        if not self.configured():
            raise BrennerNotConfiguredError("Brenner HTTP endpoint is not configured")

        headers = {"Content-Type": "application/json"}
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"

        last_error: Optional[str] = None
        for attempt in range(self.config.max_retries):
            try:
                resp = requests.post(
                    self.config.endpoint,
                    json={"query": query, "stream": stream},
                    headers=headers,
                    timeout=self.config.timeout_seconds,
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "source": "brenner_http",
                    "query": query,
                    "reply": data.get("reply", data),
                    "stream": stream,
                    "status": "ok",
                }
            except Exception as exc:
                last_error = str(exc)
                if attempt < self.config.max_retries - 1:
                    time.sleep(min(2 ** attempt, 5))

        raise BrennerAdapterError(f"Brenner request failed: {last_error}")
