"""Security scanning checks for SYNTHIA quality gates."""

from typing import Any, Dict, List

from . import QualityCategory, QualityIssue, QualityScore, SeverityLevel


class SecurityScanner:
    """Minimal security scanner adapter.

    This implementation is intentionally lightweight and deterministic.
    It can be expanded to run bandit/semgrep/pip-audit in CI.
    """

    def scan(self, target: str, context: Dict[str, Any] | None = None) -> QualityScore:
        context = context or {}
        findings: List[QualityIssue] = []

        known_findings = context.get("security_findings", [])
        for finding in known_findings:
            severity = finding.get("severity", "medium").lower()
            sev_map = {
                "critical": SeverityLevel.CRITICAL,
                "high": SeverityLevel.HIGH,
                "medium": SeverityLevel.MEDIUM,
                "low": SeverityLevel.LOW,
            }
            findings.append(
                QualityIssue(
                    category=QualityCategory.SECURITY,
                    severity=sev_map.get(severity, SeverityLevel.MEDIUM),
                    title=finding.get("title", "Security finding"),
                    description=finding.get("description", "Potential security issue"),
                    suggestion=finding.get("suggestion", "Review and remediate this issue"),
                )
            )

        critical_high = [
            f for f in findings if f.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)
        ]
        score = max(0.0, 100.0 - (len(critical_high) * 20.0) - ((len(findings) - len(critical_high)) * 5.0))

        return QualityScore(
            category=QualityCategory.SECURITY,
            score=score,
            passed=len(critical_high) == 0,
            issues=findings,
            details={"finding_count": len(findings), "critical_high": len(critical_high), "target": target},
        )
