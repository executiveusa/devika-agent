"""Visual regression checker for SYNTHIA quality gates."""

from typing import Any, Dict

from . import QualityCategory, QualityIssue, QualityScore, SeverityLevel


class VisualRegressionTester:
    """Compares visual snapshots via provided diff ratio.

    Callers can pass `visual_diff_ratio` in context to integrate with external
    screenshot tooling.
    """

    def compare(self, target: str, context: Dict[str, Any] | None = None) -> QualityScore:
        context = context or {}
        diff_ratio = float(context.get("visual_diff_ratio", 0.0))
        threshold = float(context.get("visual_diff_threshold", 0.01))

        issues = []
        passed = diff_ratio <= threshold
        if not passed:
            issues.append(
                QualityIssue(
                    category=QualityCategory.VISUAL,
                    severity=SeverityLevel.MEDIUM,
                    title="Visual regression detected",
                    description=f"Diff ratio {diff_ratio:.4f} exceeds threshold {threshold:.4f}",
                    suggestion="Review screenshot diffs and approve or update baselines",
                )
            )

        score = max(0.0, 100.0 - (diff_ratio * 100.0 * 10.0))
        return QualityScore(
            category=QualityCategory.VISUAL,
            score=score,
            passed=passed,
            issues=issues,
            details={"diff_ratio": diff_ratio, "threshold": threshold, "target": target},
        )
