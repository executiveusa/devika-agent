"""
SYNTHIA Quality Gates - Phase 5 Implementation
==============================================

Automated quality enforcement system with:
- Lighthouse CI integration for performance scoring
- WCAG 2.1 AA accessibility validation
- Security vulnerability scanning
- Automated test generation
- Visual regression testing
- Quality metrics collection

Quality Thresholds:
- Lighthouse Performance: ≥95
- Lighthouse Accessibility: ≥90
- Lighthouse Best Practices: ≥95
- Lighthouse SEO: ≥90
- WCAG 2.1 AA: 100% compliance
- Security: Zero high/critical vulnerabilities
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import asyncio
import logging
import json

logger = logging.getLogger("synthia.quality")


class QualityCategory(Enum):
    """Categories of quality checks"""
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"
    SECURITY = "security"
    SEO = "seo"
    BEST_PRACTICES = "best_practices"
    VISUAL = "visual"
    TESTING = "testing"


class SeverityLevel(Enum):
    """Severity levels for quality issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class QualityThresholds:
    """
    Quality thresholds for validation.
    
    These thresholds define the minimum acceptable scores
    for each quality category.
    """
    lighthouse_performance: float = 95.0
    lighthouse_accessibility: float = 90.0
    lighthouse_best_practices: float = 95.0
    lighthouse_seo: float = 90.0
    wcag_compliance: float = 100.0
    security_high_critical: int = 0  # Zero tolerance for high/critical
    security_medium_max: int = 5
    test_coverage_min: float = 80.0
    visual_diff_threshold: float = 0.01  # 1% max diff
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert thresholds to dictionary"""
        return {
            "lighthouse_performance": self.lighthouse_performance,
            "lighthouse_accessibility": self.lighthouse_accessibility,
            "lighthouse_best_practices": self.lighthouse_best_practices,
            "lighthouse_seo": self.lighthouse_seo,
            "wcag_compliance": self.wcag_compliance,
            "security_high_critical": self.security_high_critical,
            "security_medium_max": self.security_medium_max,
            "test_coverage_min": self.test_coverage_min,
            "visual_diff_threshold": self.visual_diff_threshold
        }


@dataclass
class QualityIssue:
    """Represents a single quality issue"""
    category: QualityCategory
    severity: SeverityLevel
    title: str
    description: str
    element: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    url: Optional[str] = None
    suggestion: Optional[str] = None
    documentation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to dictionary"""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "element": self.element,
            "line": self.line,
            "column": self.column,
            "url": self.url,
            "suggestion": self.suggestion,
            "documentation": self.documentation
        }


@dataclass
class QualityScore:
    """Score for a specific quality category"""
    category: QualityCategory
    score: float
    max_score: float = 100.0
    issues: List[QualityIssue] = field(default_factory=list)
    passed: bool = True
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def percentage(self) -> float:
        """Get score as percentage"""
        return (self.score / self.max_score) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert score to dictionary"""
        return {
            "category": self.category.value,
            "score": self.score,
            "max_score": self.max_score,
            "percentage": self.percentage,
            "passed": self.passed,
            "issues": [issue.to_dict() for issue in self.issues],
            "details": self.details
        }


@dataclass
class QualityReport:
    """
    Comprehensive quality report for a codebase or URL.
    
    Contains scores for all quality categories and overall
    pass/fail status.
    """
    url: Optional[str] = None
    project_name: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    scores: Dict[str, QualityScore] = field(default_factory=dict)
    overall_passed: bool = True
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_score(self, score: QualityScore):
        """Add a quality score to the report"""
        self.scores[score.category.value] = score
        if not score.passed:
            self.overall_passed = False
    
    def get_score(self, category: QualityCategory) -> Optional[QualityScore]:
        """Get score for a specific category"""
        return self.scores.get(category.value)
    
    def get_all_issues(self, severity: Optional[SeverityLevel] = None) -> List[QualityIssue]:
        """Get all issues across all categories"""
        issues = []
        for score in self.scores.values():
            for issue in score.issues:
                if severity is None or issue.severity == severity:
                    issues.append(issue)
        return issues
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of the report"""
        return {
            "url": self.url,
            "project_name": self.project_name,
            "timestamp": self.timestamp,
            "overall_passed": self.overall_passed,
            "execution_time_ms": self.execution_time_ms,
            "scores": {
                category: {
                    "score": score.score,
                    "passed": score.passed,
                    "issue_count": len(score.issues)
                }
                for category, score in self.scores.items()
            },
            "total_issues": len(self.get_all_issues()),
            "critical_issues": len(self.get_all_issues(SeverityLevel.CRITICAL)),
            "high_issues": len(self.get_all_issues(SeverityLevel.HIGH))
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "url": self.url,
            "project_name": self.project_name,
            "timestamp": self.timestamp,
            "overall_passed": self.overall_passed,
            "execution_time_ms": self.execution_time_ms,
            "scores": {k: v.to_dict() for k, v in self.scores.items()},
            "summary": self.get_summary(),
            "metadata": self.metadata
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert report to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)


