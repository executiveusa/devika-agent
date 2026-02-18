"""
SYNTHIA Architect Agent
=======================
Designs system architecture and component relationships.

Responsibilities:
- Analyze codebase structure
- Design component relationships
- Identify architectural patterns
- Generate architecture diagrams
- Plan refactoring strategies
- Ensure scalability considerations
"""

import os
import json
import re
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Component:
    """Represents a system component"""
    name: str
    type: str  # module, class, function, api, database, etc.
    path: str
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchitectureAnalysis:
    """Result of architecture analysis"""
    components: List[Component]
    dependency_graph: Dict[str, List[str]]
    layers: Dict[str, List[str]]
    patterns: List[str]
    issues: List[str]
    recommendations: List[str]
    diagram_mermaid: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class Architect:
    """
    Architecture analysis and design agent.
    
    Analyzes codebases to understand structure, identify patterns,
    and provide architectural recommendations.
    
    Usage:
        architect = Architect()
        analysis = architect.analyze("/path/to/project")
        print(analysis.diagram_mermaid)
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
        self._component_cache: Dict[str, Component] = {}
    
    def execute(self, context: Any, **kwargs) -> Dict:
        """Execute architecture analysis"""
        project_path = kwargs.get("project_path") or context.metadata.get("project_path")
        
        if not project_path:
            return {
                "output": "No project path provided for architecture analysis",
                "errors": ["Missing project_path"]
            }
        
        analysis = self.analyze(project_path)
        
        return {
            "output": f"Analyzed {len(analysis.components)} components, found {len(analysis.patterns)} patterns",
            "files_modified": [],
            "files_created": [],
            "metadata": {
                "components": [c.__dict__ for c in analysis.components],
                "dependency_graph": analysis.dependency_graph,
                "patterns": analysis.patterns,
                "issues": analysis.issues,
                "recommendations": analysis.recommendations,
                "diagram": analysis.diagram_mermaid
            }
        }
    
    def analyze(self, project_path: str) -> ArchitectureAnalysis:
        """
        Analyze project architecture.
        
        Args:
            project_path: Path to project root
            
        Returns:
            ArchitectureAnalysis with components, graph, and recommendations
        """
        self._component_cache.clear()
        
        # Scan for components
        components = self._scan_components(project_path)
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(components)
        
        # Identify layers
        layers = self._identify_layers(components)
        
        # Detect patterns
        patterns = self._detect_patterns(components, dependency_graph)
        
        # Find issues
        issues = self._find_issues(components, dependency_graph)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues, patterns)
        
        # Generate diagram
        diagram = self._generate_mermaid_diagram(components, dependency_graph, layers)
        
        return ArchitectureAnalysis(
            components=components,
            dependency_graph=dependency_graph,
            layers=layers,
            patterns=patterns,
            issues=issues,
            recommendations=recommendations,
            diagram_mermaid=diagram
        )
    
    def _scan_components(self, project_path: str) -> List[Component]:
        """Scan project for components"""
        components = []
        
        for root, dirs, files in os.walk(project_path):
            # Skip hidden and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in [
                "node_modules", "__pycache__", "venv", ".venv", "dist", "build",
                ".git", "data", "logs", "cache"
            ]]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_path)
                
                # Analyze based on file type
                if file.endswith(".py"):
                    component = self._analyze_python_file(file_path, rel_path)
                    if component:
                        components.append(component)
                elif file.endswith((".js", ".ts", ".jsx", ".tsx")):
                    component = self._analyze_js_file(file_path, rel_path)
                    if component:
                        components.append(component)
                elif file.endswith(".go"):
                    component = self._analyze_go_file(file_path, rel_path)
                    if component:
                        components.append(component)
        
        return components
    
    def _analyze_python_file(self, file_path: str, rel_path: str) -> Optional[Component]:
        """Analyze Python file for components"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return None
        
        # Extract imports
        imports = re.findall(r"^(?:from|import)\s+(\S+)", content, re.MULTILINE)
        
        # Extract classes
        classes = re.findall(r"class\s+(\w+)", content)
        
        # Extract functions
        functions = re.findall(r"def\s+(\w+)", content)
        
        # Determine component type
        if classes:
            comp_type = "module" if len(classes) > 1 else "class"
        elif functions:
            comp_type = "module"
        else:
            comp_type = "module"
        
        name = Path(file_path).stem
        if name == "__init__":
            name = os.path.dirname(rel_path).replace(os.sep, ".") or "root"
        
        return Component(
            name=name,
            type=comp_type,
            path=rel_path,
            dependencies=imports,
            interfaces=classes + functions,
            metadata={
                "language": "python",
                "class_count": len(classes),
                "function_count": len(functions)
            }
        )
    
    def _analyze_js_file(self, file_path: str, rel_path: str) -> Optional[Component]:
        """Analyze JavaScript/TypeScript file for components"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return None
        
        # Extract imports
        imports = re.findall(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", content)
        imports += re.findall(r"require\(['\"]([^'\"]+)['\"]\)", content)
        
        # Extract exports
        exports = re.findall(r"export\s+(?:default\s+)?(?:class|function|const|let)\s+(\w+)", content)
        
        # Extract classes
        classes = re.findall(r"class\s+(\w+)", content)
        
        # Extract functions
        functions = re.findall(r"function\s+(\w+)", content)
        functions += re.findall(r"const\s+(\w+)\s*=\s*(?:async\s*)?\(", content)
        
        # Determine component type
        if classes:
            comp_type = "component" if "Component" in content or "React" in content else "class"
        elif exports:
            comp_type = "module"
        else:
            comp_type = "module"
        
        name = Path(file_path).stem
        
        return Component(
            name=name,
            type=comp_type,
            path=rel_path,
            dependencies=imports,
            interfaces=exports,
            metadata={
                "language": "typescript" if file_path.endswith(".ts") or file_path.endswith(".tsx") else "javascript",
                "class_count": len(classes),
                "function_count": len(functions)
            }
        )
    
    def _analyze_go_file(self, file_path: str, rel_path: str) -> Optional[Component]:
        """Analyze Go file for components"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return None
        
        # Extract imports
        imports = re.findall(r'import\s+(?:\(\s*"?([^")]+)"?\s*\)|"([^"]+)")', content)
        imports = [i[0] or i[1] for i in imports if i]
        
        # Extract structs
        structs = re.findall(r"type\s+(\w+)\s+struct", content)
        
        # Extract interfaces
        interfaces = re.findall(r"type\s+(\w+)\s+interface", content)
        
        # Extract functions
        functions = re.findall(r"func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)", content)
        
        name = Path(file_path).stem
        
        return Component(
            name=name,
            type="package",
            path=rel_path,
            dependencies=imports,
            interfaces=structs + interfaces,
            metadata={
                "language": "go",
                "struct_count": len(structs),
                "interface_count": len(interfaces),
                "function_count": len(functions)
            }
        )
    
    def _build_dependency_graph(self, components: List[Component]) -> Dict[str, List[str]]:
        """Build dependency graph from components"""
        graph = {}
        
        for comp in components:
            graph[comp.name] = comp.dependencies
            
            # Track dependents
            for dep in comp.dependencies:
                if dep not in graph:
                    graph[dep] = []
        
        return graph
    
    def _identify_layers(self, components: List[Component]) -> Dict[str, List[str]]:
        """Identify architectural layers"""
        layers = {
            "presentation": [],
            "business": [],
            "data": [],
            "infrastructure": [],
            "other": []
        }
        
        layer_patterns = {
            "presentation": ["ui", "view", "component", "page", "route", "controller", "api"],
            "business": ["service", "logic", "domain", "usecase", "interactor", "agent"],
            "data": ["model", "entity", "repository", "dao", "schema", "db", "store"],
            "infrastructure": ["config", "util", "helper", "common", "lib", "core"]
        }
        
        for comp in components:
            path_lower = comp.path.lower()
            name_lower = comp.name.lower()
            
            assigned = False
            for layer, patterns in layer_patterns.items():
                if any(p in path_lower or p in name_lower for p in patterns):
                    layers[layer].append(comp.name)
                    assigned = True
                    break
            
            if not assigned:
                layers["other"].append(comp.name)
        
        return layers
    
    def _detect_patterns(
        self,
        components: List[Component],
        dependency_graph: Dict[str, List[str]]
    ) -> List[str]:
        """Detect architectural patterns"""
        patterns = []
        
        # Check for MVC
        has_model = any("model" in c.name.lower() or "entity" in c.name.lower() for c in components)
        has_view = any("view" in c.name.lower() or "component" in c.name.lower() for c in components)
        has_controller = any("controller" in c.name.lower() or "route" in c.name.lower() for c in components)
        
        if has_model and has_view and has_controller:
            patterns.append("MVC (Model-View-Controller)")
        
        # Check for Layered Architecture
        layer_count = sum(1 for layer in ["presentation", "business", "data"] 
                        if any(layer in c.path.lower() for c in components))
        if layer_count >= 2:
            patterns.append("Layered Architecture")
        
        # Check for Repository Pattern
        has_repo = any("repository" in c.name.lower() or "repo" in c.name.lower() for c in components)
        if has_repo:
            patterns.append("Repository Pattern")
        
        # Check for Service Layer
        has_service = any("service" in c.name.lower() for c in components)
        if has_service:
            patterns.append("Service Layer")
        
        # Check for Dependency Injection
        has_di = any("inject" in c.name.lower() or "container" in c.name.lower() for c in components)
        if has_di:
            patterns.append("Dependency Injection")
        
        # Check for Agent Pattern (SYNTHIA-specific)
        has_agent = any("agent" in c.name.lower() for c in components)
        if has_agent:
            patterns.append("Agent-Based Architecture")
        
        return patterns
    
    def _find_issues(
        self,
        components: List[Component],
        dependency_graph: Dict[str, List[str]]
    ) -> List[str]:
        """Find architectural issues"""
        issues = []
        
        # Check for circular dependencies
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in dependency_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in dependency_graph:
            if node not in visited:
                if has_cycle(node):
                    issues.append("Circular dependency detected")
                    break
        
        # Check for god files (too many exports)
        for comp in components:
            if len(comp.interfaces) > 20:
                issues.append(f"God file detected: {comp.name} has {len(comp.interfaces)} exports")
        
        # Check for deep nesting
        for comp in components:
            depth = comp.path.count(os.sep)
            if depth > 5:
                issues.append(f"Deep nesting detected: {comp.path} (depth: {depth})")
        
        # Check for missing tests
        has_tests = any("test" in c.name.lower() or "spec" in c.name.lower() for c in components)
        if not has_tests:
            issues.append("No test files detected")
        
        return issues
    
    def _generate_recommendations(
        self,
        issues: List[str],
        patterns: List[str]
    ) -> List[str]:
        """Generate architectural recommendations"""
        recommendations = []
        
        for issue in issues:
            if "Circular dependency" in issue:
                recommendations.append("Refactor to eliminate circular dependencies using dependency inversion")
            elif "God file" in issue:
                recommendations.append("Split large files into smaller, focused modules")
            elif "Deep nesting" in issue:
                recommendations.append("Flatten directory structure for better discoverability")
            elif "No test" in issue:
                recommendations.append("Add test coverage for critical components")
        
        # Pattern-based recommendations
        if "Agent-Based Architecture" in patterns:
            recommendations.append("Consider adding agent orchestration layer for coordination")
        
        if "Layered Architecture" not in patterns and len(patterns) < 2:
            recommendations.append("Consider adopting a layered architecture for better separation of concerns")
        
        return recommendations
    
    def _generate_mermaid_diagram(
        self,
        components: List[Component],
        dependency_graph: Dict[str, List[str]],
        layers: Dict[str, List[str]]
    ) -> str:
        """Generate Mermaid diagram of architecture"""
        lines = ["graph TB"]
        
        # Add layer subgraphs
        layer_colors = {
            "presentation": "#E1F5FE",
            "business": "#FFF3E0",
            "data": "#E8F5E9",
            "infrastructure": "#F3E5F5",
            "other": "#ECEFF1"
        }
        
        for layer, comp_names in layers.items():
            if comp_names:
                lines.append(f"    subgraph {layer}[{layer.title()} Layer]")
                for name in comp_names[:10]:  # Limit to 10 per layer
                    safe_name = name.replace("-", "_").replace(".", "_")
                    lines.append(f"        {safe_name}[{name}]")
                if len(comp_names) > 10:
                    lines.append(f"        more[... and {len(comp_names) - 10} more]")
                lines.append("    end")
        
        # Add key dependencies (limit to avoid clutter)
        dep_count = 0
        for comp_name, deps in dependency_graph.items():
            if dep_count >= 20:
                break
            for dep in deps[:3]:  # Max 3 deps per component
                if dep in [c.name for c in components]:
                    safe_comp = comp_name.replace("-", "_").replace(".", "_")
                    safe_dep = dep.replace("-", "_").replace(".", "_")
                    lines.append(f"    {safe_comp} --> {safe_dep}")
                    dep_count += 1
                    if dep_count >= 20:
                        break
        
        return "\n".join(lines)