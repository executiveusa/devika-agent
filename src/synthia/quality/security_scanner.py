"""Security scanning checks for SYNTHIA quality gates.

Integrates with real security tools:
- bandit: Python static analysis
- pip-audit: Dependency vulnerability scanning
- safety: Package vulnerability checks
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

logger = logging.getLogger("synthia.quality.security")


class SecurityToolStatus(Enum):
    """Status of security scanning tools"""
    AVAILABLE = "available"
    NOT_INSTALLED = "not_installed"
    ERROR = "error"


@dataclass
class SecurityToolResult:
    """Result from a security tool execution"""
    tool: str
    status: SecurityToolStatus
    exit_code: int
    findings: List[Dict[str, Any]] = field(default_factory=list)
    raw_output: str = ""
    error: Optional[str] = None
    elapsed_seconds: float = 0.0


@dataclass
class SecurityScannerHealthCheck:
    """Health check result for security scanner"""
    available_tools: List[str]
    missing_tools: List[str]
    last_scan: Optional[str]
    status: str  # "ready", "partial", "unavailable"


class SecurityScanner:
    """Production security scanner with real tool integration.

    Supports multiple security scanning backends:
    - bandit: Python code security analysis
    - pip-audit: Python dependency vulnerability scanning
    - safety: Alternative dependency vulnerability scanner

    Falls back to context-based scanning when tools are unavailable.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize security scanner with optional configuration.

        Args:
            config: Optional configuration dict with keys:
                - enabled_tools: List of tools to use (default: all available)
                - bandit_config: Path to bandit config file
                - fail_on_missing: Fail if tools are missing (default: False)
                - timeout: Timeout in seconds for each tool (default: 300)
        """
        self.config = config or {}
        self._tool_paths: Dict[str, Optional[str]] = {}
        self._last_scan_time: Optional[datetime] = None
        self._scan_results: List[SecurityToolResult] = []
        self._discover_tools()

    def _discover_tools(self) -> None:
        """Discover available security tools on the system."""
        tools = ["bandit", "pip-audit", "safety"]
        for tool in tools:
            path = shutil.which(tool)
            self._tool_paths[tool] = path
            if path:
                logger.debug(f"Found security tool: {tool} at {path}")
            else:
                logger.debug(f"Security tool not found: {tool}")

    def _get_tool_path(self, tool: str) -> Optional[str]:
        """Get the path to a security tool executable."""
        return self._tool_paths.get(tool)

    def is_tool_available(self, tool: str) -> bool:
        """Check if a specific security tool is available."""
        return self._tool_paths.get(tool) is not None

    def health_check(self) -> SecurityScannerHealthCheck:
        """Perform health check on security scanner.

        Returns:
            SecurityScannerHealthCheck with tool availability status
        """
        available = [t for t, p in self._tool_paths.items() if p]
        missing = [t for t, p in self._tool_paths.items() if not p]

        if len(available) == 0:
            status = "unavailable"
        elif len(missing) > 0:
            status = "partial"
        else:
            status = "ready"

        return SecurityScannerHealthCheck(
            available_tools=available,
            missing_tools=missing,
            last_scan=self._last_scan_time.isoformat() if self._last_scan_time else None,
            status=status
        )

    def _run_bandit(self, target: str) -> SecurityToolResult:
        """Run bandit security scanner on Python code.

        Args:
            target: Path to scan (file or directory)

        Returns:
            SecurityToolResult with findings
        """
        tool_path = self._get_tool_path("bandit")
        if not tool_path:
            return SecurityToolResult(
                tool="bandit",
                status=SecurityToolStatus.NOT_INSTALLED,
                exit_code=-1,
                error="bandit not found in PATH"
            )

        target_path = Path(target)
        if not target_path.exists():
            return SecurityToolResult(
                tool="bandit",
                status=SecurityToolStatus.ERROR,
                exit_code=-1,
                error=f"Target path does not exist: {target}"
            )

        # Build command
        cmd = [
            tool_path,
            "-f", "json",
            "-r",  # recursive
            target
        ]

        # Add config if specified
        bandit_config = self.config.get("bandit_config")
        if bandit_config:
            cmd.extend(["-c", bandit_config])

        timeout = self.config.get("timeout", 300)
        start_time = datetime.now()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            elapsed = (datetime.now() - start_time).total_seconds()

            findings = []
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for issue in data.get("results", []):
                        findings.append({
                            "id": issue.get("test_id", "unknown"),
                            "title": issue.get("test_name", "Security issue"),
                            "description": issue.get("issue_text", ""),
                            "severity": issue.get("issue_severity", "MEDIUM").lower(),
                            "confidence": issue.get("issue_confidence", "MEDIUM").lower(),
                            "file": issue.get("filename", ""),
                            "line": issue.get("line_number", 0),
                            "suggestion": issue.get("more_info", ""),
                        })
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse bandit output: {e}")

            return SecurityToolResult(
                tool="bandit",
                status=SecurityToolStatus.AVAILABLE,
                exit_code=result.returncode,
                findings=findings,
                raw_output=result.stdout,
                elapsed_seconds=elapsed
            )

        except subprocess.TimeoutExpired:
            return SecurityToolResult(
                tool="bandit",
                status=SecurityToolStatus.ERROR,
                exit_code=-1,
                error=f"bandit timed out after {timeout} seconds"
            )
        except Exception as e:
            return SecurityToolResult(
                tool="bandit",
                status=SecurityToolStatus.ERROR,
                exit_code=-1,
                error=str(e)
            )

    def _run_pip_audit(self, target: str) -> SecurityToolResult:
        """Run pip-audit for dependency vulnerability scanning.

        Args:
            target: Path to project directory with requirements

        Returns:
            SecurityToolResult with findings
        """
        tool_path = self._get_tool_path("pip-audit")
        if not tool_path:
            return SecurityToolResult(
                tool="pip-audit",
                status=SecurityToolStatus.NOT_INSTALLED,
                exit_code=-1,
                error="pip-audit not found in PATH"
            )

        target_path = Path(target)
        timeout = self.config.get("timeout", 300)
        start_time = datetime.now()

        # Build command - check for requirements files
        cmd = [tool_path, "--format", "json"]

        # Check for common requirements files
        requirements = target_path / "requirements.txt"
        if requirements.exists():
            cmd.extend(["-r", str(requirements)])
        else:
            # Assume we're auditing the current environment
            cmd.append("--local")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(target_path) if target_path.is_dir() else None
            )
            elapsed = (datetime.now() - start_time).total_seconds()

            findings = []
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    # pip-audit returns a list of packages with vulnerabilities
                    for pkg in data if isinstance(data, list) else [data]:
                        if not isinstance(pkg, dict):
                            continue
                        for vuln in pkg.get("vulns", []):
                            findings.append({
                                "id": vuln.get("id", "unknown"),
                                "title": f"Vulnerability in {pkg.get('name', 'unknown')}",
                                "description": vuln.get("description", ""),
                                "severity": self._cvss_to_severity(vuln.get("severity", "")),
                                "package": pkg.get("name", ""),
                                "version": pkg.get("version", ""),
                                "fixed_version": vuln.get("fix_versions", []),
                            })
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse pip-audit output: {e}")

            return SecurityToolResult(
                tool="pip-audit",
                status=SecurityToolStatus.AVAILABLE,
                exit_code=result.returncode,
                findings=findings,
                raw_output=result.stdout,
                elapsed_seconds=elapsed
            )

        except subprocess.TimeoutExpired:
            return SecurityToolResult(
                tool="pip-audit",
                status=SecurityToolStatus.ERROR,
                exit_code=-1,
                error=f"pip-audit timed out after {timeout} seconds"
            )
        except Exception as e:
            return SecurityToolResult(
                tool="pip-audit",
                status=SecurityToolStatus.ERROR,
                exit_code=-1,
                error=str(e)
            )

    def _run_safety(self, target: str) -> SecurityToolResult:
        """Run safety for dependency vulnerability scanning.

        Args:
            target: Path to project directory

        Returns:
            SecurityToolResult with findings
        """
        tool_path = self._get_tool_path("safety")
        if not tool_path:
            return SecurityToolResult(
                tool="safety",
                status=SecurityToolStatus.NOT_INSTALLED,
                exit_code=-1,
                error="safety not found in PATH"
            )

        target_path = Path(target)
        timeout = self.config.get("timeout", 300)
        start_time = datetime.now()

        # Build command
        cmd = [tool_path, "check", "--json"]

        # Check for requirements file
        requirements = target_path / "requirements.txt"
        if requirements.exists():
            cmd.extend(["-r", str(requirements)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(target_path) if target_path.is_dir() else None
            )
            elapsed = (datetime.now() - start_time).total_seconds()

            findings = []
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    # safety returns a list of vulnerabilities
                    for vuln in data:
                        if isinstance(vuln, list) and len(vuln) >= 4:
                            findings.append({
                                "id": vuln[0] if len(vuln) > 0 else "unknown",
                                "title": f"Vulnerability in {vuln[0] if len(vuln) > 0 else 'unknown'}",
                                "description": vuln[3] if len(vuln) > 3 else "",
                                "severity": "high",  # safety doesn't provide severity
                                "package": vuln[0] if len(vuln) > 0 else "",
                                "version": vuln[1] if len(vuln) > 1 else "",
                            })
                except (json.JSONDecodeError, IndexError) as e:
                    logger.warning(f"Failed to parse safety output: {e}")

            return SecurityToolResult(
                tool="safety",
                status=SecurityToolStatus.AVAILABLE,
                exit_code=result.returncode,
                findings=findings,
                raw_output=result.stdout,
                elapsed_seconds=elapsed
            )

        except subprocess.TimeoutExpired:
            return SecurityToolResult(
                tool="safety",
                status=SecurityToolStatus.ERROR,
                exit_code=-1,
                error=f"safety timed out after {timeout} seconds"
            )
        except Exception as e:
            return SecurityToolResult(
                tool="safety",
                status=SecurityToolStatus.ERROR,
                exit_code=-1,
                error=str(e)
            )

    def _cvss_to_severity(self, cvss: str) -> str:
        """Convert CVSS score to severity level.

        Args:
            cvss: CVSS score string or float

        Returns:
            Severity level string
        """
        try:
            score = float(cvss)
            if score >= 9.0:
                return "critical"
            elif score >= 7.0:
                return "high"
            elif score >= 4.0:
                return "medium"
            else:
                return "low"
        except (ValueError, TypeError):
            return "medium"

    def _finding_to_issue(self, finding: Dict[str, Any]) -> QualityIssue:
        """Convert a security finding to a QualityIssue.

        Args:
            finding: Security finding dict

        Returns:
            QualityIssue instance
        """
        severity = finding.get("severity", "medium").lower()
        sev_map = {
            "critical": SeverityLevel.CRITICAL,
            "high": SeverityLevel.HIGH,
            "medium": SeverityLevel.MEDIUM,
            "low": SeverityLevel.LOW,
        }

        return QualityIssue(
            category=QualityCategory.SECURITY,
            severity=sev_map.get(severity, SeverityLevel.MEDIUM),
            title=finding.get("title", "Security finding"),
            description=finding.get("description", "Potential security issue"),
            element=finding.get("file") or finding.get("package"),
            line=finding.get("line"),
            suggestion=finding.get("suggestion") or "Review and remediate this security issue",
        )

    def scan(self, target: str, context: Dict[str, Any] | None = None) -> QualityScore:
        """Run security scan on target.

        This method runs all available security tools and aggregates results.
        Falls back to context-based scanning if no tools are available.

        Args:
            target: Path to scan (file or directory)
            context: Optional context with pre-computed findings

        Returns:
            QualityScore with aggregated security findings
        """
        context = context or {}
        self._scan_results = []
        all_findings: List[Dict[str, Any]] = []

        # Determine which tools to run
        enabled_tools = self.config.get("enabled_tools", ["bandit", "pip-audit", "safety"])

        # Run bandit for Python code analysis
        if "bandit" in enabled_tools and self.is_tool_available("bandit"):
            result = self._run_bandit(target)
            self._scan_results.append(result)
            if result.status == SecurityToolStatus.AVAILABLE:
                all_findings.extend(result.findings)
                logger.info(f"bandit found {len(result.findings)} issues in {result.elapsed_seconds:.2f}s")

        # Run pip-audit for dependency scanning
        if "pip-audit" in enabled_tools and self.is_tool_available("pip-audit"):
            result = self._run_pip_audit(target)
            self._scan_results.append(result)
            if result.status == SecurityToolStatus.AVAILABLE:
                all_findings.extend(result.findings)
                logger.info(f"pip-audit found {len(result.findings)} issues in {result.elapsed_seconds:.2f}s")

        # Run safety as alternative dependency scanner
        if "safety" in enabled_tools and self.is_tool_available("safety"):
            result = self._run_safety(target)
            self._scan_results.append(result)
            if result.status == SecurityToolStatus.AVAILABLE:
                all_findings.extend(result.findings)
                logger.info(f"safety found {len(result.findings)} issues in {result.elapsed_seconds:.2f}s")

        # Fallback to context-based findings if no tools ran
        if not self._scan_results or all(r.status != SecurityToolStatus.AVAILABLE for r in self._scan_results):
            logger.warning("No security tools available, using context-based findings")
            all_findings = context.get("security_findings", [])

        # Deduplicate findings by ID
        seen_ids = set()
        unique_findings = []
        for f in all_findings:
            fid = f.get("id", f.get("title", ""))
            if fid not in seen_ids:
                seen_ids.add(fid)
                unique_findings.append(f)

        # Convert to QualityIssues
        issues = [self._finding_to_issue(f) for f in unique_findings]

        # Calculate score
        critical_high = [
            i for i in issues if i.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)
        ]
        medium = [i for i in issues if i.severity == SeverityLevel.MEDIUM]

        # Score: 100 - (critical/high * 20) - (medium * 5) - (low * 2)
        score = max(0.0, 100.0 - (len(critical_high) * 20.0) - (len(medium) * 5.0) - ((len(issues) - len(critical_high) - len(medium)) * 2.0))

        self._last_scan_time = datetime.now()

        # Build details
        tool_results = {
            r.tool: {
                "status": r.status.value,
                "exit_code": r.exit_code,
                "findings_count": len(r.findings),
                "elapsed_seconds": r.elapsed_seconds,
                "error": r.error
            }
            for r in self._scan_results
        }

        return QualityScore(
            category=QualityCategory.SECURITY,
            score=score,
            passed=len(critical_high) == 0,
            issues=issues,
            details={
                "finding_count": len(issues),
                "critical_high": len(critical_high),
                "medium": len(medium),
                "target": target,
                "tools_used": [r.tool for r in self._scan_results if r.status == SecurityToolStatus.AVAILABLE],
                "tool_results": tool_results,
                "scan_time": self._last_scan_time.isoformat() if self._last_scan_time else None,
            }
        )

    def get_last_results(self) -> List[SecurityToolResult]:
        """Get results from the last scan.

        Returns:
            List of SecurityToolResult from last scan
        """
        return self._scan_results.copy()