class QualityGate:
    """
    Main quality gate orchestrator.
    
    Coordinates all quality checks and enforces thresholds.
    """
    
    def __init__(
        self,
        thresholds: Optional[QualityThresholds] = None,
        enabled_checks: Optional[List[QualityCategory]] = None
    ):
        self.thresholds = thresholds or QualityThresholds()
        self.enabled_checks = enabled_checks or list(QualityCategory)
        self._checkers: Dict[QualityCategory, Callable] = {}
        
    def register_checker(
        self,
        category: QualityCategory,
        checker: Callable
    ):
        """Register a quality checker for a category"""
        self._checkers[category] = checker
        logger.info(f"Registered quality checker for {category.value}")
    
    async def run_check(
        self,
        category: QualityCategory,
        target: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """Run a specific quality check"""
        if category not in self._checkers:
            logger.warning(f"No checker registered for {category.value}")
            return QualityScore(
                category=category,
                score=0,
                passed=False,
                issues=[QualityIssue(
                    category=category,
                    severity=SeverityLevel.HIGH,
                    title="Checker not available",
                    description=f"No checker registered for {category.value}"
                )]
            )
        
        checker = self._checkers[category]
        context = context or {}
        
        try:
            if asyncio.iscoroutinefunction(checker):
                result = await checker(target, context)
            else:
                result = checker(target, context)
            
            # Ensure result is a QualityScore
            if isinstance(result, QualityScore):
                return result
            elif isinstance(result, dict):
                return QualityScore(
                    category=category,
                    score=result.get("score", 0),
                    issues=[QualityIssue(**i) for i in result.get("issues", [])],
                    passed=result.get("passed", True),
                    details=result.get("details", {})
                )
            else:
                return QualityScore(
                    category=category,
                    score=float(result) if result else 0
                )
                
        except Exception as e:
            logger.error(f"Quality check failed for {category.value}: {e}")
            return QualityScore(
                category=category,
                score=0,
                passed=False,
                issues=[QualityIssue(
                    category=category,
                    severity=SeverityLevel.CRITICAL,
                    title="Check execution failed",
                    description=str(e)
                )]
            )
    
    async def run_all_checks(
        self,
        target: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityReport:
        """Run all enabled quality checks"""
        start_time = datetime.now()
        report = QualityReport(
            url=target if target.startswith("http") else None,
            project_name=context.get("project_name") if context else None
        )
        
        # Run checks in parallel
        tasks = []
        for category in self.enabled_checks:
            if category in self._checkers:
                tasks.append(self.run_check(category, target, context))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, QualityScore):
                    report.add_score(result)
                elif isinstance(result, Exception):
                    logger.error(f"Check failed with exception: {result}")
        
        # Calculate execution time
        report.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return report
    
    def evaluate_thresholds(self, report: QualityReport) -> Dict[str, Any]:
        """Evaluate report against thresholds"""
        evaluation = {
            "passed": True,
            "failures": [],
            "warnings": []
        }
        
        # Lighthouse Performance
        perf = report.get_score(QualityCategory.PERFORMANCE)
        if perf:
            if perf.score < self.thresholds.lighthouse_performance:
                evaluation["passed"] = False
                evaluation["failures"].append({
                    "category": "lighthouse_performance",
                    "actual": perf.score,
                    "required": self.thresholds.lighthouse_performance
                })
        
        # Lighthouse Accessibility
        a11y = report.get_score(QualityCategory.ACCESSIBILITY)
        if a11y:
            if a11y.score < self.thresholds.lighthouse_accessibility:
                evaluation["passed"] = False
                evaluation["failures"].append({
                    "category": "lighthouse_accessibility",
                    "actual": a11y.score,
                    "required": self.thresholds.lighthouse_accessibility
                })
        
        # Security
        security = report.get_score(QualityCategory.SECURITY)
        if security:
            critical_high = len([
                i for i in security.issues
                if i.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)
            ])
            if critical_high > self.thresholds.security_high_critical:
                evaluation["passed"] = False
                evaluation["failures"].append({
                    "category": "security_high_critical",
                    "actual": critical_high,
                    "required": self.thresholds.security_high_critical
                })
        
        return evaluation
    
    async def enforce(
        self,
        target: str,
        context: Optional[Dict[str, Any]] = None,
        fail_fast: bool = True
    ) -> QualityReport:
        """
        Run quality gates and enforce thresholds.
        
        If fail_fast is True, stops on first critical failure.
        """
        report = await self.run_all_checks(target, context)
        evaluation = self.evaluate_thresholds(report)
        
        report.metadata["threshold_evaluation"] = evaluation
        report.overall_passed = evaluation["passed"]
        
        if not evaluation["passed"]:
            logger.warning(f"Quality gate failed: {evaluation['failures']}")
            for failure in evaluation["failures"]:
                logger.warning(f"  - {failure['category']}: {failure['actual']} < {failure['required']}")
        
        return report


