"""
SYNTHIA Strategic Planner
=========================
Generates strategic upgrade plans with priority ranking and risk assessment.

Based on Ralphy patterns:
- Task prioritization: Architectural > Integration > Unknown > Standard > Polish
- Small focused commits
- Parallel execution with worktrees
- Retry logic with exponential backoff
"""

import os
import re
import json
from typing import Optional, Dict, List, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class TaskPriority(Enum):
    """Task priority levels based on Ralphy's prioritization"""
    ARCHITECTURAL = 1  # Core changes, breaking changes, refactoring
    INTEGRATION = 2   # API integrations, third-party services
    UNKNOWN = 3       # Tasks requiring investigation
    STANDARD = 4      # Regular features, bug fixes
    POLISH = 5        # UI improvements, optimizations, documentation


class TaskType(Enum):
    """Types of tasks"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    TEST = "test"
    DEPENDENCY = "dependency"
    UI_UX = "ui_ux"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class Task:
    """A single task in the plan"""
    id: str
    title: str
    description: str
    task_type: TaskType
    priority: TaskPriority
    dependencies: List[str]  # Task IDs this depends on
    affected_files: List[str]
    estimated_complexity: str  # low, medium, high
    risk_level: str  # low, medium, high, critical
    impact_score: float  # 0-10
    effort_score: float  # 0-10
    tags: List[str]
    notes: str


@dataclass
class Phase:
    """A phase in the strategic plan"""
    name: str
    description: str
    tasks: List[Task]
    estimated_effort: str
    risk_level: str
    prerequisites: List[str]


@dataclass
class RiskAssessment:
    """Risk assessment for the plan"""
    overall_risk: str  # low, medium, high, critical
    risk_factors: List[Dict[str, str]]
    mitigation_strategies: List[str]
    rollback_plan: str


@dataclass
class ImpactAnalysis:
    """Impact analysis for the plan"""
    affected_components: List[str]
    breaking_changes: List[str]
    new_dependencies: List[str]
    removed_dependencies: List[str]
    performance_impact: str
    security_impact: str


@dataclass
class StrategicPlan:
    """Complete strategic upgrade plan"""
    project_name: str
    objective: str
    phases: List[Phase]
    total_tasks: int
    risk_assessment: RiskAssessment
    impact_analysis: ImpactAnalysis
    execution_order: List[str]  # Ordered task IDs
    parallel_groups: List[List[str]]  # Tasks that can run in parallel
    estimated_timeline: str
    success_criteria: List[str]
    created_at: datetime


class StrategicPlanner:
    """
    Generates strategic upgrade plans with priority ranking.
    
    Features:
    - Priority-based task ordering (Ralphy's prioritization)
    - Dependency graph analysis
    - Risk assessment
    - Impact analysis
    - Parallel execution grouping
    - Rollback planning
    
    Usage:
        planner = StrategicPlanner()
        plan = planner.generate_plan(
            objective="Upgrade to React 18",
            scan_result=scan_result,
            architecture_report=arch_report
        )
        print(f"Total tasks: {plan.total_tasks}")
    """
    
    # Priority mapping based on task type
    TYPE_PRIORITY_MAP = {
        TaskType.SECURITY: TaskPriority.ARCHITECTURAL,
        TaskType.REFRACTOR: TaskPriority.ARCHITECTURAL,
        TaskType.INFRASTRUCTURE: TaskPriority.ARCHITECTURAL,
        TaskType.INTEGRATION: TaskPriority.INTEGRATION,
        TaskType.DEPENDENCY: TaskPriority.INTEGRATION,
        TaskType.FEATURE: TaskPriority.STANDARD,
        TaskType.BUGFIX: TaskPriority.STANDARD,
        TaskType.PERFORMANCE: TaskPriority.STANDARD,
        TaskType.UI_UX: TaskPriority.POLISH,
        TaskType.DOCUMENTATION: TaskPriority.POLISH,
        TaskType.TEST: TaskPriority.STANDARD,
    }
    
    # Risk indicators
    RISK_INDICATORS = {
        "critical": ["security", "authentication", "payment", "data loss", "breaking change"],
        "high": ["database migration", "api change", "dependency update", "refactor core"],
        "medium": ["feature change", "ui redesign", "performance optimization"],
        "low": ["documentation", "styling", "minor fix", "test addition"]
    }
    
    def __init__(self, memory_client: Optional[Any] = None):
        self.memory = memory_client
    
    def generate_plan(
        self,
        objective: str,
        scan_result: Any,
        architecture_report: Optional[Any] = None,
        niche_profile: Optional[Any] = None,
        constraints: Optional[Dict] = None
    ) -> StrategicPlan:
        """
        Generate a strategic upgrade plan.
        
        Args:
            objective: The main objective/goal
            scan_result: RepositoryScanner result
            architecture_report: ArchitectureAnalyzer result (optional)
            niche_profile: NicheDetector result (optional)
            constraints: Additional constraints (time, resources, etc.)
            
        Returns:
            StrategicPlan with complete execution strategy
        """
        constraints = constraints or {}
        
        # Analyze objective and generate tasks
        tasks = self._generate_tasks(
            objective, scan_result, architecture_report, niche_profile
        )
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(tasks)
        
        # Determine execution order
        execution_order = self._topological_sort(tasks, dependency_graph)
        
        # Group parallelizable tasks
        parallel_groups = self._identify_parallel_groups(tasks, dependency_graph)
        
        # Create phases
        phases = self._create_phases(tasks, execution_order)
        
        # Assess risks
        risk_assessment = self._assess_risks(tasks, scan_result, architecture_report)
        
        # Analyze impact
        impact_analysis = self._analyze_impact(tasks, scan_result, architecture_report)
        
        # Determine success criteria
        success_criteria = self._determine_success_criteria(objective, tasks)
        
        # Estimate timeline
        timeline = self._estimate_timeline(tasks, parallel_groups, constraints)
        
        return StrategicPlan(
            project_name=os.path.basename(scan_result.root_path),
            objective=objective,
            phases=phases,
            total_tasks=len(tasks),
            risk_assessment=risk_assessment,
            impact_analysis=impact_analysis,
            execution_order=execution_order,
            parallel_groups=parallel_groups,
            estimated_timeline=timeline,
            success_criteria=success_criteria,
            created_at=datetime.now()
        )
    
    def _generate_tasks(
        self,
        objective: str,
        scan_result: Any,
        architecture_report: Optional[Any],
        niche_profile: Optional[Any]
    ) -> List[Task]:
        """Generate tasks based on objective and analysis"""
        tasks = []
        task_id = 0
        
        # Parse objective for task hints
        objective_lower = objective.lower()
        
        # Security tasks (from broken code detection)
        if architecture_report:
            for issue in architecture_report.security_issues:
                task_id += 1
                tasks.append(Task(
                    id=f"task-{task_id:03d}",
                    title=f"Fix security issue: {issue.vulnerability_type}",
                    description=issue.description,
                    task_type=TaskType.SECURITY,
                    priority=TaskPriority.ARCHITECTURAL,
                    dependencies=[],
                    affected_files=[issue.location.split(":")[0]],
                    estimated_complexity="medium",
                    risk_level=issue.severity,
                    impact_score=9.0 if issue.severity == "critical" else 7.0,
                    effort_score=3.0,
                    tags=["security", "critical"],
                    notes=f"CWE: {issue.cwe or 'N/A'}"
                ))
        
        # Performance tasks
        if architecture_report:
            for bottleneck in architecture_report.bottlenecks:
                task_id += 1
                tasks.append(Task(
                    id=f"task-{task_id:03d}",
                    title=f"Optimize: {bottleneck.issue_type}",
                    description=bottleneck.description,
                    task_type=TaskType.PERFORMANCE,
                    priority=self._get_priority_for_severity(bottleneck.severity),
                    dependencies=[],
                    affected_files=[bottleneck.location.split(":")[0]],
                    estimated_complexity="medium",
                    risk_level=bottleneck.severity,
                    impact_score=6.0,
                    effort_score=4.0,
                    tags=["performance", "optimization"],
                    notes=bottleneck.recommendation
                ))
        
        # Dependency update tasks
        for dep_info in scan_result.dependencies:
            for dep in dep_info.dependencies:
                # Check if update needed (simplified)
                if "update" in objective_lower or "upgrade" in objective_lower:
                    task_id += 1
                    tasks.append(Task(
                        id=f"task-{task_id:03d}",
                        title=f"Update dependency: {dep['name']}",
                        description=f"Update {dep['name']} from {dep.get('version', 'unknown')} to latest",
                        task_type=TaskType.DEPENDENCY,
                        priority=TaskPriority.INTEGRATION,
                        dependencies=[],
                        affected_files=[dep_info.file_path],
                        estimated_complexity="low",
                        risk_level="medium",
                        impact_score=4.0,
                        effort_score=2.0,
                        tags=["dependency", "update"],
                        notes="Check for breaking changes in changelog"
                    ))
        
        # Architecture improvement tasks
        if architecture_report:
            for rec in architecture_report.recommendations[:5]:
                task_id += 1
                tasks.append(Task(
                    id=f"task-{task_id:03d}",
                    title=f"Architecture: {rec[:50]}...",
                    description=rec,
                    task_type=TaskType.REFRACTOR,
                    priority=TaskPriority.ARCHITECTURAL,
                    dependencies=[],
                    affected_files=[],
                    estimated_complexity="high",
                    risk_level="medium",
                    impact_score=7.0,
                    effort_score=6.0,
                    tags=["architecture", "improvement"],
                    notes=""
                ))
        
        # UI/UX tasks based on niche
        if niche_profile:
            # Add design system implementation task
            task_id += 1
            tasks.append(Task(
                id=f"task-{task_id:03d}",
                title="Implement design system",
                description=f"Apply {niche_profile.niche_type} design direction",
                task_type=TaskType.UI_UX,
                priority=TaskPriority.POLISH,
                dependencies=[],
                affected_files=[],
                estimated_complexity="medium",
                risk_level="low",
                impact_score=5.0,
                effort_score=4.0,
                tags=["ui", "ux", "design-system"],
                notes=f"Colors: {niche_profile.design_direction.color_palette[:3]}"
            ))
            
            # Add accessibility task if high priority
            if niche_profile.accessibility_priority == "critical":
                task_id += 1
                tasks.append(Task(
                    id=f"task-{task_id:03d}",
                    title="Implement WCAG 2.1 AA compliance",
                    description="Ensure all UI components meet accessibility standards",
                    task_type=TaskType.FEATURE,
                    priority=TaskPriority.STANDARD,
                    dependencies=[],
                    affected_files=[],
                    estimated_complexity="medium",
                    risk_level="low",
                    impact_score=6.0,
                    effort_score=5.0,
                    tags=["accessibility", "wcag"],
                    notes="Critical for healthcare niche"
                ))
        
        # Add testing tasks
        if scan_result.test_files and len(scan_result.test_files) < scan_result.total_files * 0.1:
            task_id += 1
            tasks.append(Task(
                id=f"task-{task_id:03d}",
                title="Increase test coverage",
                description="Add unit tests for core components",
                task_type=TaskType.TEST,
                priority=TaskPriority.STANDARD,
                dependencies=[],
                affected_files=[],
                estimated_complexity="medium",
                risk_level="low",
                impact_score=5.0,
                effort_score=4.0,
                tags=["testing", "quality"],
                notes="Aim for >80% coverage on critical paths"
            ))
        
        # Add documentation task if missing
        if not scan_result.documentation:
            task_id += 1
            tasks.append(Task(
                id=f"task-{task_id:03d}",
                title="Create documentation",
                description="Add README, API docs, and contribution guide",
                task_type=TaskType.DOCUMENTATION,
                priority=TaskPriority.POLISH,
                dependencies=[],
                affected_files=[],
                estimated_complexity="low",
                risk_level="low",
                impact_score=3.0,
                effort_score=2.0,
                tags=["documentation"],
                notes=""
            ))
        
        # Sort tasks by priority
        tasks.sort(key=lambda t: t.priority.value)
        
        return tasks
    
    def _get_priority_for_severity(self, severity: str) -> TaskPriority:
        """Map severity to priority"""
        mapping = {
            "critical": TaskPriority.ARCHITECTURAL,
            "high": TaskPriority.INTEGRATION,
            "medium": TaskPriority.STANDARD,
            "low": TaskPriority.POLISH
        }
        return mapping.get(severity.lower(), TaskPriority.STANDARD)
    
    def _build_dependency_graph(self, tasks: List[Task]) -> Dict[str, Set[str]]:
        """Build dependency graph between tasks"""
        graph = {task.id: set(task.dependencies) for task in tasks}
        
        # Infer dependencies based on affected files
        file_to_tasks = defaultdict(list)
        for task in tasks:
            for file in task.affected_files:
                file_to_tasks[file].append(task.id)
        
        # If multiple tasks affect the same file, create dependencies
        for file, task_ids in file_to_tasks.items():
            if len(task_ids) > 1:
                # Earlier tasks should complete before later ones
                for i in range(1, len(task_ids)):
                    graph[task_ids[i]].add(task_ids[i-1])
        
        return graph
    
    def _topological_sort(
        self,
        tasks: List[Task],
        dependency_graph: Dict[str, Set[str]]
    ) -> List[str]:
        """Topological sort of tasks based on dependencies"""
        # Build reverse graph
        in_degree = defaultdict(int)
        reverse_graph = defaultdict(set)
        
        for task_id, deps in dependency_graph.items():
            for dep in deps:
                reverse_graph[dep].add(task_id)
                in_degree[task_id] += 1
        
        # Initialize queue with tasks that have no dependencies
        queue = [t.id for t in tasks if in_degree[t.id] == 0]
        result = []
        
        while queue:
            # Sort queue by priority to maintain order
            queue.sort(key=lambda tid: next(
                (t.priority.value for t in tasks if t.id == tid), 999
            ))
            
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in reverse_graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Handle cycles (shouldn't happen but just in case)
        remaining = [t.id for t in tasks if t.id not in result]
        result.extend(remaining)
        
        return result
    
    def _identify_parallel_groups(
        self,
        tasks: List[Task],
        dependency_graph: Dict[str, Set[str]]
    ) -> List[List[str]]:
        """Identify tasks that can be executed in parallel"""
        groups = []
        assigned = set()
        
        # Group by priority level
        for priority in TaskPriority:
            priority_tasks = [
                t.id for t in tasks
                if t.priority == priority and t.id not in assigned
            ]
            
            if priority_tasks:
                # Within same priority, group independent tasks
                independent = []
                dependent = []
                
                for task_id in priority_tasks:
                    if not dependency_graph.get(task_id):
                        independent.append(task_id)
                    else:
                        dependent.append(task_id)
                
                if independent:
                    groups.append(independent)
                    assigned.update(independent)
                
                # Dependent tasks go in separate groups
                for task_id in dependent:
                    groups.append([task_id])
                    assigned.add(task_id)
        
        return groups
    
    def _create_phases(
        self,
        tasks: List[Task],
        execution_order: List[str]
    ) -> List[Phase]:
        """Create execution phases"""
        phases = []
        task_map = {t.id: t for t in tasks}
        
        # Phase 1: Critical & Security
        security_tasks = [t for t in tasks if t.task_type == TaskType.SECURITY]
        if security_tasks:
            phases.append(Phase(
                name="Security Fixes",
                description="Address critical security vulnerabilities",
                tasks=security_tasks,
                estimated_effort="1-2 days",
                risk_level="high",
                prerequisites=[]
            ))
        
        # Phase 2: Architecture
        arch_tasks = [t for t in tasks if t.priority == TaskPriority.ARCHITECTURAL and t.task_type != TaskType.SECURITY]
        if arch_tasks:
            phases.append(Phase(
                name="Architecture Improvements",
                description="Refactoring and structural changes",
                tasks=arch_tasks,
                estimated_effort="3-5 days",
                risk_level="medium",
                prerequisites=["Security Fixes"] if security_tasks else []
            ))
        
        # Phase 3: Integration
        integration_tasks = [t for t in tasks if t.priority == TaskPriority.INTEGRATION]
        if integration_tasks:
            phases.append(Phase(
                name="Integrations & Dependencies",
                description="Update dependencies and integrate services",
                tasks=integration_tasks,
                estimated_effort="2-3 days",
                risk_level="medium",
                prerequisites=["Architecture Improvements"] if arch_tasks else []
            ))
        
        # Phase 4: Standard Features
        standard_tasks = [t for t in tasks if t.priority == TaskPriority.STANDARD]
        if standard_tasks:
            phases.append(Phase(
                name="Features & Fixes",
                description="Implement features and fix bugs",
                tasks=standard_tasks,
                estimated_effort="3-5 days",
                risk_level="low",
                prerequisites=["Integrations & Dependencies"] if integration_tasks else []
            ))
        
        # Phase 5: Polish
        polish_tasks = [t for t in tasks if t.priority == TaskPriority.POLISH]
        if polish_tasks:
            phases.append(Phase(
                name="Polish & Documentation",
                description="UI improvements and documentation",
                tasks=polish_tasks,
                estimated_effort="1-2 days",
                risk_level="low",
                prerequisites=["Features & Fixes"] if standard_tasks else []
            ))
        
        return phases
    
    def _assess_risks(
        self,
        tasks: List[Task],
        scan_result: Any,
        architecture_report: Optional[Any]
    ) -> RiskAssessment:
        """Assess overall risk of the plan"""
        risk_factors = []
        mitigation_strategies = []
        
        # Analyze task risks
        critical_tasks = [t for t in tasks if t.risk_level == "critical"]
        high_risk_tasks = [t for t in tasks if t.risk_level == "high"]
        
        if critical_tasks:
            risk_factors.append({
                "factor": "Critical security issues",
                "count": str(len(critical_tasks)),
                "impact": "System compromise risk"
            })
            mitigation_strategies.append("Implement security fixes before any other changes")
        
        if high_risk_tasks:
            risk_factors.append({
                "factor": "High-risk changes",
                "count": str(len(high_risk_tasks)),
                "impact": "Potential breaking changes"
            })
            mitigation_strategies.append("Create comprehensive test suite before changes")
        
        # Analyze architecture risks
        if architecture_report:
            if architecture_report.complexity_score > 70:
                risk_factors.append({
                    "factor": "High code complexity",
                    "score": str(architecture_report.complexity_score),
                    "impact": "Difficult to predict change impact"
                })
                mitigation_strategies.append("Add tests before refactoring high-complexity areas")
        
        # Determine overall risk
        if critical_tasks:
            overall_risk = "critical"
        elif high_risk_tasks or len(tasks) > 20:
            overall_risk = "high"
        elif len(tasks) > 10:
            overall_risk = "medium"
        else:
            overall_risk = "low"
        
        # Create rollback plan
        rollback_plan = self._create_rollback_plan(tasks, scan_result)
        
        return RiskAssessment(
            overall_risk=overall_risk,
            risk_factors=risk_factors,
            mitigation_strategies=mitigation_strategies,
            rollback_plan=rollback_plan
        )
    
    def _create_rollback_plan(self, tasks: List[Task], scan_result: Any) -> str:
        """Create rollback plan"""
        plan = []
        plan.append("## Rollback Plan")
        plan.append("")
        plan.append("### Pre-Implementation")
        plan.append("1. Create git branch: `git checkout -b upgrade-plan`")
        plan.append("2. Create backup: `git tag backup-pre-upgrade`")
        plan.append("3. Run full test suite and document results")
        plan.append("")
        plan.append("### If Issues Arise")
        plan.append("1. Stop all changes immediately")
        plan.append("2. `git checkout main` to return to stable state")
        plan.append("3. `git reset --hard backup-pre-upgrade` if needed")
        plan.append("4. Review failed changes and create new plan")
        plan.append("")
        plan.append("### Post-Implementation")
        plan.append("1. Run full test suite")
        plan.append("2. Perform manual QA")
        plan.append("3. Monitor for 24-48 hours before considering stable")
        
        return "\n".join(plan)
    
    def _analyze_impact(
        self,
        tasks: List[Task],
        scan_result: Any,
        architecture_report: Optional[Any]
    ) -> ImpactAnalysis:
        """Analyze impact of the plan"""
        affected_components = set()
        breaking_changes = []
        new_dependencies = []
        removed_dependencies = []
        
        for task in tasks:
            # Track affected components
            for file in task.affected_files:
                component = file.split("/")[0] if "/" in file else "root"
                affected_components.add(component)
            
            # Track breaking changes
            if task.task_type == TaskType.REFRACTOR:
                breaking_changes.append(f"{task.title}: May affect existing functionality")
            
            # Track dependency changes
            if task.task_type == TaskType.DEPENDENCY:
                if "update" in task.title.lower() or "upgrade" in task.title.lower():
                    dep_name = task.title.split(": ")[-1] if ": " in task.title else "unknown"
                    new_dependencies.append(dep_name)
        
        # Determine performance impact
        perf_tasks = [t for t in tasks if t.task_type == TaskType.PERFORMANCE]
        performance_impact = "positive" if perf_tasks else "neutral"
        
        # Determine security impact
        security_tasks = [t for t in tasks if t.task_type == TaskType.SECURITY]
        security_impact = "improved" if security_tasks else "neutral"
        
        return ImpactAnalysis(
            affected_components=list(affected_components),
            breaking_changes=breaking_changes,
            new_dependencies=new_dependencies,
            removed_dependencies=removed_dependencies,
            performance_impact=performance_impact,
            security_impact=security_impact
        )
    
    def _determine_success_criteria(
        self,
        objective: str,
        tasks: List[Task]
    ) -> List[str]:
        """Determine success criteria for the plan"""
        criteria = []
        
        # Objective-based criteria
        criteria.append(f"Primary objective achieved: {objective}")
        
        # Task-based criteria
        security_tasks = [t for t in tasks if t.task_type == TaskType.SECURITY]
        if security_tasks:
            criteria.append(f"All {len(security_tasks)} security issues resolved")
        
        perf_tasks = [t for t in tasks if t.task_type == TaskType.PERFORMANCE]
        if perf_tasks:
            criteria.append("Performance benchmarks improved by at least 10%")
        
        # Quality criteria
        criteria.append("All existing tests pass")
        criteria.append("No new security vulnerabilities introduced")
        criteria.append("Code coverage maintained or improved")
        
        # Documentation criteria
        doc_tasks = [t for t in tasks if t.task_type == TaskType.DOCUMENTATION]
        if doc_tasks:
            criteria.append("Documentation updated to reflect changes")
        
        return criteria
    
    def _estimate_timeline(
        self,
        tasks: List[Task],
        parallel_groups: List[List[str]],
        constraints: Dict
    ) -> str:
        """Estimate timeline for execution"""
        # Base effort calculation
        total_effort = sum(t.effort_score for t in tasks)
        
        # Adjust for parallelization
        parallel_factor = len(parallel_groups) / max(len(tasks), 1)
        adjusted_effort = total_effort * (1 - parallel_factor * 0.3)
        
        # Convert to timeline (assuming 1 effort unit = 0.5 days)
        days = adjusted_effort * 0.5
        
        # Apply constraints
        if constraints.get("max_days"):
            days = min(days, constraints["max_days"])
        
        # Format timeline
        if days <= 1:
            return "< 1 day"
        elif days <= 3:
            return "1-3 days"
        elif days <= 7:
            return "3-7 days"
        elif days <= 14:
            return "1-2 weeks"
        elif days <= 30:
            return "2-4 weeks"
        else:
            return "1+ month"
    
    def to_markdown(self, plan: StrategicPlan) -> str:
        """Convert plan to markdown format"""
        lines = []
        
        lines.append(f"# Strategic Plan: {plan.project_name}")
        lines.append("")
        lines.append(f"**Objective:** {plan.objective}")
        lines.append(f"**Created:** {plan.created_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**Total Tasks:** {plan.total_tasks}")
        lines.append(f"**Estimated Timeline:** {plan.estimated_timeline}")
        lines.append(f"**Overall Risk:** {plan.risk_assessment.overall_risk.upper()}")
        lines.append("")
        
        # Phases
        lines.append("## Execution Phases")
        lines.append("")
        
        for i, phase in enumerate(plan.phases, 1):
            lines.append(f"### Phase {i}: {phase.name}")
            lines.append(f"**Description:** {phase.description}")
            lines.append(f"**Effort:** {phase.estimated_effort}")
            lines.append(f"**Risk:** {phase.risk_level}")
            
            if phase.prerequisites:
                lines.append(f"**Prerequisites:** {', '.join(phase.prerequisites)}")
            
            lines.append("")
            lines.append("| Task | Type | Priority | Complexity | Risk |")
            lines.append("|------|------|----------|------------|------|")
            
            for task in phase.tasks:
                lines.append(
                    f"| {task.title[:40]}... | {task.task_type.value} | "
                    f"{task.priority.name} | {task.estimated_complexity} | {task.risk_level} |"
                )
            
            lines.append("")
        
        # Risk Assessment
        lines.append("## Risk Assessment")
        lines.append("")
        
        for factor in plan.risk_assessment.risk_factors:
            lines.append(f"- **{factor['factor']}** ({factor.get('count', 'N/A')}): {factor['impact']}")
        
        lines.append("")
        lines.append("### Mitigation Strategies")
        for strategy in plan.risk_assessment.mitigation_strategies:
            lines.append(f"- {strategy}")
        
        lines.append("")
        lines.append("### Rollback Plan")
        lines.append(plan.risk_assessment.rollback_plan)
        
        # Impact Analysis
        lines.append("")
        lines.append("## Impact Analysis")
        lines.append("")
        lines.append(f"**Affected Components:** {', '.join(plan.impact_analysis.affected_components) or 'None'}")
        lines.append(f"**Performance Impact:** {plan.impact_analysis.performance_impact}")
        lines.append(f"**Security Impact:** {plan.impact_analysis.security_impact}")
        
        if plan.impact_analysis.breaking_changes:
            lines.append("")
            lines.append("### Breaking Changes")
            for change in plan.impact_analysis.breaking_changes:
                lines.append(f"- {change}")
        
        # Success Criteria
        lines.append("")
        lines.append("## Success Criteria")
        lines.append("")
        for i, criterion in enumerate(plan.success_criteria, 1):
            lines.append(f"{i}. {criterion}")
        
        # Parallel Execution
        lines.append("")
        lines.append("## Parallel Execution Groups")
        lines.append("")
        for i, group in enumerate(plan.parallel_groups, 1):
            lines.append(f"**Group {i}:** {', '.join(group)}")
        
        return "\n".join(lines)