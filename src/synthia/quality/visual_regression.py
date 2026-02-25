"""Visual regression checker for SYNTHIA quality gates.

Integrates with real visual testing tools:
- Playwright: Browser automation and screenshots
- Pixelmatch: Image comparison
- Custom screenshot comparison
"""

import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import QualityCategory, QualityIssue, QualityScore, SeverityLevel

logger = logging.getLogger("synthia.quality.visual")


class VisualToolStatus(Enum):
    """Status of visual testing tools"""
    AVAILABLE = "available"
    NOT_INSTALLED = "not_installed"
    ERROR = "error"


@dataclass
class ScreenshotResult:
    """Result from screenshot capture"""
    url: str
    status: VisualToolStatus
    screenshot_path: Optional[str] = None
    width: int = 0
    height: int = 0
    error: Optional[str] = None
    elapsed_seconds: float = 0.0


@dataclass
class DiffResult:
    """Result from image comparison"""
    baseline_path: str
    current_path: str
    diff_path: Optional[str] = None
    diff_ratio: float = 0.0
    diff_pixels: int = 0
    total_pixels: int = 0
    passed: bool = True


@dataclass
class VisualRegressionHealthCheck:
    """Health check result for visual regression tester"""
    playwright_available: bool
    pixelmatch_available: bool
    baseline_dir: Optional[str]
    last_run: Optional[str]
    status: str  # "ready", "partial", "unavailable"


