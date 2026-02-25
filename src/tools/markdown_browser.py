"""Wrapper for markdown_web_browser (mdwb) tool.

This is a lightweight wrapper that calls a local CLI/API for deterministic
page capture. When mdwb is not available it returns a clear disabled status.
The researcher agent should treat outputs as untrusted and pass them through
ACIP/other sanitizers.

Environment Variables:
    MDWB_PATH: Path to the mdwb CLI binary (default: "mdwb")
    MDWB_TIMEOUT: Timeout for capture operations in seconds (default: 45)
    MDWB_DEFAULT_OUT_DIR: Default output directory (default: "./tmp_mdwb")
"""
import shutil
import subprocess
import os
import json
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MarkdownBrowserError(RuntimeError):
    """Base error for markdown browser operations."""


class MarkdownBrowserNotAvailableError(MarkdownBrowserError):
    """Raised when the mdwb CLI is not available and strict mode is enabled."""


class MarkdownBrowserTimeoutError(MarkdownBrowserError):
    """Raised when a capture operation times out."""


class MarkdownBrowserCaptureError(MarkdownBrowserError):
    """Raised when a capture operation fails."""


class CaptureStatus(Enum):
    """Status of a capture operation."""
    OK = "ok"
    DISABLED = "disabled"
    ERROR = "error"
    TIMEOUT = "timeout"


class BrowserStatus(Enum):
    """Status of the markdown browser."""
    AVAILABLE = "available"
    NOT_INSTALLED = "not_installed"
    ERROR = "error"


@dataclass
class MDWBConfig:
    """Configuration for the markdown browser."""
    mdwb_path: str = "mdwb"
    timeout: int = 45
    default_out_dir: str = "./tmp_mdwb"
    
    @classmethod
    def from_env(cls) -> "MDWBConfig":
        """Create configuration from environment variables."""
        return cls(
            mdwb_path=os.environ.get("MDWB_PATH", "mdwb"),
            timeout=int(os.environ.get("MDWB_TIMEOUT", "45")),
            default_out_dir=os.environ.get("MDWB_DEFAULT_OUT_DIR", "./tmp_mdwb"),
        )


@dataclass
class CaptureResult:
    """Result of a capture operation."""
    status: CaptureStatus
    out_md: Optional[str] = None
    manifest: Optional[str] = None
    error: Optional[str] = None
    url: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status.value,
            "out_md": self.out_md,
            "manifest": self.manifest,
            "error": self.error,
            "url": self.url,
            "elapsed_seconds": self.elapsed_seconds,
        }
    
    @property
    def success(self) -> bool:
        """Check if the capture was successful."""
        return self.status == CaptureStatus.OK


@dataclass
class BrowserHealthCheck:
    """Result of a browser health check."""
    status: BrowserStatus
    message: str
    version: Optional[str] = None
    path: Optional[str] = None


