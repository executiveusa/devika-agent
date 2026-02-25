"""Testing quality helper for coverage-based gating.

Integrates with real testing tools:
- pytest: Python testing framework
- pytest-cov: Coverage plugin for pytest
- coverage.py: Coverage collection
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
from typing import Any, Dict, List, Optional

from . import QualityCategory, QualityIssue, QualityScore, SeverityLevel

logger = logging.getLogger("synthia.quality.testing")


class TestToolStatus(Enum):
    """Status of testing tools"""
    __test__ = False
    AVAILABLE = "available"
    NOT_INSTALLED = "not_installed"
    ERROR = "error"


@dataclass
class CoverageResult:
    """Result from coverage analysis"""
    tool: str
    status: TestToolStatus
    exit_code: int
    coverage_percent: float = 0.0
    covered_lines: int = 0
    total_lines: int = 0
    missing_files: List[str] = field(default_factory=list)
    by_module: Dict[str, float] = field(default_factory=dict)
    raw_output: str = ""
    error: Optional[str] = None
    elapsed_seconds: float = 0.0


@dataclass
class TestRunResult:
    """Result from test execution"""
    __test__ = False
    tool: str
    status: TestToolStatus
    exit_code: int
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    raw_output: str = ""
    error: Optional[str] = None
    elapsed_seconds: float = 0.0


@dataclass
class TestGeneratorHealthCheck:
    """Health check result for test generator"""
    __test__ = False
    pytest_available: bool
    coverage_available: bool
    last_run: Optional[str]
    last_coverage: Optional[float]
    status: str  # "ready", "partial", "unavailable"


class TestGenerator:
    """Production test generator with real pytest-cov integration.

    Provides:
    - Real coverage measurement via pytest-cov
    - Test execution and result parsing
    - Coverage threshold validation
    - Module-level coverage breakdown
    """

    __test__ = False

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize test generator with optional configuration.

        Args:
            config: Optional configuration dict with keys:
                - min_coverage: Minimum coverage threshold (default: 80.0)
                - pytest_args: Additional pytest arguments
                - coverage_rc: Path to .coveragerc file
                - timeout: Timeout in seconds (default: 600)
                - fail_under: Fail if coverage below threshold
        """
        self.config = config or {}
        self._pytest_path: Optional[str] = None
        self._coverage_path: Optional[str] = None
        self._last_run_time: Optional[datetime] = None
        self._last_coverage: Optional[float] = None
        self._last_result: Optional[CoverageResult] = None
        self._discover_tools()

    def _discover_tools(self) -> None:
        """Discover available testing tools on the system."""
        self._pytest_path = shutil.which("pytest")
        self._coverage_path = shutil.which("coverage")

        if self._pytest_path:
            logger.debug(f"Found pytest at {self._pytest_path}")
        else:
            logger.debug("pytest not found in PATH")

        if self._coverage_path:
            logger.debug(f"Found coverage at {self._coverage_path}")

    def is_pytest_available(self) -> bool:
        """Check if pytest is available."""
        return self._pytest_path is not None

    def is_coverage_available(self) -> bool:
        """Check if coverage is available."""
        return self._coverage_path is not None

    def health_check(self) -> TestGeneratorHealthCheck:
        """Perform health check on test generator.

        Returns:
            TestGeneratorHealthCheck with tool availability status
        """
        pytest_ok = self.is_pytest_available()
        coverage_ok = self.is_coverage_available()

        if pytest_ok and coverage_ok:
            status = "ready"
        elif pytest_ok or coverage_ok:
            status = "partial"
        else:
            status = "unavailable"

        return TestGeneratorHealthCheck(
            pytest_available=pytest_ok,
            coverage_available=coverage_ok,
            last_run=self._last_run_time.isoformat() if self._last_run_time else None,
            last_coverage=self._last_coverage,
            status=status
        )

    def _run_pytest_with_coverage(self, target: str) -> CoverageResult:
        """Run pytest with coverage measurement.

        Args:
            target: Path to project directory

        Returns:
            CoverageResult with coverage data
        """
        if not self._pytest_path:
            return CoverageResult(
                tool="pytest-cov",
                status=TestToolStatus.NOT_INSTALLED,
                exit_code=-1,
                error="pytest not found in PATH"
            )

        target_path = Path(target)
        timeout = self.config.get("timeout", 600)
        min_coverage = self.config.get("min_coverage", 80.0)

        # Build pytest command with coverage
        cmd = [
            self._pytest_path,
            "--cov=.",
            "--cov-report=json:coverage.json",
            "--cov-report=term-missing",
            f"--cov-fail-under={min_coverage}",
            "-v",
        ]

        # Add additional pytest args from config
        extra_args = self.config.get("pytest_args", [])
        cmd.extend(extra_args)

        # Add coverage config if specified
        coverage_rc = self.config.get("coverage_rc")
        if coverage_rc:
            os.environ["COVERAGE_FILE"] = coverage_rc

        start_time = datetime.now()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(target_path)
            )
            elapsed = (datetime.now() - start_time).total_seconds()

            # Parse coverage.json output
            coverage_file = target_path / "coverage.json"
            coverage_data = {}
            if coverage_file.exists():
                try:
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to parse coverage.json: {e}")

            # Extract coverage metrics
            totals = coverage_data.get("totals", {})
            coverage_percent = totals.get("percent_covered", 0.0)
            covered_lines = totals.get("covered_lines", 0)
            total_lines = totals.get("num_statements", 0)

            # Get per-module coverage
            by_module = {}
            files = coverage_data.get("files", {})
            for file_path, file_data in files.items():
                summary = file_data.get("summary", {})
                by_module[file_path] = summary.get("percent_covered", 0.0)

            # Find files with missing coverage
            missing_files = [
                f for f, cov in by_module.items()
                if cov < 100.0
            ]

            return CoverageResult(
                tool="pytest-cov",
                status=TestToolStatus.AVAILABLE,
                exit_code=result.returncode,
                coverage_percent=float(coverage_percent),
                covered_lines=covered_lines,
                total_lines=total_lines,
                missing_files=missing_files,
                by_module=by_module,
                raw_output=result.stdout + result.stderr,
                elapsed_seconds=elapsed
            )

        except subprocess.TimeoutExpired:
            return CoverageResult(
                tool="pytest-cov",
                status=TestToolStatus.ERROR,
                exit_code=-1,
                error=f"pytest timed out after {timeout} seconds"
            )
        except Exception as e:
            return CoverageResult(
                tool="pytest-cov",
                status=TestToolStatus.ERROR,
                exit_code=-1,
                error=str(e)
            )

    def _run_coverage_report(self, target: str) -> CoverageResult:
        """Run coverage report directly (without pytest).

        Args:
            target: Path to project directory

        Returns:
            CoverageResult with coverage data
        """
        if not self._coverage_path:
            return CoverageResult(
                tool="coverage",
                status=TestToolStatus.NOT_INSTALLED,
                exit_code=-1,
                error="coverage not found in PATH"
            )

        target_path = Path(target)
        timeout = self.config.get("timeout", 300)
        start_time = datetime.now()

        try:
            # Run coverage report
            result = subprocess.run(
                [self._coverage_path, "report", "--format=json"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(target_path)
            )
            elapsed = (datetime.now() - start_time).total_seconds()

            # Parse JSON output
            coverage_data = {}
            if result.stdout:
                try:
                    coverage_data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Fallback to parsing text output
                    pass

            totals = coverage_data.get("totals", {})
            coverage_percent = totals.get("percent_covered", 0.0)

            # If JSON parsing failed, try text parsing
            if coverage_percent == 0.0 and result.stdout:
                for line in result.stdout.split("\n"):
                    if "TOTAL" in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                coverage_percent = float(parts[-1].rstrip("%"))
                            except ValueError:
                                pass

            return CoverageResult(
                tool="coverage",
                status=TestToolStatus.AVAILABLE,
                exit_code=result.returncode,
                coverage_percent=coverage_percent,
                raw_output=result.stdout,
                elapsed_seconds=elapsed
            )

        except subprocess.TimeoutExpired:
            return CoverageResult(
                tool="coverage",
                status=TestToolStatus.ERROR,
                exit_code=-1,
                error=f"coverage timed out after {timeout} seconds"
            )
        except Exception as e:
            return CoverageResult(
                tool="coverage",
                status=TestToolStatus.ERROR,
                exit_code=-1,
                error=str(e)
            )

    def run_tests(self, target: str) -> TestRunResult:
        """Run tests and return results.

        Args:
            target: Path to project directory

        Returns:
            TestRunResult with test execution data
        """
        if not self._pytest_path:
            return TestRunResult(
                tool="pytest",
                status=TestToolStatus.NOT_INSTALLED,
                exit_code=-1,
                error="pytest not found in PATH"
            )

        target_path = Path(target)
        timeout = self.config.get("timeout", 600)
        start_time = datetime.now()

        cmd = [self._pytest_path, "-v", "--tb=short"]

        # Add additional pytest args
        extra_args = self.config.get("pytest_args", [])
        cmd.extend(extra_args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(target_path)
            )
            elapsed = (datetime.now() - start_time).total_seconds()

            # Parse test results from output
            tests_run = 0
            tests_passed = 0
            tests_failed = 0
            tests_skipped = 0
            errors = []

            output = result.stdout + result.stderr

            # Parse pytest summary line
            for line in output.split("\n"):
                if "passed" in line or "failed" in line or "skipped" in line:
                    # Example: "5 passed, 2 failed, 1 skipped"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed" and i > 0:
                            tests_passed = int(parts[i - 1])
                        elif part == "failed" and i > 0:
                            tests_failed = int(parts[i - 1])
                        elif part == "skipped" and i > 0:
                            tests_skipped = int(parts[i - 1])

            tests_run = tests_passed + tests_failed + tests_skipped

            # Extract error messages
            if tests_failed > 0:
                in_failure = False
                for line in output.split("\n"):
                    if "FAILED" in line:
                        in_failure = True
                        errors.append(line)
                    elif in_failure and line.strip():
                        errors.append(line)

            return TestRunResult(
                tool="pytest",
                status=TestToolStatus.AVAILABLE,
                exit_code=result.returncode,
                tests_run=tests_run,
                tests_passed=tests_passed,
                tests_failed=tests_failed,
                tests_skipped=tests_skipped,
                errors=errors[:10],  # Limit error messages
                raw_output=output,
                elapsed_seconds=elapsed
            )

        except subprocess.TimeoutExpired:
            return TestRunResult(
                tool="pytest",
                status=TestToolStatus.ERROR,
                exit_code=-1,
                error=f"pytest timed out after {timeout} seconds"
            )
        except Exception as e:
            return TestRunResult(
                tool="pytest",
                status=TestToolStatus.ERROR,
                exit_code=-1,
                error=str(e)
            )

    def check_coverage(self, target: str, context: Dict[str, Any] | None = None) -> QualityScore:
        """Check test coverage against threshold.

        This method runs pytest with coverage and validates against
        the minimum threshold. Falls back to context-based coverage
        if tools are unavailable.

        Args:
            target: Path to project directory
            context: Optional context with pre-computed coverage data

        Returns:
            QualityScore with coverage validation results
        """
        context = context or {}
        issues = []

        # Try pytest-cov first
        if self.is_pytest_available():
            result = self._run_pytest_with_coverage(target)
            self._last_result = result

            if result.status == TestToolStatus.AVAILABLE:
                coverage = result.coverage_percent
                self._last_coverage = coverage
                self._last_run_time = datetime.now()

                minimum = float(context.get("test_coverage_min", self.config.get("min_coverage", 80.0)))
                passed = coverage >= minimum

                if not passed:
                    issues.append(
                        QualityIssue(
                            category=QualityCategory.TESTING,
                            severity=SeverityLevel.HIGH,
                            title="Test coverage below threshold",
                            description=f"Coverage {coverage:.2f}% is below required {minimum:.2f}%",
                            suggestion="Increase unit/integration test coverage before release",
                        )
                    )

                # Add issues for files with low coverage
                for file_path, file_cov in result.by_module.items():
                    if file_cov < 50.0:
                        issues.append(
                            QualityIssue(
                                category=QualityCategory.TESTING,
                                severity=SeverityLevel.MEDIUM,
                                title=f"Low coverage in {file_path}",
                                description=f"File has only {file_cov:.1f}% coverage",
                                element=file_path,
                                suggestion="Add tests to improve coverage for this file",
                            )
                        )

                return QualityScore(
                    category=QualityCategory.TESTING,
                    score=max(0.0, min(100.0, coverage)),
                    passed=passed,
                    issues=issues,
                    details={
                        "coverage": coverage,
                        "minimum": minimum,
                        "target": target,
                        "covered_lines": result.covered_lines,
                        "total_lines": result.total_lines,
                        "by_module": result.by_module,
                        "missing_files": result.missing_files,
                        "tool": "pytest-cov",
                        "elapsed_seconds": result.elapsed_seconds,
                    }
                )

        # Fallback to coverage report
        if self.is_coverage_available():
            result = self._run_coverage_report(target)

            if result.status == TestToolStatus.AVAILABLE:
                coverage = result.coverage_percent
                self._last_coverage = coverage
                self._last_run_time = datetime.now()

                minimum = float(context.get("test_coverage_min", self.config.get("min_coverage", 80.0)))
                passed = coverage >= minimum

                if not passed:
                    issues.append(
                        QualityIssue(
                            category=QualityCategory.TESTING,
                            severity=SeverityLevel.HIGH,
                            title="Test coverage below threshold",
                            description=f"Coverage {coverage:.2f}% is below required {minimum:.2f}%",
                            suggestion="Increase unit/integration test coverage before release",
                        )
                    )

                return QualityScore(
                    category=QualityCategory.TESTING,
                    score=max(0.0, min(100.0, coverage)),
                    passed=passed,
                    issues=issues,
                    details={
                        "coverage": coverage,
                        "minimum": minimum,
                        "target": target,
                        "tool": "coverage",
                        "elapsed_seconds": result.elapsed_seconds,
                    }
                )

        # Fallback to context-based coverage
        logger.warning("No testing tools available, using context-based coverage")
        coverage = float(context.get("test_coverage", 0.0))
        minimum = float(context.get("test_coverage_min", self.config.get("min_coverage", 80.0)))

        passed = coverage >= minimum
        if not passed:
            issues.append(
                QualityIssue(
                    category=QualityCategory.TESTING,
                    severity=SeverityLevel.HIGH,
                    title="Test coverage below threshold",
                    description=f"Coverage {coverage:.2f}% is below required {minimum:.2f}%",
                    suggestion="Increase unit/integration test coverage before release",
                )
            )

        return QualityScore(
            category=QualityCategory.TESTING,
            score=max(0.0, min(100.0, coverage)),
            passed=passed,
            issues=issues,
            details={
                "coverage": coverage,
                "minimum": minimum,
                "target": target,
                "tool": "context",
            }
        )

    def get_last_result(self) -> Optional[CoverageResult]:
        """Get the last coverage result.

        Returns:
            CoverageResult from last run or None
        """
        return self._last_result
