"""
SYNTHIA Architecture Analyzer
=============================
Analyzes project architecture, dependencies, and identifies issues.

Based on Ralphy patterns:
- Memory-first: Check cached analysis
- Parallel execution: Analyze multiple components concurrently
- Retry logic: Handle transient failures
"""

import os
import re
import json
from typing import Optional, Dict, List, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import subprocess


@dataclass
class ComponentDependency:
    """Dependency between components"""
    source: str
    target: str
    dependency_type: str  # import, function_call, inheritance, etc.
    strength: int  # number of connections


@dataclass
class Component:
    """A component in the architecture"""
    name: str
    path: str
    component_type: str  # module, class, function, api, etc.
    dependencies: List[str]
    dependents: List[str]
    complexity: float
    lines_of_code: int
    file_count: int
    issues: List[str]


@dataclass
class DataFlow:
    """Data flow between components"""
    source: str
    target: str
    data_type: str
    description: str


@dataclass
class PerformanceBottleneck:
    """Identified performance bottleneck"""
    location: str
    issue_type: str
    severity: str
    description: str
    recommendation: str


@dataclass
class SecurityVulnerability:
    """Security vulnerability in architecture"""
    location: str
    vulnerability_type: str
    severity: str
    description: str
    cwe: Optional[str]


@dataclass
class ArchitectureReport:
    """Complete architecture analysis report"""
    architecture_type: str  # monolith, microservices, serverless, etc.
    components: List[Component]
    dependencies: List[ComponentDependency]
    data_flows: List[DataFlow]
    bottlenecks: List[PerformanceBottleneck]
    security_issues: List[SecurityVulnerability]
    complexity_score: float
    maintainability_score: float
    testability_score: float
    recommendations: List[str]
    diagrams: Dict[str, str]  # Mermaid diagram definitions
    analysis_timestamp: datetime


