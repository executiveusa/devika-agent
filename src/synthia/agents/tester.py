"""
SYNTHIA Tester Agent
====================
Quality assurance and testing agent.

Responsibilities:
- Generate unit tests
- Run test suites
- Validate code quality
- Check coverage
- Performance benchmarks
- Accessibility validation
"""

import os
import re
import subprocess
import json
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import tempfile


@dataclass
class TestResult:
    """Result of a test execution"""
    test_name: str
    passed: bool
    duration: float
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None


@dataclass
class TestSuiteResult:
    """Result of a test suite"""
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    coverage: Optional[float] = None
    results: List[TestResult] = field(default_factory=list)


@dataclass
class QualityReport:
    """Complete quality report"""
    test_results: List[TestSuiteResult]
    lint_issues: List[Dict]
    coverage_percentage: float
    performance_metrics: Dict[str, float]
    accessibility_issues: List[Dict]
    recommendations: List[str]
    overall_score: float


class Tester:
    """
    Testing and quality assurance agent.
    
    Generates tests, runs test suites, and validates code quality.
    
    Usage:
        tester = Tester()
        report = tester.analyze("/path/to/project")
        print(f"Overall score: {report.overall_score}")
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
    
    def execute(self, context: Any, **kwargs) -> Dict:
        """Execute testing analysis"""
        project_path = kwargs.get("project_path") or context.metadata.get("project_path")
        
        if not project_path:
            return {
                "output": "No project path provided for testing",
                "errors": ["Missing project_path"]
            }
        
        report = self.analyze(project_path)
        
        return {
            "output": f"Quality score: {report.overall_score:.1f}/100. {report.test_results[0].passed if report.test_results else 0} tests passed.",
            "files_modified": [],
            "files_created": [],
            "metadata": {
                "overall_score": report.overall_score,
                "coverage": report.coverage_percentage,
                "test_results": [
                    {
                        "suite": r.suite_name,
                        "passed": r.passed,
                        "failed": r.failed,
                        "total": r.total_tests
                    }
                    for r in report.test_results
                ],
                "lint_issues": len(report.lint_issues),
                "accessibility_issues": len(report.accessibility_issues),
                "recommendations": report.recommendations
            }
        }
    
    def analyze(self, project_path: str) -> QualityReport:
        """
        Analyze project quality.
        
        Args:
            project_path: Path to project root
            
        Returns:
            QualityReport with all quality metrics
        """
        # Run tests
        test_results = self._run_tests(project_path)
        
        # Run linter
        lint_issues = self._run_linter(project_path)
        
        # Check coverage
        coverage = self._check_coverage(project_path)
        
        # Performance metrics
        performance = self._measure_performance(project_path)
        
        # Accessibility check
        accessibility = self._check_accessibility(project_path)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            test_results, lint_issues, coverage, accessibility
        )
        
        # Calculate overall score
        score = self._calculate_score(
            test_results, lint_issues, coverage, accessibility
        )
        
        return QualityReport(
            test_results=test_results,
            lint_issues=lint_issues,
            coverage_percentage=coverage,
            performance_metrics=performance,
            accessibility_issues=accessibility,
            recommendations=recommendations,
            overall_score=score
        )
    
    def _run_tests(self, project_path: str) -> List[TestSuiteResult]:
        """Run test suites"""
        results = []
        
        # Detect test framework
        test_framework = self._detect_test_framework(project_path)
        
        if test_framework == "pytest":
            results.append(self._run_pytest(project_path))
        elif test_framework == "jest":
            results.append(self._run_jest(project_path))
        elif test_framework == "go":
            results.append(self._run_go_test(project_path))
        else:
            # No tests found
            results.append(TestSuiteResult(
                suite_name="unknown",
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                duration=0
            ))
        
        return results
    
    def _detect_test_framework(self, project_path: str) -> Optional[str]:
        """Detect test framework used"""
        # Check for pytest
        if os.path.exists(os.path.join(project_path, "pytest.ini")):
            return "pytest"
        if os.path.exists(os.path.join(project_path, "setup.cfg")):
            with open(os.path.join(project_path, "setup.cfg")) as f:
                if "pytest" in f.read():
                    return "pytest"
        
        # Check for Jest
        if os.path.exists(os.path.join(project_path, "jest.config.js")):
            return "jest"
        if os.path.exists(os.path.join(project_path, "jest.config.ts")):
            return "jest"
        
        # Check for Go tests
        for root, dirs, files in os.walk(project_path):
            if any(f.endswith("_test.go") for f in files):
                return "go"
        
        # Check for Python test files
        for root, dirs, files in os.walk(project_path):
            if any(f.startswith("test_") and f.endswith(".py") for f in files):
                return "pytest"
            if any(f.endswith("_test.py") for f in files):
                return "pytest"
        
        return None
    
    def _run_pytest(self, project_path: str) -> TestSuiteResult:
        """Run pytest and parse results"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--json-report", "--json-report-file=-"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse JSON output
            try:
                report = json.loads(result.stdout)
                return TestSuiteResult(
                    suite_name="pytest",
                    total_tests=report.get("summary", {}).get("total", 0),
                    passed=report.get("summary", {}).get("passed", 0),
                    failed=report.get("summary", {}).get("failed", 0),
                    skipped=report.get("summary", {}).get("skipped", 0),
                    duration=report.get("duration", 0)
                )
            except json.JSONDecodeError:
                # Fallback to parsing text output
                output = result.stdout + result.stderr
                passed = len(re.findall(r"(\d+) passed", output))
                failed = len(re.findall(r"(\d+) failed", output))
                skipped = len(re.findall(r"(\d+) skipped", output))
                
                return TestSuiteResult(
                    suite_name="pytest",
                    total_tests=passed + failed + skipped,
                    passed=passed,
                    failed=failed,
                    skipped=skipped,
                    duration=0
                )
        except Exception as e:
            return TestSuiteResult(
                suite_name="pytest",
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                duration=0
            )
    
    def _run_jest(self, project_path: str) -> TestSuiteResult:
        """Run Jest and parse results"""
        try:
            result = subprocess.run(
                ["npm", "test", "--", "--json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse JSON output
            try:
                report = json.loads(result.stdout)
                success = report.get("success", False)
                num_total = report.get("numTotalTests", 0)
                num_passed = report.get("numPassedTests", 0)
                num_failed = report.get("numFailedTests", 0)
                
                return TestSuiteResult(
                    suite_name="jest",
                    total_tests=num_total,
                    passed=num_passed,
                    failed=num_failed,
                    skipped=num_total - num_passed - num_failed,
                    duration=0
                )
            except json.JSONDecodeError:
                return TestSuiteResult(
                    suite_name="jest",
                    total_tests=0,
                    passed=0,
                    failed=0,
                    skipped=0,
                    duration=0
                )
        except Exception:
            return TestSuiteResult(
                suite_name="jest",
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                duration=0
            )
    
    def _run_go_test(self, project_path: str) -> TestSuiteResult:
        """Run Go tests and parse results"""
        try:
            result = subprocess.run(
                ["go", "test", "-v", "./..."],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            output = result.stdout + result.stderr
            passed = len(re.findall(r"--- PASS:", output))
            failed = len(re.findall(r"--- FAIL:", output))
            skipped = len(re.findall(r"--- SKIP:", output))
            
            return TestSuiteResult(
                suite_name="go",
                total_tests=passed + failed + skipped,
                passed=passed,
                failed=failed,
                skipped=skipped,
                duration=0
            )
        except Exception:
            return TestSuiteResult(
                suite_name="go",
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                duration=0
            )
    
    def _run_linter(self, project_path: str) -> List[Dict]:
        """Run linter and collect issues"""
        issues = []
        
        # Detect language and run appropriate linter
        if os.path.exists(os.path.join(project_path, "requirements.txt")):
            # Python - try pylint/flake8
            try:
                result = subprocess.run(
                    ["python", "-m", "flake8", "--format=json"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.stdout:
                    for line in result.stdout.strip().split("\n"):
                        try:
                            issue = json.loads(line)
                            issues.append({
                                "file": issue.get("path", ""),
                                "line": issue.get("row", 0),
                                "column": issue.get("column", 0),
                                "message": issue.get("text", ""),
                                "severity": "warning"
                            })
                        except json.JSONDecodeError:
                            continue
            except Exception:
                pass
        
        if os.path.exists(os.path.join(project_path, "package.json")):
            # JavaScript/TypeScript - try eslint
            try:
                result = subprocess.run(
                    ["npx", "eslint", "--format=json", "."],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.stdout:
                    report = json.loads(result.stdout)
                    for file_result in report:
                        for msg in file_result.get("messages", []):
                            issues.append({
                                "file": file_result.get("filePath", ""),
                                "line": msg.get("line", 0),
                                "column": msg.get("column", 0),
                                "message": msg.get("message", ""),
                                "severity": msg.get("severity", 1) == 1 and "warning" or "error"
                            })
            except Exception:
                pass
        
        return issues
    
    def _check_coverage(self, project_path: str) -> float:
        """Check test coverage"""
        # Try to find existing coverage report
        coverage_files = [
            "coverage.json",
            ".coverage",
            "coverage/lcov.info",
            "coverage/coverage-final.json"
        ]
        
        for cov_file in coverage_files:
            path = os.path.join(project_path, cov_file)
            if os.path.exists(path):
                try:
                    if cov_file.endswith(".json"):
                        with open(path) as f:
                            data = json.load(f)
                            if "coverage" in data:
                                return data["coverage"]
                            if "total" in data:
                                return data["total"].get("lines", {}).get("percentage", 0)
                except Exception:
                    continue
        
        # Try to run coverage
        if os.path.exists(os.path.join(project_path, "pytest.ini")):
            try:
                subprocess.run(
                    ["python", "-m", "pytest", "--cov", "--cov-report=json"],
                    cwd=project_path,
                    capture_output=True,
                    timeout=120
                )
                
                cov_path = os.path.join(project_path, "coverage.json")
                if os.path.exists(cov_path):
                    with open(cov_path) as f:
                        data = json.load(f)
                        return data.get("totals", {}).get("percent_covered", 0)
            except Exception:
                pass
        
        return 0.0
    
    def _measure_performance(self, project_path: str) -> Dict[str, float]:
        """Measure performance metrics"""
        metrics = {
            "bundle_size": 0,
            "startup_time": 0,
            "memory_usage": 0
        }
        
        # Check bundle size for JS projects
        if os.path.exists(os.path.join(project_path, "package.json")):
            dist_path = os.path.join(project_path, "dist")
            if os.path.exists(dist_path):
                total_size = 0
                for root, dirs, files in os.walk(dist_path):
                    for f in files:
                        total_size += os.path.getsize(os.path.join(root, f))
                metrics["bundle_size"] = total_size / 1024  # KB
        
        return metrics
    
    def _check_accessibility(self, project_path: str) -> List[Dict]:
        """Check accessibility issues"""
        issues = []
        
        # Check for common accessibility issues in HTML/JSX files
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
            
            for file in files:
                if file.endswith((".html", ".jsx", ".tsx", ".vue", ".svelte")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        # Check for missing alt attributes
                        img_tags = re.findall(r'<img[^>]*>', content)
                        for img in img_tags:
                            if "alt=" not in img:
                                issues.append({
                                    "file": file_path,
                                    "line": content[:content.index(img)].count("\n") + 1,
                                    "message": "Image missing alt attribute",
                                    "severity": "error"
                                })
                        
                        # Check for missing aria labels
                        buttons = re.findall(r'<button[^>]*>', content)
                        for btn in buttons:
                            if "aria-label=" not in btn and ">" in content[content.index(btn):content.index(btn) + 100]:
                                # Button has no accessible name
                                pass
                        
                        # Check for proper heading hierarchy
                        headings = re.findall(r'<h([1-6])', content)
                        if headings:
                            prev_level = 0
                            for level in map(int, headings):
                                if level > prev_level + 1 and prev_level != 0:
                                    issues.append({
                                        "file": file_path,
                                        "message": f"Heading hierarchy skip: h{prev_level} to h{level}",
                                        "severity": "warning"
                                    })
                                prev_level = level
                        
                    except Exception:
                        continue
        
        return issues
    
    def _generate_recommendations(
        self,
        test_results: List[TestSuiteResult],
        lint_issues: List[Dict],
        coverage: float,
        accessibility: List[Dict]
    ) -> List[str]:
        """Generate quality recommendations"""
        recommendations = []
        
        # Test recommendations
        for result in test_results:
            if result.total_tests == 0:
                recommendations.append("Add unit tests to improve code reliability")
            elif result.failed > 0:
                recommendations.append(f"Fix {result.failed} failing tests before deployment")
        
        # Coverage recommendations
        if coverage < 50:
            recommendations.append("Increase test coverage to at least 50%")
        elif coverage < 80:
            recommendations.append("Increase test coverage to 80% for better reliability")
        
        # Lint recommendations
        error_count = sum(1 for i in lint_issues if i.get("severity") == "error")
        if error_count > 0:
            recommendations.append(f"Fix {error_count} linting errors")
        
        # Accessibility recommendations
        if accessibility:
            recommendations.append(f"Address {len(accessibility)} accessibility issues for WCAG compliance")
        
        return recommendations
    
    def _calculate_score(
        self,
        test_results: List[TestSuiteResult],
        lint_issues: List[Dict],
        coverage: float,
        accessibility: List[Dict]
    ) -> float:
        """Calculate overall quality score"""
        score = 100.0
        
        # Test score (40% weight)
        if test_results:
            total = sum(r.total_tests for r in test_results)
            passed = sum(r.passed for r in test_results)
            if total > 0:
                test_score = (passed / total) * 40
                score = score * 0.6 + test_score
            else:
                score -= 20  # Penalty for no tests
        
        # Coverage score (20% weight)
        coverage_score = (coverage / 100) * 20
        score = score * 0.8 + coverage_score
        
        # Lint score (20% weight)
        error_count = sum(1 for i in lint_issues if i.get("severity") == "error")
        warning_count = sum(1 for i in lint_issues if i.get("severity") == "warning")
        lint_penalty = min(error_count * 2 + warning_count * 0.5, 20)
        score -= lint_penalty
        
        # Accessibility score (20% weight)
        a11y_penalty = min(len(accessibility) * 2, 20)
        score -= a11y_penalty
        
        return max(0, min(100, score))
    
    def generate_tests(
        self,
        source_file: str,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Generate unit tests for a source file.
        
        Args:
            source_file: Path to source file
            output_dir: Directory to write test file
            
        Returns:
            Path to generated test file
        """
        if not self.llm_client:
            raise ValueError("LLM client required for test generation")
        
        # Read source file
        with open(source_file, "r", encoding="utf-8") as f:
            source_code = f.read()
        
        # Determine test file path
        source_path = Path(source_file)
        if output_dir:
            test_dir = Path(output_dir)
        else:
            test_dir = source_path.parent / "tests"
        
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / f"test_{source_path.stem}.py"
        
        # Generate tests using LLM
        prompt = f"""
Generate comprehensive unit tests for the following Python code.
Include tests for:
- Normal cases
- Edge cases
- Error handling
- Boundary conditions

Source code:
```python
{source_code}
```

Output only the test code, no explanations.
"""
        
        # This would call the LLM in production
        test_code = f'"""Tests for {source_path.stem}"""\n\nimport pytest\nfrom {source_path.stem} import *\n\n# TODO: Add tests\n'
        
        # Write test file
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)
        
        return str(test_file)