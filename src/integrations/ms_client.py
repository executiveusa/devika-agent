"""Meta-Skill client with deterministic CLI contract and caching.

This client interfaces with the `ms` CLI tool for skill discovery and retrieval.
It gracefully handles the case where the CLI is not installed.

Environment Variables:
    MS_PATH: Path to the ms CLI binary (default: "ms")
    MS_TIMEOUT: Timeout for CLI operations in seconds (default: 20)
    MS_CACHE_TTL: Cache time-to-live in seconds (default: 300, 0 to disable)
"""
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import shutil
import subprocess
import time
import logging
import os

logger = logging.getLogger(__name__)


class MSClientError(RuntimeError):
    """Base error for MS client operations."""


class MSClientNotAvailableError(MSClientError):
    """Raised when the ms CLI is not available and strict mode is enabled."""


class MSClientTimeoutError(MSClientError):
    """Raised when a CLI operation times out."""


class MSClientParseError(MSClientError):
    """Raised when CLI output cannot be parsed."""


class MSStatus(Enum):
    """Status of the MS client."""
    AVAILABLE = "available"
    NOT_INSTALLED = "not_installed"
    ERROR = "error"


@dataclass
class MSConfig:
    """Configuration for the MS client."""
    ms_path: str = "ms"
    timeout: int = 20
    cache_ttl: int = 300  # 5 minutes, 0 to disable
    
    @classmethod
    def from_env(cls) -> "MSConfig":
        """Create configuration from environment variables."""
        return cls(
            ms_path=os.environ.get("MS_PATH", "ms"),
            timeout=int(os.environ.get("MS_TIMEOUT", "20")),
            cache_ttl=int(os.environ.get("MS_CACHE_TTL", "300")),
        )


@dataclass
class MSCacheEntry:
    """A cached entry with expiration."""
    data: Any
    timestamp: float
    
    def is_expired(self, ttl: int) -> bool:
        """Check if the entry is expired."""
        if ttl <= 0:
            return True  # TTL disabled means always expired
        return (time.time() - self.timestamp) > ttl


@dataclass
class MSHealthCheck:
    """Result of an MS client health check."""
    status: MSStatus
    message: str
    version: Optional[str] = None
    path: Optional[str] = None


