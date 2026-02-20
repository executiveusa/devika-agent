"""Testing quality helper for coverage-based gating."""

from typing import Any, Dict

from . import QualityCategory, QualityIssue, QualityScore, SeverityLevel


class TestGenerator:
    """Coverage checker used by quality gates.

    Despite the name, this class currently validates reported coverage; real
    test generation should be added separately.
    """

    def check_coverage(self, target: str, context: Dict[str, Any] | None = None) -> QualityScore:
        context = context or {}
        coverage = float(context.get("test_coverage", 0.0))
        minimum = float(context.get("test_coverage_min", 80.0))

        passed = coverage >= minimum
        issues = []
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
            details={"coverage": coverage, "minimum": minimum, "target": target},
        )