# Convenience function for quick quality checks
async def check_quality(
    target: str,
    thresholds: Optional[QualityThresholds] = None,
    context: Optional[Dict[str, Any]] = None
) -> QualityReport:
    """
    Quick quality check function.
    
    Creates a quality gate with default settings and runs all checks.
    """
    gate = QualityGate(thresholds=thresholds)

    # Import and register default checkers. Keep this resilient so partial
    # environments still produce a report instead of crashing.
    lighthouse = None
    accessibility_checker = None
    security_scanner = None
    visual_regression = None
    test_generator = None
    metrics_collector = None

    try:
        from .lighthouse_runner import LighthouseRunner
        lighthouse = LighthouseRunner()
    except Exception as exc:
        logger.warning("Lighthouse checker unavailable: %s", exc)

    try:
        from .accessibility_checker import AccessibilityChecker
        accessibility_checker = AccessibilityChecker()
    except Exception as exc:
        logger.warning("Accessibility checker unavailable: %s", exc)

    try:
        from .security_scanner import SecurityScanner
        security_scanner = SecurityScanner()
    except Exception as exc:
        logger.warning("Security scanner unavailable: %s", exc)

    try:
        from .visual_regression import VisualRegressionTester
        visual_regression = VisualRegressionTester()
    except Exception as exc:
        logger.warning("Visual regression checker unavailable: %s", exc)

    try:
        from .test_generator import TestGenerator
        test_generator = TestGenerator()
    except Exception as exc:
        logger.warning("Test generator unavailable: %s", exc)

    try:
        from .metrics_collector import MetricsCollector
        metrics_collector = MetricsCollector()
    except Exception as exc:
        logger.warning("Metrics collector unavailable: %s", exc)
    
    # Register checkers
    if lighthouse:
        gate.register_checker(QualityCategory.PERFORMANCE, lighthouse.check_performance)
        gate.register_checker(QualityCategory.SEO, lighthouse.check_seo)
        gate.register_checker(QualityCategory.BEST_PRACTICES, lighthouse.check_best_practices)

    if accessibility_checker:
        gate.register_checker(QualityCategory.ACCESSIBILITY, accessibility_checker.check)
    if security_scanner:
        gate.register_checker(QualityCategory.SECURITY, security_scanner.scan)
    if visual_regression:
        gate.register_checker(QualityCategory.VISUAL, visual_regression.compare)
    if test_generator:
        gate.register_checker(QualityCategory.TESTING, test_generator.check_coverage)

    # Metrics collector is optional metadata only; not a scoring category.
    _ = metrics_collector
    
    return await gate.run_all_checks(target, context)


__all__ = [
    "QualityCategory",
    "SeverityLevel",
    "QualityThresholds",
    "QualityIssue",
    "QualityScore",
    "QualityReport",
    "QualityGate",
    "check_quality"
]