class MSClient:
    """Client for the Meta-Skill CLI tool.
    
    This client provides a Python interface to the `ms` CLI for skill
    discovery and retrieval. It includes caching, timeout handling,
    and graceful degradation when the CLI is not available.
    
    Example:
        client = MSClient()
        if client.available():
            skills = client.search_skills("code review")
            for skill in skills:
                print(skill.get("name"))
    """
    
    def __init__(self, config: Optional[MSConfig] = None):
        """Initialize the MS client.
        
        Args:
            config: Optional configuration. If not provided, uses env vars.
        """
        self.config = config or MSConfig.from_env()
        self._cache: Dict[Tuple[str, str], MSCacheEntry] = {}
        self._available: Optional[bool] = None
        self._version: Optional[str] = None
        
        # Log initialization state
        self._log_initialization_state()
    
    def _log_initialization_state(self) -> None:
        """Log the initialization state for debugging."""
        if self.available():
            logger.info(
                f"MSClient initialized with CLI at: {self.config.ms_path} "
                f"(timeout: {self.config.timeout}s, cache_ttl: {self.config.cache_ttl}s)"
            )
        else:
            logger.info(
                f"MSClient initialized but CLI not found at: {self.config.ms_path}. "
                "Skill search/fetch will return empty results."
            )
    
    def available(self) -> bool:
        """Check if the ms CLI is available.
        
        Returns:
            True if the CLI is installed and executable, False otherwise.
        """
        if self._available is None:
            self._available = shutil.which(self.config.ms_path) is not None
        return self._available
    
    def get_status(self) -> MSStatus:
        """Get the current status of the client.
        
        Returns:
            MSStatus indicating availability state.
        """
        if self.available():
            return MSStatus.AVAILABLE
        return MSStatus.NOT_INSTALLED
    
    def health_check(self) -> MSHealthCheck:
        """Perform a health check on the MS client.
        
        Returns:
            MSHealthCheck with status and version information.
        """
        if not self.available():
            return MSHealthCheck(
                status=MSStatus.NOT_INSTALLED,
                message=f"ms CLI not found at path: {self.config.ms_path}"
            )
        
        try:
            result = subprocess.run(
                [self.config.ms_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            version = result.stdout.strip() or result.stderr.strip()
            return MSHealthCheck(
                status=MSStatus.AVAILABLE,
                message="ms CLI is available and working",
                version=version,
                path=shutil.which(self.config.ms_path),
            )
        except subprocess.TimeoutExpired:
            return MSHealthCheck(
                status=MSStatus.ERROR,
                message="ms CLI health check timed out"
            )
        except Exception as e:
            return MSHealthCheck(
                status=MSStatus.ERROR,
                message=f"ms CLI health check failed: {str(e)[:100]}"
            )
    
    def _get_cached(self, key: Tuple[str, str]) -> Optional[Any]:
        """Get a cached value if not expired.
        
        Args:
            key: Cache key tuple.
            
        Returns:
            Cached data or None if not found/expired.
        """
        if self.config.cache_ttl <= 0:
            return None
        
        entry = self._cache.get(key)
        if entry is None:
            return None
        
        if entry.is_expired(self.config.cache_ttl):
            del self._cache[key]
            return None
        
        return entry.data
    
    def _set_cached(self, key: Tuple[str, str], data: Any) -> None:
        """Set a cached value.
        
        Args:
            key: Cache key tuple.
            data: Data to cache.
        """
        if self.config.cache_ttl > 0:
            self._cache[key] = MSCacheEntry(data=data, timestamp=time.time())
    
    def search_skills(self, query: str, strict: bool = False) -> List[Dict]:
        """Search for skills matching a query.
        
        Args:
            query: Search query string.
            strict: If True, raise error when CLI not available.
            
        Returns:
            List of skill dictionaries matching the query.
            
        Raises:
            MSClientNotAvailableError: If strict=True and CLI not available.
            MSClientTimeoutError: If the CLI operation times out.
            MSClientParseError: If the CLI output cannot be parsed.
        """
        normalized_query = query.strip().lower()
        key = ("search", normalized_query)
        
        # Check cache
        cached = self._get_cached(key)
        if cached is not None:
            logger.debug(f"Returning cached search results for: {query}")
            return cached
        
        # Check availability
        if not self.available():
            if strict:
                raise MSClientNotAvailableError(
                    f"ms CLI not available at: {self.config.ms_path}"
                )
            logger.debug("ms client not available; returning empty skill list")
            return []
        
        # Execute CLI
        try:
            logger.debug(f"Executing: {self.config.ms_path} search {query} --json")
            result = subprocess.run(
                [self.config.ms_path, "search", query, "--json"],
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
            )
            
            if result.returncode != 0:
                logger.warning(
                    f"ms search returned code {result.returncode}: {result.stderr[:200]}"
                )
                return []
            
            # Parse output
            try:
                parsed = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise MSClientParseError(
                    f"Failed to parse ms search output: {e}"
                ) from e
            
            # Extract skills list
            skills = parsed if isinstance(parsed, list) else parsed.get("skills", [])
            if not isinstance(skills, list):
                logger.warning("ms search returned non-list skills, using empty list")
                skills = []
            
            # Cache and return
            self._set_cached(key, skills)
            logger.debug(f"Found {len(skills)} skills for query: {query}")
            return skills
            
        except subprocess.TimeoutExpired as e:
            raise MSClientTimeoutError(
                f"ms search timed out after {self.config.timeout}s"
            ) from e
        except MSClientError:
            raise
        except Exception as e:
            logger.error(f"ms search failed: {e}")
            return []
    
    def fetch_skill(self, skill_id: str, strict: bool = False) -> Dict:
        """Fetch a specific skill by ID.
        
        Args:
            skill_id: The skill identifier.
            strict: If True, raise error when CLI not available.
            
        Returns:
            Skill dictionary, or empty dict if not found.
            
        Raises:
            MSClientNotAvailableError: If strict=True and CLI not available.
            MSClientTimeoutError: If the CLI operation times out.
            MSClientParseError: If the CLI output cannot be parsed.
        """
        normalized_id = skill_id.strip().lower()
        key = ("get", normalized_id)
        
        # Check cache
        cached = self._get_cached(key)
        if cached is not None:
            logger.debug(f"Returning cached skill: {skill_id}")
            return cached
        
        # Check availability
        if not self.available():
            if strict:
                raise MSClientNotAvailableError(
                    f"ms CLI not available at: {self.config.ms_path}"
                )
            logger.debug("ms client not available; returning empty skill dict")
            return {}
        
        # Execute CLI
        try:
            logger.debug(f"Executing: {self.config.ms_path} get {skill_id} --json")
            result = subprocess.run(
                [self.config.ms_path, "get", skill_id, "--json"],
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
            )
            
            if result.returncode != 0:
                logger.warning(
                    f"ms get returned code {result.returncode}: {result.stderr[:200]}"
                )
                return {}
            
            # Parse output
            try:
                parsed = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise MSClientParseError(
                    f"Failed to parse ms get output: {e}"
                ) from e
            
            if not isinstance(parsed, dict):
                logger.warning("ms get returned non-dict, using empty dict")
                parsed = {}
            
            # Cache and return
            self._set_cached(key, parsed)
            logger.debug(f"Fetched skill: {skill_id}")
            return parsed
            
        except subprocess.TimeoutExpired as e:
            raise MSClientTimeoutError(
                f"ms get timed out after {self.config.timeout}s"
            ) from e
        except MSClientError:
            raise
        except Exception as e:
            logger.error(f"ms get failed: {e}")
            return {}
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.debug("MS client cache cleared")


# Default instance for convenience
ms_client = MSClient()