class MarkdownBrowser:
    """Client for the markdown_web_browser (mdwb) CLI tool.
    
    This browser captures web pages and converts them to markdown format.
    It requires the mdwb CLI to be installed and available on the PATH.
    
    Example:
        browser = MarkdownBrowser()
        if browser.available():
            result = browser.capture_url("https://example.com")
            if result.success:
                print(f"Captured to: {result.out_md}")
    """
    
    def __init__(self, config: Optional[MDWBConfig] = None):
        """Initialize the markdown browser.
        
        Args:
            config: Optional configuration. If not provided, uses env vars.
        """
        self.config = config or MDWBConfig.from_env()
        self._available: Optional[bool] = None
        
        # Log initialization state
        self._log_initialization_state()
    
    def _log_initialization_state(self) -> None:
        """Log the initialization state for debugging."""
        if self.available():
            logger.info(
                f"MarkdownBrowser initialized with CLI at: {self.config.mdwb_path} "
                f"(timeout: {self.config.timeout}s)"
            )
        else:
            logger.info(
                f"MarkdownBrowser initialized but CLI not found at: {self.config.mdwb_path}. "
                "URL capture will return disabled status."
            )
    
    def available(self) -> bool:
        """Check if the mdwb CLI is available.
        
        Returns:
            True if the CLI is installed and executable, False otherwise.
        """
        if self._available is None:
            self._available = shutil.which(self.config.mdwb_path) is not None
        return self._available
    
    def get_status(self) -> BrowserStatus:
        """Get the current status of the browser.
        
        Returns:
            BrowserStatus indicating availability state.
        """
        if self.available():
            return BrowserStatus.AVAILABLE
        return BrowserStatus.NOT_INSTALLED
    
    def health_check(self) -> BrowserHealthCheck:
        """Perform a health check on the markdown browser.
        
        Returns:
            BrowserHealthCheck with status and version information.
        """
        if not self.available():
            return BrowserHealthCheck(
                status=BrowserStatus.NOT_INSTALLED,
                message=f"mdwb CLI not found at path: {self.config.mdwb_path}"
            )
        
        try:
            result = subprocess.run(
                [self.config.mdwb_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            version = result.stdout.strip() or result.stderr.strip()
            return BrowserHealthCheck(
                status=BrowserStatus.AVAILABLE,
                message="mdwb CLI is available and working",
                version=version,
                path=shutil.which(self.config.mdwb_path),
            )
        except subprocess.TimeoutExpired:
            return BrowserHealthCheck(
                status=BrowserStatus.ERROR,
                message="mdwb CLI health check timed out"
            )
        except Exception as e:
            return BrowserHealthCheck(
                status=BrowserStatus.ERROR,
                message=f"mdwb CLI health check failed: {str(e)[:100]}"
            )
    
    def capture_url(
        self,
        url: str,
        out_dir: Optional[str] = None,
        strict: bool = False,
    ) -> CaptureResult:
        """Capture a URL and convert to markdown.
        
        Args:
            url: The URL to capture.
            out_dir: Output directory for captured files.
            strict: If True, raise error when CLI not available.
            
        Returns:
            CaptureResult with status and file paths.
            
        Raises:
            MarkdownBrowserNotAvailableError: If strict=True and CLI not available.
            MarkdownBrowserTimeoutError: If the capture times out.
            MarkdownBrowserCaptureError: If the capture fails.
        """
        start_time = time.time()
        output_dir = out_dir or self.config.default_out_dir
        
        # Validate URL
        if not url or not url.strip():
            return CaptureResult(
                status=CaptureStatus.ERROR,
                error="URL must not be empty",
                url=url,
            )
        
        # Check availability
        if not self.available():
            if strict:
                raise MarkdownBrowserNotAvailableError(
                    f"mdwb CLI not available at: {self.config.mdwb_path}"
                )
            logger.debug("mdwb CLI not found on PATH")
            return CaptureResult(
                status=CaptureStatus.DISABLED,
                error="mdwb CLI not found on PATH",
                url=url,
            )
        
        # Execute capture
        try:
            logger.debug(f"Capturing URL: {url}")
            result = subprocess.run(
                [self.config.mdwb_path, "capture", "--url", url, "--out", output_dir],
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() or f"Exit code: {result.returncode}"
                logger.warning(f"mdwb capture failed: {error_msg}")
                return CaptureResult(
                    status=CaptureStatus.ERROR,
                    error=error_msg,
                    url=url,
                    elapsed_seconds=elapsed,
                )
            
            # Verify output files
            out_md = os.path.join(output_dir, "out.md")
            manifest = os.path.join(output_dir, "manifest.json")
            
            if not os.path.exists(out_md):
                return CaptureResult(
                    status=CaptureStatus.ERROR,
                    error="mdwb output markdown not found",
                    out_md=out_md,
                    manifest=manifest,
                    url=url,
                    elapsed_seconds=elapsed,
                )
            
            logger.info(f"Successfully captured {url} to {out_md}")
            return CaptureResult(
                status=CaptureStatus.OK,
                out_md=out_md,
                manifest=manifest if os.path.exists(manifest) else None,
                url=url,
                elapsed_seconds=elapsed,
            )
            
        except subprocess.TimeoutExpired as e:
            elapsed = time.time() - start_time
            raise MarkdownBrowserTimeoutError(
                f"mdwb capture timed out after {self.config.timeout}s"
            ) from e
        except MarkdownBrowserError:
            raise
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"mdwb capture failed: {e}")
            return CaptureResult(
                status=CaptureStatus.ERROR,
                error=str(e),
                url=url,
                elapsed_seconds=elapsed,
            )
    
    def read_capture(self, result: CaptureResult) -> Optional[str]:
        """Read the captured markdown content.
        
        Args:
            result: A successful CaptureResult from capture_url.
            
        Returns:
            The markdown content, or None if not available.
        """
        if not result.success or not result.out_md:
            return None
        
        try:
            with open(result.out_md, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read capture file: {e}")
            return None
    
    def read_manifest(self, result: CaptureResult) -> Optional[Dict[str, Any]]:
        """Read the capture manifest.
        
        Args:
            result: A successful CaptureResult from capture_url.
            
        Returns:
            The manifest as a dictionary, or None if not available.
        """
        if not result.success or not result.manifest:
            return None
        
        try:
            with open(result.manifest, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read manifest file: {e}")
            return None


# Default instance for convenience
md_browser = MarkdownBrowser()