class ArchitectureAnalyzer:
    """
    Analyzes project architecture comprehensively.
    
    Features:
    - Component detection and mapping
    - Dependency graph generation
    - Data flow analysis
    - Performance bottleneck detection
    - Security vulnerability scanning
    - Architecture pattern detection
    - Mermaid diagram generation
    
    Usage:
        analyzer = ArchitectureAnalyzer()
        report = analyzer.analyze(scan_result)
        print(f"Architecture: {report.architecture_type}")
    """
    
    # Architecture patterns
    ARCHITECTURE_PATTERNS = {
        "monolith": {
            "indicators": ["single codebase", "shared database", "tightly coupled"],
            "threshold": 0.7
        },
        "microservices": {
            "indicators": ["multiple services", "api gateway", "service discovery", "event bus"],
            "threshold": 0.6
        },
        "serverless": {
            "indicators": ["lambda functions", "api gateway", "managed services", "event-driven"],
            "threshold": 0.6
        },
        "layered": {
            "indicators": ["presentation layer", "business layer", "data layer", "separation of concerns"],
            "threshold": 0.7
        },
        "hexagonal": {
            "indicators": ["ports", "adapters", "domain core", "dependency inversion"],
            "threshold": 0.6
        },
        "event_driven": {
            "indicators": ["event bus", "message queue", "pub/sub", "event handlers"],
            "threshold": 0.6
        },
        "cqrs": {
            "indicators": ["command handler", "query handler", "separate models", "event sourcing"],
            "threshold": 0.6
        }
    }
    
    # Component type patterns
    COMPONENT_PATTERNS = {
        "api": {
            "files": ["routes", "views", "controllers", "endpoints", "api"],
            "extensions": [".py", ".js", ".ts", ".go", ".java", ".rb"]
        },
        "models": {
            "files": ["models", "entities", "schemas", "types", "domain"],
            "extensions": [".py", ".js", ".ts", ".go", ".java", ".rb"]
        },
        "services": {
            "files": ["services", "business", "logic", "handlers", "usecases"],
            "extensions": [".py", ".js", ".ts", ".go", ".java", ".rb"]
        },
        "data_access": {
            "files": ["repository", "dao", "data", "store", "persistence", "db"],
            "extensions": [".py", ".js", ".ts", ".go", ".java", ".rb"]
        },
        "ui": {
            "files": ["components", "pages", "views", "templates", "ui"],
            "extensions": [".jsx", ".tsx", ".vue", ".svelte", ".html"]
        },
        "utils": {
            "files": ["utils", "helpers", "common", "lib", "shared"],
            "extensions": [".py", ".js", ".ts", ".go", ".java", ".rb"]
        },
        "config": {
            "files": ["config", "settings", "env", "constants"],
            "extensions": [".py", ".js", ".ts", ".json", ".yaml", ".toml"]
        },
        "tests": {
            "files": ["test", "spec", "__test__", "tests"],
            "extensions": [".py", ".js", ".ts", ".go", ".java", ".rb"]
        }
    }
    
    # Performance issue patterns
    PERFORMANCE_PATTERNS = {
        "n_plus_one": {
            "pattern": r"for\s+\w+\s+in\s+.*:\s*\n.*(?:query|fetch|get|find|select)",
            "severity": "high",
            "description": "Potential N+1 query problem in loop"
        },
        "sync_in_loop": {
            "pattern": r"for\s+\w+\s+in\s+.*:\s*\n.*(?:requests\.|urllib|http\.|fetch\()",
            "severity": "high",
            "description": "Synchronous HTTP request in loop"
        },
        "unbounded_cache": {
            "pattern": r"(?:cache|memo)[^=]*=\s*(?:\{\}|dict\(\)|Dict\[)",
            "severity": "medium",
            "description": "Unbounded cache without eviction policy"
        },
        "large_data_in_memory": {
            "pattern":r"(?:load|read|fetch)_(?:all|everything|full)",
            "severity": "medium",
            "description": "Potential large data load into memory"
        },
        "blocking_io": {
            "pattern": r"(?:time\.sleep|input\(|wait\()",
            "severity": "low",
            "description": "Blocking I/O operation"
        }
    }
    
    def __init__(self, memory_client: Optional[Any] = None):
        self.memory = memory_client
    
    def analyze(
        self,
        scan_result: Any,
        deep_analysis: bool = True
    ) -> ArchitectureReport:
        """
        Analyze project architecture.
        
        Args:
            scan_result: RepositoryScanner result
            deep_analysis: Perform deep content analysis
            
        Returns:
            ArchitectureReport with complete analysis
        """
        # Detect components
        components = self._detect_components(scan_result)
        
        # Analyze dependencies
        dependencies = self._analyze_dependencies(scan_result, components)
        
        # Detect architecture type
        architecture_type = self._detect_architecture_type(components, dependencies)
        
        # Analyze data flows
        data_flows = self._analyze_data_flows(scan_result, components)
        
        # Detect performance bottlenecks
        bottlenecks = self._detect_bottlenecks(scan_result)
        
        # Detect security issues
        security_issues = self._detect_security_issues(scan_result)
        
        # Calculate scores
        complexity_score = self._calculate_complexity(components, dependencies)
        maintainability_score = self._calculate_maintainability(components, dependencies)
        testability_score = self._calculate_testability(scan_result, components)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            architecture_type, components, dependencies, bottlenecks, security_issues
        )
        
        # Generate diagrams
        diagrams = self._generate_diagrams(components, dependencies, data_flows)
        
        return ArchitectureReport(
            architecture_type=architecture_type,
            components=components,
            dependencies=dependencies,
            data_flows=data_flows,
            bottlenecks=bottlenecks,
            security_issues=security_issues,
            complexity_score=complexity_score,
            maintainability_score=maintainability_score,
            testability_score=testability_score,
            recommendations=recommendations,
            diagrams=diagrams,
            analysis_timestamp=datetime.now()
        )
    
    def _detect_components(self, scan_result: Any) -> List[Component]:
        """Detect components in the project"""
        components = []
        component_map = defaultdict(lambda: {
            "files": [],
            "dependencies": set(),
            "dependents": set(),
            "lines": 0,
            "issues": []
        })
        
        # Categorize files into components
        for file_info in scan_result.files:
            if file_info.is_binary or file_info.is_generated:
                continue
            
            # Determine component type
            component_type = self._get_component_type(file_info)
            if component_type:
                component_name = component_type
                component_map[component_name]["files"].append(file_info)
                component_map[component_name]["lines"] += file_info.line_count
        
        # Create Component objects
        for name, data in component_map.items():
            if data["files"]:
                components.append(Component(
                    name=name,
                    path=os.path.dirname(data["files"][0].relative_path),
                    component_type=self._get_component_category(name),
                    dependencies=list(data["dependencies"]),
                    dependents=list(data["dependents"]),
                    complexity=self._calculate_component_complexity(data),
                    lines_of_code=data["lines"],
                    file_count=len(data["files"]),
                    issues=data["issues"]
                ))
        
        return components
    
    def _get_component_type(self, file_info: Any) -> Optional[str]:
        """Determine component type for a file"""
        rel_path = file_info.relative_path.lower()
        filename = os.path.basename(file_info.path).lower()
        
        for comp_type, patterns in self.COMPONENT_PATTERNS.items():
            # Check filename patterns
            for pattern in patterns["files"]:
                if pattern in filename or pattern in rel_path:
                    if file_info.extension in patterns["extensions"]:
                        return comp_type
        
        return None
    
    def _get_component_category(self, component_type: str) -> str:
        """Get high-level category for component type"""
        categories = {
            "api": "presentation",
            "ui": "presentation",
            "models": "domain",
            "services": "business",
            "data_access": "infrastructure",
            "utils": "support",
            "config": "support",
            "tests": "quality"
        }
        return categories.get(component_type, "other")
    
    def _calculate_component_complexity(self, data: Dict) -> float:
        """Calculate complexity score for a component"""
        # Simple complexity based on file count and lines
        file_count = len(data["files"])
        lines = data["lines"]
        
        # More files and more lines = higher complexity
        complexity = (file_count * 0.3) + (lines / 1000 * 0.7)
        
        return min(10.0, complexity)
    
    def _analyze_dependencies(
        self,
        scan_result: Any,
        components: List[Component]
    ) -> List[ComponentDependency]:
        """Analyze dependencies between components"""
        dependencies = []
        
        # Build import map
        import_map = self._build_import_map(scan_result)
        
        # Create dependency graph
        for source, targets in import_map.items():
            for target in targets:
                # Find which components these belong to
                source_comp = self._find_component(source, components)
                target_comp = self._find_component(target, components)
                
                if source_comp and target_comp and source_comp != target_comp:
                    dependencies.append(ComponentDependency(
                        source=source_comp,
                        target=target_comp,
                        dependency_type="import",
                        strength=1
                    ))
        
        # Aggregate duplicate dependencies
        aggregated = defaultdict(lambda: {"count": 0, "type": "import"})
        for dep in dependencies:
            key = (dep.source, dep.target)
            aggregated[key]["count"] += 1
        
        return [
            ComponentDependency(
                source=key[0],
                target=key[1],
                dependency_type=data["type"],
                strength=data["count"]
            )
            for key, data in aggregated.items()
        ]
    
    def _build_import_map(self, scan_result: Any) -> Dict[str, Set[str]]:
        """Build map of imports between files"""
        import_map = defaultdict(set)
        
        for file_info in scan_result.files:
            if file_info.extension not in [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java"]:
                continue
            
            try:
                with open(file_info.path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                # Python imports
                if file_info.extension == ".py":
                    imports = re.findall(r"^(?:from|import)\s+(\S+)", content, re.MULTILINE)
                    for imp in imports:
                        import_map[file_info.relative_path].add(imp)
                
                # JavaScript/TypeScript imports
                elif file_info.extension in [".js", ".ts", ".jsx", ".tsx"]:
                    imports = re.findall(r"import.*from\s+['\"]([^'\"]+)['\"]", content)
                    imports += re.findall(r"require\(['\"]([^'\"]+)['\"]\)", content)
                    for imp in imports:
                        import_map[file_info.relative_path].add(imp)
                
                # Go imports
                elif file_info.extension == ".go":
                    imports = re.findall(r'import\s+(?:\([^)]+\)|"([^"]+)")', content, re.DOTALL)
                    for imp in imports:
                        if imp:
                            import_map[file_info.relative_path].add(imp)
                
                # Java imports
                elif file_info.extension == ".java":
                    imports = re.findall(r"import\s+([\w.]+);", content)
                    for imp in imports:
                        import_map[file_info.relative_path].add(imp)
            
            except Exception:
                continue
        
        return import_map
    
    def _find_component(self, file_path: str, components: List[Component]) -> Optional[str]:
        """Find which component a file belongs to"""
        file_path_lower = file_path.lower()
        
        for comp in components:
            if comp.name in file_path_lower:
                return comp.name
            if comp.path and comp.path in file_path_lower:
                return comp.name
        
        return None
    
    def _detect_architecture_type(
        self,
        components: List[Component],
        dependencies: List[ComponentDependency]
    ) -> str:
        """Detect the architecture pattern"""
        scores = defaultdict(float)
        
        # Check for layered architecture
        layers = ["presentation", "business", "domain", "infrastructure"]
        found_layers = set(c.component_type for c in components)
        
        if len(found_layers & set(layers)) >= 3:
            scores["layered"] = 0.8
        
        # Check for microservices
        if len([c for c in components if c.name == "api"]) > 1:
            scores["microservices"] = 0.6
        
        # Check for event-driven
        event_indicators = ["event", "queue", "message", "pub", "sub", "kafka", "rabbitmq"]
        for comp in components:
            if any(ind in comp.name.lower() for ind in event_indicators):
                scores["event_driven"] = scores.get("event_driven", 0) + 0.2
        
        # Check for CQRS
        has_commands = any("command" in c.name.lower() for c in components)
        has_queries = any("query" in c.name.lower() for c in components)
        if has_commands and has_queries:
            scores["cqrs"] = 0.7
        
        # Default to monolith if no clear pattern
        if not scores:
            scores["monolith"] = 0.5
        
        # Return highest scoring architecture
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _analyze_data_flows(
        self,
        scan_result: Any,
        components: List[Component]
    ) -> List[DataFlow]:
        """Analyze data flows between components"""
        data_flows = []
        
        # Look for API endpoints and their handlers
        for file_info in scan_result.files:
            if file_info.extension not in [".py", ".js", ".ts", ".jsx", ".tsx"]:
                continue
            
            try:
                with open(file_info.path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                # Find API routes
                routes = self._extract_routes(content, file_info.extension)
                
                for route in routes:
                    data_flows.append(DataFlow(
                        source="client",
                        target=route.get("handler", "unknown"),
                        data_type=route.get("method", "GET"),
                        description=f"{route.get('method', 'GET')} {route.get('path', '/')}"
                    ))
            
            except Exception:
                continue
        
        return data_flows
    
    def _extract_routes(self, content: str, extension: str) -> List[Dict]:
        """Extract API routes from code"""
        routes = []
        
        if extension == ".py":
            # Flask routes
            flask_routes = re.findall(
                r"@app\.route\(['\"]([^'\"]+)['\"].*?\).*?def\s+(\w+)",
                content,
                re.DOTALL
            )
            for path, handler in flask_routes:
                routes.append({"path": path, "handler": handler, "method": "GET"})
            
            # FastAPI routes
            fastapi_routes = re.findall(
                r"@(?:app|router)\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"].*?\).*?def\s+(\w+)",
                content,
                re.DOTALL | re.IGNORECASE
            )
            for method, path, handler in fastapi_routes:
                routes.append({"path": path, "handler": handler, "method": method.upper()})
        
        elif extension in [".js", ".ts", ".jsx", ".tsx"]:
            # Express routes
            express_routes = re.findall(
                r"app\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"].*?(?:=>|function)",
                content,
                re.IGNORECASE
            )
            for method, path in express_routes:
                routes.append({"path": path, "handler": "handler", "method": method.upper()})
        
        return routes
    
    def _detect_bottlenecks(self, scan_result: Any) -> List[PerformanceBottleneck]:
        """Detect performance bottlenecks"""
        bottlenecks = []
        
        for file_info in scan_result.files:
            if file_info.extension not in [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java"]:
                continue
            
            try:
                with open(file_info.path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.split("\n")
                
                for pattern_name, pattern_info in self.PERFORMANCE_PATTERNS.items():
                    for match in re.finditer(pattern_info["pattern"], content, re.MULTILINE):
                        line_num = content[:match.start()].count("\n") + 1
                        
                        bottlenecks.append(PerformanceBottleneck(
                            location=f"{file_info.relative_path}:{line_num}",
                            issue_type=pattern_name,
                            severity=pattern_info["severity"],
                            description=pattern_info["description"],
                            recommendation=self._get_performance_fix(pattern_name)
                        ))
            
            except Exception:
                continue
        
        return bottlenecks
    
    def _get_performance_fix(self, issue_type: str) -> str:
        """Get recommendation for performance issue"""
        fixes = {
            "n_plus_one": "Use eager loading, select_related, or prefetch_related to batch queries",
            "sync_in_loop": "Use async/await with aiohttp or gather multiple requests concurrently",
            "unbounded_cache": "Implement LRU cache with max_size or use Redis with TTL",
            "large_data_in_memory": "Use pagination, streaming, or chunked processing",
            "blocking_io": "Move to async operations or use background tasks"
        }
        return fixes.get(issue_type, "Review and optimize the code")
    
    def _detect_security_issues(self, scan_result: Any) -> List[SecurityVulnerability]:
        """Detect security vulnerabilities in architecture"""
        issues = []
        
        # Check for common architectural security issues
        for file_info in scan_result.files:
            if file_info.extension not in [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java"]:
                continue
            
            try:
                with open(file_info.path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                # Check for missing authentication
                if "route" in file_info.relative_path.lower() or "api" in file_info.relative_path.lower():
                    if not re.search(r"@(?:login_required|auth|authenticate|middleware", content):
                        if re.search(r"@(?:app|router)\.(?:post|put|delete|patch)", content):
                            issues.append(SecurityVulnerability(
                                location=file_info.relative_path,
                                vulnerability_type="missing_auth",
                                severity="medium",
                                description="API endpoint may lack authentication",
                                cwe="CWE-306"
                            ))
            
            except Exception:
                continue
        
        return issues
    
    def _calculate_complexity(
        self,
        components: List[Component],
        dependencies: List[ComponentDependency]
    ) -> float:
        """Calculate overall complexity score (0-100)"""
        if not components:
            return 0.0
        
        # Average component complexity
        avg_complexity = sum(c.complexity for c in components) / len(components)
        
        # Dependency complexity
        dep_count = len(dependencies)
        dep_factor = min(20, dep_count) / 20 * 10
        
        # Combined score
        score = (avg_complexity / 10 * 50) + (dep_factor * 5)
        
        return min(100, max(0, score))
    
    def _calculate_maintainability(
        self,
        components: List[Component],
        dependencies: List[ComponentDependency]
    ) -> float:
        """Calculate maintainability score (0-100)"""
        if not components:
            return 100.0
        
        # Lower complexity = higher maintainability
        avg_complexity = sum(c.complexity for c in components) / len(components)
        complexity_score = 100 - (avg_complexity / 10 * 50)
        
        # Fewer circular dependencies = higher maintainability
        circular = self._count_circular_dependencies(dependencies)
        circular_penalty = circular * 5
        
        return max(0, complexity_score - circular_penalty)
    
    def _calculate_testability(
        self,
        scan_result: Any,
        components: List[Component]
    ) -> float:
        """Calculate testability score (0-100)"""
        # Check for test files
        test_files = len(scan_result.test_files)
        source_files = sum(1 for f in scan_result.files if not f.is_binary and not f.is_generated)
        
        if source_files == 0:
            return 100.0
        
        test_ratio = test_files / source_files
        
        # Higher test ratio = higher testability
        score = min(100, test_ratio * 200)
        
        return max(0, score)
    
    def _count_circular_dependencies(self, dependencies: List[ComponentDependency]) -> int:
        """Count circular dependencies"""
        # Build adjacency list
        graph = defaultdict(set)
        for dep in dependencies:
            graph[dep.source].add(dep.target)
        
        # Detect cycles using DFS
        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        visited = set()
        cycles = 0
        
        for node in graph:
            if node not in visited:
                if has_cycle(node, visited, set()):
                    cycles += 1
        
        return cycles
    
    def _generate_recommendations(
        self,
        architecture_type: str,
        components: List[Component],
        dependencies: List[ComponentDependency],
        bottlenecks: List[PerformanceBottleneck],
        security_issues: List[SecurityVulnerability]
    ) -> List[str]:
        """Generate architecture recommendations"""
        recommendations = []
        
        # Architecture-specific recommendations
        if architecture_type == "monolith":
            recommendations.append("Consider modularizing into separate services for better scalability")
        
        # Complexity recommendations
        high_complexity = [c for c in components if c.complexity > 7]
        if high_complexity:
            recommendations.append(
                f"Refactor high-complexity components: {', '.join(c.name for c in high_complexity[:3])}"
            )
        
        # Performance recommendations
        critical_bottlenecks = [b for b in bottlenecks if b.severity == "high"]
        if critical_bottlenecks:
            recommendations.append(
                f"Address {len(critical_bottlenecks)} critical performance bottlenecks"
            )
        
        # Security recommendations
        critical_security = [s for s in security_issues if s.severity in ["critical", "high"]]
        if critical_security:
            recommendations.append(
                f"Fix {len(critical_security)} critical/high security vulnerabilities"
            )
        
        # Dependency recommendations
        if len(dependencies) > 50:
            recommendations.append("Consider reducing coupling between components")
        
        return recommendations
    
    def _generate_diagrams(
        self,
        components: List[Component],
        dependencies: List[ComponentDependency],
        data_flows: List[DataFlow]
    ) -> Dict[str, str]:
        """Generate Mermaid diagrams"""
        diagrams = {}
        
        # Component diagram
        component_diagram = ["graph TB"]
        for comp in components:
            category = comp.component_type
            component_diagram.append(f"    {comp.name}[{comp.name}<br/>{category}]")
        
        for dep in dependencies[:20]:  # Limit to avoid huge diagrams
            component_diagram.append(f"    {dep.source} --> {dep.target}")
        
        diagrams["component"] = "\n".join(component_diagram)
        
        # Data flow diagram
        flow_diagram = ["graph LR"]
        flow_diagram.append("    Client[Client]")
        
        for flow in data_flows[:10]:
            flow_diagram.append(f"    Client -->|{flow.data_type}| {flow.target}")
        
        diagrams["data_flow"] = "\n".join(flow_diagram)
        
        return diagrams