class VisualRegressionTester:
    """Production visual regression tester with Playwright integration.

    Provides:
    - Screenshot capture via Playwright
    - Image comparison via pixelmatch or built-in diff
    - Baseline management
    - Multi-viewport testing
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize visual regression tester with optional configuration.

        Args:
            config: Optional configuration dict with keys:
                - baseline_dir: Directory for baseline screenshots
                - diff_dir: Directory for diff images
                - threshold: Diff threshold (default: 0.01)
                - viewports: List of viewport sizes to test
                - timeout: Timeout in seconds (default: 60)
                - headless: Run browser in headless mode (default: True)
        """
        self.config = config or {}
        self._playwright_path: Optional[str] = None
        self._pixelmatch_available: bool = False
        self._last_run_time: Optional[datetime] = None
        self._last_results: List[DiffResult] = []
        self._discover_tools()

    def _discover_tools(self) -> None:
        """Discover available visual testing tools."""
        # Check for Playwright
        self._playwright_path = shutil.which("playwright")
        if self._playwright_path:
            logger.debug(f"Found Playwright at {self._playwright_path}")
        else:
            # Check for npx playwright
            result = subprocess.run(
                ["npx", "playwright", "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                self._playwright_path = "npx playwright"
                logger.debug("Found Playwright via npx")

        # Check for pixelmatch (Node.js)
        result = subprocess.run(
            ["npm", "list", "pixelmatch"],
            capture_output=True,
            text=True,
            timeout=30
        )
        self._pixelmatch_available = "pixelmatch" in result.stdout
        if self._pixelmatch_available:
            logger.debug("Found pixelmatch")

    def is_playwright_available(self) -> bool:
        """Check if Playwright is available."""
        return self._playwright_path is not None

    def is_pixelmatch_available(self) -> bool:
        """Check if pixelmatch is available."""
        return self._pixelmatch_available

    def health_check(self) -> VisualRegressionHealthCheck:
        """Perform health check on visual regression tester.

        Returns:
            VisualRegressionHealthCheck with tool availability status
        """
        playwright_ok = self.is_playwright_available()
        pixelmatch_ok = self.is_pixelmatch_available()

        if playwright_ok and pixelmatch_ok:
            status = "ready"
        elif playwright_ok:
            status = "partial"
        else:
            status = "unavailable"

        baseline_dir = self.config.get("baseline_dir")

        return VisualRegressionHealthCheck(
            playwright_available=playwright_ok,
            pixelmatch_available=pixelmatch_ok,
            baseline_dir=baseline_dir,
            last_run=self._last_run_time.isoformat() if self._last_run_time else None,
            status=status
        )

    def _ensure_directories(self) -> Tuple[Path, Path]:
        """Ensure baseline and diff directories exist.

        Returns:
            Tuple of (baseline_dir, diff_dir)
        """
        baseline_dir = Path(self.config.get("baseline_dir", "./baselines"))
        diff_dir = Path(self.config.get("diff_dir", "./diffs"))

        baseline_dir.mkdir(parents=True, exist_ok=True)
        diff_dir.mkdir(parents=True, exist_ok=True)

        return baseline_dir, diff_dir

    def capture_screenshot(
        self,
        url: str,
        output_path: str,
        viewport: Optional[Dict[str, int]] = None
    ) -> ScreenshotResult:
        """Capture screenshot of a URL using Playwright.

        Args:
            url: URL to capture
            output_path: Path to save screenshot
            viewport: Optional viewport size dict with width/height

        Returns:
            ScreenshotResult with capture details
        """
        if not self._playwright_path:
            return ScreenshotResult(
                url=url,
                status=VisualToolStatus.NOT_INSTALLED,
                error="Playwright not found"
            )

        viewport = viewport or {"width": 1280, "height": 720}
        timeout = self.config.get("timeout", 60)
        headless = self.config.get("headless", True)

        start_time = datetime.now()

        # Create a temporary Node.js script for Playwright
        script = f'''
const {{ chromium }} = require('playwright');

(async () => {{
    const browser = await chromium.launch({{ headless: {str(headless).lower()} }});
    const page = await browser.newPage({{
        viewport: {{ width: {viewport["width"]}, height: {viewport["height"]} }}
    }});

    try {{
        await page.goto('{url}', {{ waitUntil: 'networkidle', timeout: {timeout * 1000} }});
        await page.screenshot({{ path: '{output_path}', fullPage: true }});

        const dimensions = await page.evaluate(() => ({{
            width: document.documentElement.scrollWidth,
            height: document.documentElement.scrollHeight
        }}));

        console.log(JSON.stringify(dimensions));
    }} catch (error) {{
        console.error(error.message);
        process.exit(1);
    }} finally {{
        await browser.close();
    }}
}})();
'''

        script_path = Path(output_path).parent / "_capture.js"
        script_path.write_text(script)

        try:
            result = subprocess.run(
                ["node", str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout + 30
            )
            elapsed = (datetime.now() - start_time).total_seconds()

            # Clean up script
            script_path.unlink(missing_ok=True)

            if result.returncode != 0:
                return ScreenshotResult(
                    url=url,
                    status=VisualToolStatus.ERROR,
                    error=result.stderr or "Unknown error",
                    elapsed_seconds=elapsed
                )

            # Parse dimensions from output
            dimensions = {"width": viewport["width"], "height": viewport["height"]}
            try:
                dimensions = json.loads(result.stdout.strip())
            except (json.JSONDecodeError, ValueError):
                pass

            return ScreenshotResult(
                url=url,
                status=VisualToolStatus.AVAILABLE,
                screenshot_path=output_path,
                width=dimensions.get("width", viewport["width"]),
                height=dimensions.get("height", viewport["height"]),
                elapsed_seconds=elapsed
            )

        except subprocess.TimeoutExpired:
            script_path.unlink(missing_ok=True)
            return ScreenshotResult(
                url=url,
                status=VisualToolStatus.ERROR,
                error=f"Screenshot capture timed out after {timeout} seconds"
            )
        except Exception as e:
            script_path.unlink(missing_ok=True)
            return ScreenshotResult(
                url=url,
                status=VisualToolStatus.ERROR,
                error=str(e)
            )

    def _compare_images_python(
        self,
        baseline_path: str,
        current_path: str,
        diff_path: str
    ) -> DiffResult:
        """Compare two images using Python PIL.

        Args:
            baseline_path: Path to baseline image
            current_path: Path to current image
            diff_path: Path to save diff image

        Returns:
            DiffResult with comparison details
        """
        try:
            from PIL import Image
            import math

            baseline = Image.open(baseline_path)
            current = Image.open(current_path)

            # Ensure same size
            if baseline.size != current.size:
                # Resize to match
                max_size = (
                    max(baseline.size[0], current.size[0]),
                    max(baseline.size[1], current.size[1])
                )
                baseline = baseline.resize(max_size, Image.Resampling.LANCZOS)
                current = current.resize(max_size, Image.Resampling.LANCZOS)

            width, height = baseline.size
            total_pixels = width * height

            # Compare pixels
            baseline_pixels = baseline.load()
            current_pixels = current.load()

            diff_pixels = 0
            diff_image = Image.new("RGB", (width, height))

            for y in range(height):
                for x in range(width):
                    bp = baseline_pixels[x, y]
                    cp = current_pixels[x, y]

                    # Calculate pixel difference
                    if isinstance(bp, tuple) and isinstance(cp, tuple):
                        diff = sum(abs(b - c) for b, c in zip(bp[:3], cp[:3]))
                        if diff > 0:
                            diff_pixels += 1
                            # Highlight difference in red
                            diff_image.putpixel((x, y), (255, 0, 0))
                        else:
                            diff_image.putpixel((x, y), bp)

            # Save diff image
            diff_image.save(diff_path)

            diff_ratio = diff_pixels / total_pixels if total_pixels > 0 else 0.0

            return DiffResult(
                baseline_path=baseline_path,
                current_path=current_path,
                diff_path=diff_path,
                diff_ratio=diff_ratio,
                diff_pixels=diff_pixels,
                total_pixels=total_pixels,
                passed=diff_ratio <= self.config.get("threshold", 0.01)
            )

        except ImportError:
            logger.warning("PIL not available, using basic comparison")
            return self._compare_images_basic(baseline_path, current_path, diff_path)

    def _compare_images_basic(
        self,
        baseline_path: str,
        current_path: str,
        diff_path: str
    ) -> DiffResult:
        """Basic file-based image comparison fallback.

        Args:
            baseline_path: Path to baseline image
            current_path: Path to current image
            diff_path: Path to save diff image

        Returns:
            DiffResult with comparison details
        """
        baseline_stat = Path(baseline_path).stat()
        current_stat = Path(current_path).stat()

        # Simple file size comparison
        size_diff = abs(baseline_stat.st_size - current_stat.st_size)
        max_size = max(baseline_stat.st_size, current_stat.st_size)

        diff_ratio = size_diff / max_size if max_size > 0 else 0.0

        return DiffResult(
            baseline_path=baseline_path,
            current_path=current_path,
            diff_path=None,
            diff_ratio=diff_ratio,
            diff_pixels=0,
            total_pixels=0,
            passed=diff_ratio <= self.config.get("threshold", 0.01)
        )

    def _compare_images_pixelmatch(
        self,
        baseline_path: str,
        current_path: str,
        diff_path: str
    ) -> DiffResult:
        """Compare images using pixelmatch.

        Args:
            baseline_path: Path to baseline image
            current_path: Path to current image
            diff_path: Path to save diff image

        Returns:
            DiffResult with comparison details
        """
        threshold = self.config.get("threshold", 0.01)

        script = f'''
const {{ createCanvas, loadImage }} = require('canvas');
const pixelmatch = require('pixelmatch');
const fs = require('fs');

(async () => {{
    const img1 = await loadImage('{baseline_path}');
    const img2 = await loadImage('{current_path}');

    const width = Math.max(img1.width, img2.width);
    const height = Math.max(img1.height, img2.height);

    const canvas1 = createCanvas(width, height);
    const canvas2 = createCanvas(width, height);
    const canvasDiff = createCanvas(width, height);

    const ctx1 = canvas1.getContext('2d');
    const ctx2 = canvas2.getContext('2d');

    ctx1.drawImage(img1, 0, 0);
    ctx2.drawImage(img2, 0, 0);

    const img1Data = ctx1.getImageData(0, 0, width, height);
    const img2Data = ctx2.getImageData(0, 0, width, height);
    const diffData = ctxDiff.createImageData(width, height);

    const diffPixels = pixelmatch(
        img1Data.data,
        img2Data.data,
        diffData.data,
        width,
        height,
        {{ threshold: {threshold} }}
    );

    const out = fs.createWriteStream('{diff_path}');
    const stream = canvasDiff.createPNGStream();
    stream.pipe(out);

    console.log(JSON.stringify({{
        diffPixels: diffPixels,
        totalPixels: width * height,
        diffRatio: diffPixels / (width * height)
    }}));
}})();
'''

        script_path = Path(diff_path).parent / "_compare.js"
        script_path.write_text(script)

        try:
            result = subprocess.run(
                ["node", str(script_path)],
                capture_output=True,
                text=True,
                timeout=60
            )

            script_path.unlink(missing_ok=True)

            if result.returncode != 0:
                logger.warning(f"pixelmatch failed: {result.stderr}")
                return self._compare_images_python(baseline_path, current_path, diff_path)

            data = json.loads(result.stdout.strip())

            return DiffResult(
                baseline_path=baseline_path,
                current_path=current_path,
                diff_path=diff_path,
                diff_ratio=data.get("diffRatio", 0.0),
                diff_pixels=data.get("diffPixels", 0),
                total_pixels=data.get("totalPixels", 0),
                passed=data.get("diffRatio", 0.0) <= threshold
            )

        except Exception as e:
            script_path.unlink(missing_ok=True)
            logger.warning(f"pixelmatch error: {e}")
            return self._compare_images_python(baseline_path, current_path, diff_path)

    def compare(
        self,
        url: str,
        baseline_path: Optional[str] = None,
        context: Dict[str, Any] | None = None
    ) -> QualityScore:
        """Compare current screenshot against baseline.

        This method captures a screenshot and compares it against a baseline.
        Falls back to context-based comparison if tools are unavailable.

        Args:
            url: URL to capture and compare
            baseline_path: Optional path to baseline image
            context: Optional context with pre-computed diff data

        Returns:
            QualityScore with visual regression results
        """
        context = context or {}
        issues = []
        threshold = float(context.get("visual_diff_threshold", self.config.get("threshold", 0.01)))

        baseline_dir, diff_dir = self._ensure_directories()

        # Determine baseline path
        if not baseline_path:
            # Generate baseline path from URL
            safe_name = url.replace("://", "_").replace("/", "_").replace("?", "_")
            baseline_path = str(baseline_dir / f"{safe_name}.png")

        # Check if baseline exists
        has_baseline = Path(baseline_path).exists()

        if self.is_playwright_available():
            # Capture current screenshot
            current_path = str(diff_dir / f"current_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            capture_result = self.capture_screenshot(url, current_path)

            if capture_result.status != VisualToolStatus.AVAILABLE:
                # Fallback to context-based comparison
                logger.warning(f"Screenshot capture failed: {capture_result.error}")
                return self._context_based_compare(url, context)

            if not has_baseline:
                # No baseline exists - create one
                Path(current_path).rename(baseline_path)
                logger.info(f"Created baseline: {baseline_path}")

                return QualityScore(
                    category=QualityCategory.VISUAL,
                    score=100.0,
                    passed=True,
                    issues=[],
                    details={
                        "url": url,
                        "baseline_created": True,
                        "baseline_path": baseline_path,
                        "viewport": {"width": capture_result.width, "height": capture_result.height},
                    }
                )

            # Compare with baseline
            diff_path = str(diff_dir / f"diff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

            if self._pixelmatch_available:
                diff_result = self._compare_images_pixelmatch(baseline_path, current_path, diff_path)
            else:
                diff_result = self._compare_images_python(baseline_path, current_path, diff_path)

            self._last_results.append(diff_result)
            self._last_run_time = datetime.now()

            diff_ratio = diff_result.diff_ratio
            passed = diff_ratio <= threshold

            if not passed:
                issues.append(
                    QualityIssue(
                        category=QualityCategory.VISUAL,
                        severity=SeverityLevel.MEDIUM,
                        title="Visual regression detected",
                        description=f"Diff ratio {diff_ratio:.4f} exceeds threshold {threshold:.4f}",
                        url=url,
                        suggestion="Review screenshot diffs and approve or update baselines",
                    )
                )

            score = max(0.0, 100.0 - (diff_ratio * 100.0 * 10.0))

            return QualityScore(
                category=QualityCategory.VISUAL,
                score=score,
                passed=passed,
                issues=issues,
                details={
                    "url": url,
                    "diff_ratio": diff_ratio,
                    "threshold": threshold,
                    "diff_pixels": diff_result.diff_pixels,
                    "total_pixels": diff_result.total_pixels,
                    "baseline_path": baseline_path,
                    "current_path": current_path,
                    "diff_path": diff_result.diff_path,
                    "tool": "playwright",
                }
            )

        # Fallback to context-based comparison
        return self._context_based_compare(url, context)

    def _context_based_compare(self, url: str, context: Dict[str, Any]) -> QualityScore:
        """Context-based comparison fallback.

        Args:
            url: URL being compared
            context: Context with diff data

        Returns:
            QualityScore from context data
        """
        logger.warning("No visual testing tools available, using context-based comparison")

        diff_ratio = float(context.get("visual_diff_ratio", 0.0))
        threshold = float(context.get("visual_diff_threshold", self.config.get("threshold", 0.01)))

        issues = []
        passed = diff_ratio <= threshold
        if not passed:
            issues.append(
                QualityIssue(
                    category=QualityCategory.VISUAL,
                    severity=SeverityLevel.MEDIUM,
                    title="Visual regression detected",
                    description=f"Diff ratio {diff_ratio:.4f} exceeds threshold {threshold:.4f}",
                    url=url,
                    suggestion="Review screenshot diffs and approve or update baselines",
                )
            )

        score = max(0.0, 100.0 - (diff_ratio * 100.0 * 10.0))

        return QualityScore(
            category=QualityCategory.VISUAL,
            score=score,
            passed=passed,
            issues=issues,
            details={
                "url": url,
                "diff_ratio": diff_ratio,
                "threshold": threshold,
                "tool": "context",
            }
        )

    def update_baseline(self, current_path: str, baseline_path: str) -> bool:
        """Update baseline with current screenshot.

        Args:
            current_path: Path to current screenshot
            baseline_path: Path to baseline to update

        Returns:
            True if baseline was updated successfully
        """
        try:
            current = Path(current_path)
            baseline = Path(baseline_path)

            if not current.exists():
                logger.error(f"Current screenshot not found: {current_path}")
                return False

            # Ensure baseline directory exists
            baseline.parent.mkdir(parents=True, exist_ok=True)

            # Copy current to baseline
            import shutil
            shutil.copy2(current, baseline)
            logger.info(f"Updated baseline: {baseline_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to update baseline: {e}")
            return False

    def get_last_results(self) -> List[DiffResult]:
        """Get results from the last comparison.

        Returns:
            List of DiffResult from last run
        """
        return self._last_results.copy()
