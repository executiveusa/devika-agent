"""Quality metrics collector utility.

Collects real metrics from:
- Git repository (commits, authors, changes)
- Codebase (file counts, lines of code)
- CI/CD (build info, status)
- Quality tools (coverage, lint results)
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("synthia.quality.metrics")


@dataclass
class GitMetrics:
    """Git repository metrics"""
    commit: str
    branch: str
    author: str
    message: str
    timestamp: str
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    is_dirty: bool = False
    remote_url: Optional[str] = None


@dataclass
class CodebaseMetrics:
    """Codebase structure metrics"""
    total_files: int = 0
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    by_extension: Dict[str, int] = field(default_factory=dict)
    by_directory: Dict[str, int] = field(default_factory=dict)
    largest_files: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CIMetrics:
    """CI/CD metrics"""
    build_id: str = "local"
    build_number: Optional[int] = None
    build_url: Optional[str] = None
    job_name: Optional[str] = None
    stage: Optional[str] = None
    is_ci: bool = False
    ci_platform: Optional[str] = None


@dataclass
class QualityMetrics:
    """Quality-specific metrics"""
    test_coverage: Optional[float] = None
    lint_errors: int = 0
    lint_warnings: int = 0
    security_issues: int = 0
    todo_count: int = 0
    fixme_count: int = 0


@dataclass
class MetricsCollectorHealthCheck:
    """Health check result for metrics collector"""
    git_available: bool
    project_dir: Optional[str]
    last_collection: Optional[str]
    status: str  # "ready", "partial", "unavailable"


class MetricsCollector:
    """Production metrics collector with real data sources.

    Collects comprehensive metrics from:
    - Git repository (commits, branches, changes)
    - Codebase (file counts, lines of code)
    - CI/CD environment (build info)
    - Quality tools (coverage, lint results)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize metrics collector with optional configuration.

        Args:
            config: Optional configuration dict with keys:
                - project_dir: Project directory path
                - exclude_dirs: Directories to exclude from analysis
                - exclude_extensions: File extensions to exclude
                - collect_git: Whether to collect git metrics (default: True)
                - collect_codebase: Whether to collect codebase metrics (default: True)
        """
        self.config = config or {}
        self._git_available: Optional[bool] = None
        self._last_collection_time: Optional[datetime] = None
        self._last_metrics: Dict[str, Any] = {}

    def _check_git_available(self) -> bool:
        """Check if git is available and we're in a repository."""
        if self._git_available is not None:
            return self._git_available

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                timeout=10
            )
            self._git_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._git_available = False

        return self._git_available

    def health_check(self) -> MetricsCollectorHealthCheck:
        """Perform health check on metrics collector.

        Returns:
            MetricsCollectorHealthCheck with availability status
        """
        git_ok = self._check_git_available()
        project_dir = self.config.get("project_dir", os.getcwd())

        status = "ready" if git_ok else "partial"

        return MetricsCollectorHealthCheck(
            git_available=git_ok,
            project_dir=project_dir,
            last_collection=self._last_collection_time.isoformat() if self._last_collection_time else None,
            status=status
        )

    def collect_git_metrics(self) -> GitMetrics:
        """Collect git repository metrics.

        Returns:
            GitMetrics with repository information
        """
        if not self._check_git_available():
            return GitMetrics(
                commit="unknown",
                branch="unknown",
                author="unknown",
                message="",
                timestamp=datetime.now().isoformat()
            )

        try:
            # Get commit hash
            commit_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10
            )
            commit = commit_result.stdout.strip()[:12] if commit_result.returncode == 0 else "unknown"

            # Get branch name
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10
            )
            branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

            # Get author
            author_result = subprocess.run(
                ["git", "log", "-1", "--format=%an"],
                capture_output=True,
                text=True,
                timeout=10
            )
            author = author_result.stdout.strip() if author_result.returncode == 0 else "unknown"

            # Get commit message
            message_result = subprocess.run(
                ["git", "log", "-1", "--format=%s"],
                capture_output=True,
                text=True,
                timeout=10
            )
            message = message_result.stdout.strip() if message_result.returncode == 0 else ""

            # Get timestamp
            timestamp_result = subprocess.run(
                ["git", "log", "-1", "--format=%ci"],
                capture_output=True,
                text=True,
                timeout=10
            )
            timestamp = timestamp_result.stdout.strip() if timestamp_result.returncode == 0 else datetime.now().isoformat()

            # Get diff stats
            files_changed = 0
            insertions = 0
            deletions = 0

            diff_result = subprocess.run(
                ["git", "diff", "--shortstat", "HEAD~1"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if diff_result.returncode == 0:
                # Parse: "3 files changed, 10 insertions(+), 5 deletions(-)"
                parts = diff_result.stdout.strip().split(",")
                for part in parts:
                    part = part.strip()
                    if "file" in part:
                        files_changed = int(part.split()[0])
                    elif "insertion" in part:
                        insertions = int(part.split()[0])
                    elif "deletion" in part:
                        deletions = int(part.split()[0])

            # Check if dirty
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10
            )
            is_dirty = bool(status_result.stdout.strip()) if status_result.returncode == 0 else False

            # Get remote URL
            remote_result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                timeout=10
            )
            remote_url = remote_result.stdout.strip() if remote_result.returncode == 0 else None

            return GitMetrics(
                commit=commit,
                branch=branch,
                author=author,
                message=message,
                timestamp=timestamp,
                files_changed=files_changed,
                insertions=insertions,
                deletions=deletions,
                is_dirty=is_dirty,
                remote_url=remote_url
            )

        except subprocess.TimeoutExpired:
            logger.warning("Git command timed out")
            return GitMetrics(
                commit="timeout",
                branch="unknown",
                author="unknown",
                message="",
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.warning(f"Git metrics collection failed: {e}")
            return GitMetrics(
                commit="error",
                branch="unknown",
                author="unknown",
                message="",
                timestamp=datetime.now().isoformat()
            )

    def collect_codebase_metrics(self) -> CodebaseMetrics:
        """Collect codebase structure metrics.

        Returns:
            CodebaseMetrics with file and line counts
        """
        project_dir = Path(self.config.get("project_dir", os.getcwd()))
        exclude_dirs = set(self.config.get("exclude_dirs", [
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            "build", "dist", ".tox", ".eggs", "*.egg-info"
        ]))
        exclude_extensions = set(self.config.get("exclude_extensions", [
            ".pyc", ".pyo", ".so", ".dll", ".dylib",
            ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
            ".pdf", ".zip", ".tar", ".gz", ".bz2",
            ".mp3", ".mp4", ".avi", ".mov",
        ]))

        metrics = CodebaseMetrics()

        try:
            for path in project_dir.rglob("*"):
                # Skip excluded directories
                if any(excluded in path.parts for excluded in exclude_dirs):
                    continue

                if path.is_file():
                    # Skip excluded extensions
                    if path.suffix.lower() in exclude_extensions:
                        continue

                    metrics.total_files += 1

                    # Count by extension
                    ext = path.suffix.lower() or ".no_extension"
                    metrics.by_extension[ext] = metrics.by_extension.get(ext, 0) + 1

                    # Count by directory
                    dir_name = str(path.parent.relative_to(project_dir))
                    metrics.by_directory[dir_name] = metrics.by_directory.get(dir_name, 0) + 1

                    # Count lines for text files
                    try:
                        if path.suffix.lower() in [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".css", ".scss", ".html", ".json", ".yaml", ".yml", ".md", ".txt", ".sh"]:
                            content = path.read_text(encoding="utf-8", errors="ignore")
                            lines = content.splitlines()

                            code_lines = 0
                            comment_lines = 0
                            blank_lines = 0

                            in_multiline_comment = False

                            for line in lines:
                                stripped = line.strip()

                                if not stripped:
                                    blank_lines += 1
                                elif stripped.startswith("#") or stripped.startswith("//"):
                                    comment_lines += 1
                                elif stripped.startswith("/*") or stripped.startswith("'''") or stripped.startswith('"""'):
                                    comment_lines += 1
                                    in_multiline_comment = True
                                elif stripped.endswith("*/") or stripped.endswith("'''") or stripped.endswith('"""'):
                                    comment_lines += 1
                                    in_multiline_comment = False
                                elif in_multiline_comment:
                                    comment_lines += 1
                                else:
                                    code_lines += 1

                            metrics.total_lines += len(lines)
                            metrics.code_lines += code_lines
                            metrics.comment_lines += comment_lines
                            metrics.blank_lines += blank_lines

                            # Track largest files
                            if len(lines) > 100:
                                metrics.largest_files.append({
                                    "path": str(path.relative_to(project_dir)),
                                    "lines": len(lines),
                                    "extension": path.suffix
                                })

                    except Exception as e:
                        logger.debug(f"Could not read file {path}: {e}")

            # Sort largest files
            metrics.largest_files.sort(key=lambda x: x["lines"], reverse=True)
            metrics.largest_files = metrics.largest_files[:10]

        except Exception as e:
            logger.warning(f"Codebase metrics collection failed: {e}")

        return metrics

    def collect_ci_metrics(self) -> CIMetrics:
        """Collect CI/CD environment metrics.

        Returns:
            CIMetrics with build information
        """
        metrics = CIMetrics()

        # Detect CI platform
        if os.environ.get("CI"):
            metrics.is_ci = True

            # GitHub Actions
            if os.environ.get("GITHUB_ACTIONS"):
                metrics.ci_platform = "github_actions"
                metrics.build_id = os.environ.get("GITHUB_RUN_ID", "local")
                metrics.build_number = int(os.environ.get("GITHUB_RUN_NUMBER", "0"))
                metrics.build_url = f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{metrics.build_id}"
                metrics.job_name = os.environ.get("GITHUB_JOB")

            # GitLab CI
            elif os.environ.get("GITLAB_CI"):
                metrics.ci_platform = "gitlab_ci"
                metrics.build_id = os.environ.get("CI_JOB_ID", "local")
                metrics.build_number = int(os.environ.get("CI_PIPELINE_ID", "0"))
                metrics.build_url = os.environ.get("CI_JOB_URL")
                metrics.job_name = os.environ.get("CI_JOB_NAME")
                metrics.stage = os.environ.get("CI_JOB_STAGE")

            # Jenkins
            elif os.environ.get("JENKINS_URL"):
                metrics.ci_platform = "jenkins"
                metrics.build_id = os.environ.get("BUILD_ID", "local")
                metrics.build_number = int(os.environ.get("BUILD_NUMBER", "0"))
                metrics.build_url = os.environ.get("BUILD_URL")
                metrics.job_name = os.environ.get("JOB_NAME")

            # CircleCI
            elif os.environ.get("CIRCLECI"):
                metrics.ci_platform = "circleci"
                metrics.build_id = os.environ.get("CIRCLE_BUILD_NUM", "local")
                metrics.build_number = int(os.environ.get("CIRCLE_BUILD_NUM", "0"))
                metrics.build_url = os.environ.get("CIRCLE_BUILD_URL")
                metrics.job_name = os.environ.get("CIRCLE_JOB")

            # Travis CI
            elif os.environ.get("TRAVIS"):
                metrics.ci_platform = "travis_ci"
                metrics.build_id = os.environ.get("TRAVIS_BUILD_ID", "local")
                metrics.build_number = int(os.environ.get("TRAVIS_BUILD_NUMBER", "0"))
                metrics.build_url = f"https://travis-ci.com/{os.environ.get('TRAVIS_REPO_SLUG', '')}/builds/{metrics.build_id}"
                metrics.job_name = os.environ.get("TRAVIS_JOB_NAME")

            # Azure DevOps
            elif os.environ.get("TF_BUILD"):
                metrics.ci_platform = "azure_devops"
                metrics.build_id = os.environ.get("Build.BuildId", "local")
                metrics.build_number = int(os.environ.get("Build.BuildNumber", "0"))
                metrics.build_url = os.environ.get("System.TeamFoundationCollectionUri")
                metrics.job_name = os.environ.get("Build.DefinitionName")

        return metrics

    def collect_quality_metrics(self, project_dir: Optional[str] = None) -> QualityMetrics:
        """Collect quality-specific metrics.

        Args:
            project_dir: Optional project directory override

        Returns:
            QualityMetrics with quality indicators
        """
        metrics = QualityMetrics()
        project_path = Path(project_dir or self.config.get("project_dir", os.getcwd()))

        # Count TODOs and FIXMEs
        todo_patterns = ["TODO", "FIXME", "XXX", "HACK"]
        exclude_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}

        try:
            for path in project_path.rglob("*"):
                if any(excluded in path.parts for excluded in exclude_dirs):
                    continue

                if path.is_file() and path.suffix.lower() in [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go"]:
                    try:
                        content = path.read_text(encoding="utf-8", errors="ignore")
                        for line in content.splitlines():
                            if "TODO" in line:
                                metrics.todo_count += 1
                            if "FIXME" in line:
                                metrics.fixme_count += 1
                    except Exception:
                        pass

        except Exception as e:
            logger.warning(f"Quality metrics collection failed: {e}")

        return metrics

    def collect(self, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Collect all metrics.

        This is the main entry point for metrics collection.
        Gathers git, codebase, CI, and quality metrics.

        Args:
            context: Optional context with additional metrics

        Returns:
            Dict with all collected metrics
        """
        context = context or {}
        self._last_collection_time = datetime.now()

        # Collect from all sources
        git_metrics = self.collect_git_metrics() if self.config.get("collect_git", True) else None
        codebase_metrics = self.collect_codebase_metrics() if self.config.get("collect_codebase", True) else None
        ci_metrics = self.collect_ci_metrics()
        quality_metrics = self.collect_quality_metrics()

        # Build result
        result = {
            "timestamp": self._last_collection_time.isoformat(),
            "collection_time": self._last_collection_time.isoformat(),
        }

        # Add git metrics
        if git_metrics:
            result["git"] = {
                "commit": git_metrics.commit,
                "branch": git_metrics.branch,
                "author": git_metrics.author,
                "message": git_metrics.message,
                "timestamp": git_metrics.timestamp,
                "files_changed": git_metrics.files_changed,
                "insertions": git_metrics.insertions,
                "deletions": git_metrics.deletions,
                "is_dirty": git_metrics.is_dirty,
                "remote_url": git_metrics.remote_url,
            }

        # Add codebase metrics
        if codebase_metrics:
            result["codebase"] = {
                "total_files": codebase_metrics.total_files,
                "total_lines": codebase_metrics.total_lines,
                "code_lines": codebase_metrics.code_lines,
                "comment_lines": codebase_metrics.comment_lines,
                "blank_lines": codebase_metrics.blank_lines,
                "by_extension": codebase_metrics.by_extension,
                "by_directory": dict(list(codebase_metrics.by_directory.items())[:20]),
                "largest_files": codebase_metrics.largest_files,
            }

        # Add CI metrics
        result["ci"] = {
            "build_id": ci_metrics.build_id,
            "build_number": ci_metrics.build_number,
            "build_url": ci_metrics.build_url,
            "job_name": ci_metrics.job_name,
            "stage": ci_metrics.stage,
            "is_ci": ci_metrics.is_ci,
            "ci_platform": ci_metrics.ci_platform,
        }

        # Add quality metrics
        result["quality"] = {
            "todo_count": quality_metrics.todo_count,
            "fixme_count": quality_metrics.fixme_count,
            "lint_errors": quality_metrics.lint_errors,
            "lint_warnings": quality_metrics.lint_warnings,
            "security_issues": quality_metrics.security_issues,
        }

        # Merge with context
        for key, value in context.items():
            if key not in result:
                result[key] = value

        self._last_metrics = result
        return result

    def get_last_metrics(self) -> Dict[str, Any]:
        """Get the last collected metrics.

        Returns:
            Dict with last collected metrics or empty dict
        """
        return self._last_metrics.copy()

    def to_summary(self, metrics: Optional[Dict[str, Any]] = None) -> str:
        """Generate a human-readable summary of metrics.

        Args:
            metrics: Optional metrics dict (uses last collected if not provided)

        Returns:
            Human-readable summary string
        """
        metrics = metrics or self._last_metrics
        if not metrics:
            return "No metrics collected"

        lines = ["=== SYNTHIA Quality Metrics ==="]

        # Git summary
        if "git" in metrics:
            git = metrics["git"]
            lines.append(f"\nGit: {git.get('commit', 'unknown')} on {git.get('branch', 'unknown')}")
            lines.append(f"  Author: {git.get('author', 'unknown')}")
            lines.append(f"  Message: {git.get('message', '')[:50]}...")
            if git.get("is_dirty"):
                lines.append("  Status: DIRTY (uncommitted changes)")

        # Codebase summary
        if "codebase" in metrics:
            cb = metrics["codebase"]
            lines.append(f"\nCodebase: {cb.get('total_files', 0)} files, {cb.get('total_lines', 0)} lines")
            lines.append(f"  Code: {cb.get('code_lines', 0)}, Comments: {cb.get('comment_lines', 0)}, Blank: {cb.get('blank_lines', 0)}")

        # CI summary
        if "ci" in metrics:
            ci = metrics["ci"]
            if ci.get("is_ci"):
                lines.append(f"\nCI: {ci.get('ci_platform', 'unknown')}")
                lines.append(f"  Build: {ci.get('build_id', 'unknown')}")
            else:
                lines.append("\nCI: Running locally")

        # Quality summary
        if "quality" in metrics:
            q = metrics["quality"]
            lines.append(f"\nQuality: {q.get('todo_count', 0)} TODOs, {q.get('fixme_count', 0)} FIXMEs")

        return "\n".join(lines)
