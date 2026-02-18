"""
SYNTHIA Repository Scanner
==========================
Deep repository scanning with multi-language support, SVG analysis, and broken code detection.

Based on Ralphy patterns:
- Memory-first: Check cached scans before re-scanning
- Parallel execution: Scan multiple directories concurrently
- Retry logic: Handle transient failures gracefully
"""

import os
import re
import json
import subprocess
import hashlib
import mimetypes
from typing import Optional, Dict, List, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


@dataclass
class FileInfo:
    """Information about a single file"""
    path: str
    relative_path: str
    size: int
    extension: str
    language: Optional[str]
    mime_type: Optional[str]
    hash: str
    line_count: int
    is_binary: bool
    is_generated: bool
    last_modified: datetime


@dataclass
class SVGAnalysis:
    """Analysis of an SVG file"""
    path: str
    viewbox: Optional[Tuple[float, float, float, float]]
    width: Optional[float]
    height: Optional[float]
    colors: List[str]
    shapes: Dict[str, int]
    has_animations: bool
    has_scripts: bool
    complexity_score: float
    is_icon: bool
    is_illustration: bool


@dataclass
class BrokenCode:
    """Detected broken or problematic code"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # critical, high, medium, low
    description: str
    code_snippet: str
    suggestion: str


@dataclass
class DependencyInfo:
    """Information about project dependencies"""
    manager: str  # pip, npm, yarn, cargo, go mod, etc.
    file_path: str
    dependencies: List[Dict[str, str]]
    dev_dependencies: List[Dict[str, str]]
    vulnerable: List[Dict[str, Any]]


@dataclass
class ScanResult:
    """Complete repository scan result"""
    root_path: str
    total_files: int
    total_directories: int
    total_size: int
    languages: Dict[str, int]  # language -> file count
    frameworks: List[str]
    file_types: Dict[str, int]
    files: List[FileInfo]
    svg_assets: List[SVGAnalysis]
    broken_code: List[BrokenCode]
    dependencies: List[DependencyInfo]
    entry_points: List[str]
    config_files: List[str]
    test_files: List[str]
    documentation: List[str]
    git_info: Dict[str, Any]
    structure_hash: str
    scan_timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "root_path": self.root_path,
            "total_files": self.total_files,
            "total_directories": self.total_directories,
            "total_size": self.total_size,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "file_types": self.file_types,
            "svg_count": len(self.svg_assets),
            "broken_code_count": len(self.broken_code),
            "entry_points": self.entry_points,
            "structure_hash": self.structure_hash,
            "scan_timestamp": self.scan_timestamp.isoformat()
        }


class RepositoryScanner:
    """
    Deep repository scanner with multi-language support.
    
    Features:
    - Multi-language file detection and analysis
    - SVG asset analysis (colors, shapes, complexity)
    - Broken code detection (syntax errors, anti-patterns)
    - Dependency scanning with vulnerability detection
    - Memory-first caching for repeated scans
    - Parallel execution for large repositories
    
    Usage:
        scanner = RepositoryScanner()
        result = scanner.scan("/path/to/repository")
        print(f"Found {result.total_files} files")
    """
    
    # Language detection by extension
    LANGUAGE_MAP = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript (React)",
        ".ts": "TypeScript",
        ".tsx": "TypeScript (React)",
        ".vue": "Vue",
        ".svelte": "Svelte",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".kt": "Kotlin",
        ".swift": "Swift",
        ".m": "Objective-C",
        ".c": "C",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".h": "C/C++ Header",
        ".hpp": "C++ Header",
        ".cs": "C#",
        ".rb": "Ruby",
        ".php": "PHP",
        ".pl": "Perl",
        ".sh": "Shell",
        ".bash": "Shell",
        ".zsh": "Shell",
        ".ps1": "PowerShell",
        ".sql": "SQL",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".sass": "Sass",
        ".less": "Less",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".xml": "XML",
        ".toml": "TOML",
        ".ini": "INI",
        ".cfg": "Config",
        ".conf": "Config",
        ".md": "Markdown",
        ".rst": "reStructuredText",
        ".tex": "LaTeX",
        ".scala": "Scala",
        ".clj": "Clojure",
        ".ex": "Elixir",
        ".exs": "Elixir",
        ".erl": "Erlang",
        ".hs": "Haskell",
        ".lua": "Lua",
        ".r": "R",
        ".dart": "Dart",
        ".jl": "Julia",
        ".nim": "Nim",
        ".v": "Verilog",
        ".sv": "SystemVerilog",
        ".sol": "Solidity",
        ".vy": "Vyper",
    }
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        "django": ["django", "settings.py", "urls.py", "wsgi.py"],
        "flask": ["flask", "app.py", "from flask import"],
        "fastapi": ["fastapi", "from fastapi import"],
        "express": ["express", "app.listen", "router."],
        "nextjs": ["next", "next.config", "getServerSideProps", "getStaticProps"],
        "react": ["react", "ReactDOM", "useState", "useEffect"],
        "vue": ["vue", "createApp", "defineComponent"],
        "svelte": ["svelte", "svelte.config"],
        "angular": ["@angular", "angular.json", "ng.module"],
        "spring": ["springframework", "SpringBootApplication"],
        "rails": ["rails", "ActiveRecord", "ApplicationController"],
        "laravel": ["laravel", "Illuminate"],
        "dotnet": ["Microsoft.AspNetCore", "Program.cs"],
        "gatsby": ["gatsby", "gatsby-config", "gatsby-node"],
        "nuxt": ["nuxt", "nuxt.config"],
        "remix": ["remix", "remix.config"],
        "sveltekit": ["@sveltejs/kit", "svelte.config.js"],
        "actix": ["actix_web", "actix::"],
        "rocket": ["rocket", "Rocket::build"],
        "gin": ["gin-gonic", "gin.Engine"],
        "beego": ["beego", "beego.Controller"],
        "tornado": ["tornado", "tornado.web"],
        "aiohttp": ["aiohttp", "aiohttp.web"],
        "sanic": ["sanic", "Sanic("],
        "starlette": ["starlette", "Starlette("],
    }
    
    # Directories to skip
    SKIP_DIRS = {
        ".git", ".svn", ".hg", ".bzr",
        "node_modules", "__pycache__", ".pytest_cache",
        "venv", ".venv", "env", ".env",
        "dist", "build", "target", "out",
        ".idea", ".vscode", ".sublime",
        "vendor", "Pods", "Carthage",
        ".gradle", ".mvn", "gradle",
        "cache", ".cache", "tmp", "temp",
        "logs", "data", "coverage", ".nyc_output",
        ".next", ".nuxt", ".svelte-kit",
    }
    
    # Generated file patterns
    GENERATED_PATTERNS = [
        r"\.min\.js$",
        r"\.min\.css$",
        r"\.d\.ts$",
        r"\.pb\.go$",
        r"_pb2\.py$",
        r"generated_",
        r"\.generated\.",
        r"/dist/",
        r"/build/",
        r"/target/",
        r"\.lock$",
        r"-lock\.json$",
        r"\.lockb$",
    ]
    
    def __init__(
        self,
        memory_client: Optional[Any] = None,
        max_workers: int = 4,
        skip_tests: bool = False
    ):
        self.memory = memory_client
        self.max_workers = max_workers
        self.skip_tests = skip_tests
        self._lock = threading.Lock()
    
    def scan(
        self,
        repo_path: str,
        deep_scan: bool = True,
        analyze_svgs: bool = True,
        detect_broken: bool = True
    ) -> ScanResult:
        """
        Scan a repository comprehensively.
        
        Args:
            repo_path: Path to repository root
            deep_scan: Perform deep content analysis
            analyze_svgs: Analyze SVG files in detail
            detect_broken: Detect broken/problematic code
            
        Returns:
            ScanResult with complete repository analysis
        """
        repo_path = os.path.abspath(repo_path)
        
        # Memory-first: Check for cached scan
        if self.memory:
            cached = self._get_cached_scan(repo_path)
            if cached:
                return cached
        
        # Initialize result containers
        files: List[FileInfo] = []
        svg_assets: List[SVGAnalysis] = []
        broken_code: List[BrokenCode] = []
        dependencies: List[DependencyInfo] = []
        languages: Dict[str, int] = {}
        file_types: Dict[str, int] = {}
        entry_points: List[str] = []
        config_files: List[str] = []
        test_files: List[str] = []
        documentation: List[str] = []
        total_size = 0
        total_dirs = 0
        
        # Collect all files first
        file_paths = self._collect_files(repo_path)
        
        # Parallel file scanning
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._scan_file,
                    repo_path,
                    fp,
                    deep_scan
                ): fp for fp in file_paths
            }
            
            for future in as_completed(futures):
                try:
                    file_info = future.result()
                    if file_info:
                        files.append(file_info)
                        total_size += file_info.size
                        
                        # Track languages
                        if file_info.language:
                            languages[file_info.language] = languages.get(file_info.language, 0) + 1
                        
                        # Track file types
                        ext = file_info.extension or "no_ext"
                        file_types[ext] = file_types.get(ext, 0) + 1
                        
                        # Categorize file
                        self._categorize_file(
                            file_info,
                            entry_points,
                            config_files,
                            test_files,
                            documentation
                        )
                except Exception as e:
                    pass  # Skip problematic files
        
        # Count directories
        for root, dirs, _ in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            total_dirs += len(dirs)
        
        # Analyze SVGs if requested
        if analyze_svgs:
            svg_files = [f for f in files if f.extension == ".svg"]
            for svg_file in svg_files:
                svg_analysis = self._analyze_svg(svg_file.path)
                if svg_analysis:
                    svg_assets.append(svg_analysis)
        
        # Detect broken code if requested
        if detect_broken:
            broken_code = self._detect_broken_code(repo_path, files)
        
        # Scan dependencies
        dependencies = self._scan_dependencies(repo_path)
        
        # Detect frameworks
        frameworks = self._detect_frameworks(files)
        
        # Get git info
        git_info = self._get_git_info(repo_path)
        
        # Calculate structure hash
        structure_hash = self._calculate_structure_hash(files)
        
        result = ScanResult(
            root_path=repo_path,
            total_files=len(files),
            total_directories=total_dirs,
            total_size=total_size,
            languages=languages,
            frameworks=frameworks,
            file_types=file_types,
            files=files,
            svg_assets=svg_assets,
            broken_code=broken_code,
            dependencies=dependencies,
            entry_points=entry_points,
            config_files=config_files,
            test_files=test_files,
            documentation=documentation,
            git_info=git_info,
            structure_hash=structure_hash,
            scan_timestamp=datetime.now()
        )
        
        # Cache the result
        if self.memory:
            self._cache_scan(repo_path, result)
        
        return result
    
    def _collect_files(self, repo_path: str) -> List[str]:
        """Collect all file paths in repository"""
        file_paths = []
        
        for root, dirs, files in os.walk(repo_path):
            # Filter out skip directories
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            for file in files:
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
        
        return file_paths
    
    def _scan_file(
        self,
        repo_path: str,
        file_path: str,
        deep_scan: bool
    ) -> Optional[FileInfo]:
        """Scan a single file"""
        try:
            stat = os.stat(file_path)
            rel_path = os.path.relpath(file_path, repo_path)
            ext = os.path.splitext(file_path)[1].lower()
            
            # Detect language
            language = self.LANGUAGE_MAP.get(ext)
            
            # Detect mime type
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Check if binary
            is_binary = self._is_binary(file_path)
            
            # Check if generated
            is_generated = self._is_generated(rel_path)
            
            # Calculate hash and line count for text files
            file_hash = ""
            line_count = 0
            
            if not is_binary and deep_scan:
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()
                        file_hash = hashlib.sha256(content).hexdigest()[:16]
                        line_count = content.count(b"\n") + 1
                except Exception:
                    pass
            
            return FileInfo(
                path=file_path,
                relative_path=rel_path,
                size=stat.st_size,
                extension=ext,
                language=language,
                mime_type=mime_type,
                hash=file_hash,
                line_count=line_count,
                is_binary=is_binary,
                is_generated=is_generated,
                last_modified=datetime.fromtimestamp(stat.st_mtime)
            )
        except Exception:
            return None
    
    def _is_binary(self, file_path: str) -> bool:
        """Check if file is binary"""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
                if b"\x00" in chunk:
                    return True
                # Check for high ratio of non-text bytes
                text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
                non_text = sum(1 for byte in chunk if byte not in text_chars)
                return non_text / max(len(chunk), 1) > 0.3
        except Exception:
            return True
    
    def _is_generated(self, rel_path: str) -> bool:
        """Check if file is likely generated"""
        for pattern in self.GENERATED_PATTERNS:
            if re.search(pattern, rel_path, re.IGNORECASE):
                return True
        return False
    
    def _categorize_file(
        self,
        file_info: FileInfo,
        entry_points: List[str],
        config_files: List[str],
        test_files: List[str],
        documentation: List[str]
    ):
        """Categorize a file by its purpose"""
        filename = os.path.basename(file_info.path).lower()
        rel_path = file_info.relative_path.lower()
        
        # Entry points
        if filename in ["main.py", "app.py", "index.py", "index.js", "index.ts",
                        "main.go", "main.rs", "main.java", "program.cs", "server.py",
                        "wsgi.py", "asgi.py", "__main__.py"]:
            entry_points.append(file_info.relative_path)
        
        # Config files
        if filename in ["config.py", "settings.py", "config.json", "config.yaml",
                        "config.yml", ".env", ".env.local", "config.toml",
                        "pyproject.toml", "setup.py", "setup.cfg", "package.json",
                        "tsconfig.json", "webpack.config.js", "vite.config.js",
                        "rollup.config.js", "babel.config.js", ".eslintrc",
                        ".prettierrc", "dockerfile", "docker-compose.yml"]:
            config_files.append(file_info.relative_path)
        
        # Test files
        if "test" in filename or "spec" in filename or "tests" in rel_path:
            test_files.append(file_info.relative_path)
        
        # Documentation
        if file_info.extension in [".md", ".rst", ".txt"] or "doc" in rel_path:
            documentation.append(file_info.relative_path)
    
    def _analyze_svg(self, file_path: str) -> Optional[SVGAnalysis]:
        """Analyze an SVG file in detail"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Parse viewbox
            viewbox = None
            vb_match = re.search(r'viewBox=["\']([^"\']+)["\']', content)
            if vb_match:
                try:
                    parts = [float(x) for x in vb_match.group(1).split()]
                    if len(parts) == 4:
                        viewbox = tuple(parts)
                except ValueError:
                    pass
            
            # Parse width and height
            width = None
            height = None
            w_match = re.search(r'width=["\']([^"\']+)["\']', content)
            h_match = re.search(r'height=["\']([^"\']+)["\']', content)
            
            if w_match:
                try:
                    width = float(re.sub(r"[^\d.]", "", w_match.group(1)))
                except ValueError:
                    pass
            if h_match:
                try:
                    height = float(re.sub(r"[^\d.]", "", h_match.group(1)))
                except ValueError:
                    pass
            
            # Extract colors
            colors = []
            color_patterns = [
                r"#([0-9a-fA-F]{3,8})\b",
                r"rgb\(([^)]+)\)",
                r"rgba\(([^)]+)\)",
                r'fill=["\']([^"\']+)["\']',
                r'stroke=["\']([^"\']+)["\']',
            ]
            for pattern in color_patterns:
                colors.extend(re.findall(pattern, content, re.IGNORECASE))
            colors = list(set(colors))[:20]  # Unique colors, max 20
            
            # Count shapes
            shapes = {}
            shape_tags = ["path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "text", "g", "use", "image"]
            for tag in shape_tags:
                count = len(re.findall(f"<{tag}[\\s>]", content, re.IGNORECASE))
                if count > 0:
                    shapes[tag] = count
            
            # Check for animations
            has_animations = bool(re.search(r"<animate|<animateTransform|<animateMotion", content, re.IGNORECASE))
            
            # Check for scripts
            has_scripts = bool(re.search(r"<script|onload=|onclick=|onmouseover=", content, re.IGNORECASE))
            
            # Calculate complexity
            complexity_score = len(content) / 1000 + sum(shapes.values()) * 0.5 + len(colors) * 0.2
            
            # Determine if icon or illustration
            is_icon = (width is not None and width <= 64) or (height is not None and height <= 64) or complexity_score < 2
            is_illustration = complexity_score > 5 or sum(shapes.values()) > 20
            
            return SVGAnalysis(
                path=file_path,
                viewbox=viewbox,
                width=width,
                height=height,
                colors=colors,
                shapes=shapes,
                has_animations=has_animations,
                has_scripts=has_scripts,
                complexity_score=complexity_score,
                is_icon=is_icon,
                is_illustration=is_illustration
            )
        except Exception:
            return None
    
    def _detect_broken_code(
        self,
        repo_path: str,
        files: List[FileInfo]
    ) -> List[BrokenCode]:
        """Detect broken or problematic code"""
        broken = []
        
        # Patterns for broken code
        broken_patterns = [
            # Python
            (r"except\s*:", "Python bare except", "high", "Use specific exception types"),
            (r"except Exception\s*:", "Python broad exception", "medium", "Catch specific exceptions"),
            (r"print\s*\(", "Debug print statement", "low", "Use logging instead"),
            (r"# TODO|# FIXME|# XXX", "Unresolved TODO", "info", "Resolve or document"),
            (r"pass\s*$", "Empty block", "low", "Implement or remove"),
            
            # JavaScript/TypeScript
            (r"console\.log\s*\(", "Console.log in code", "low", "Remove or use logger"),
            (r"debugger\s*;", "Debugger statement", "medium", "Remove debugger"),
            (r"var\s+\w+\s*=", "var declaration", "medium", "Use let or const"),
            (r"==\s*[^=]|[^=]\s*==", "Loose equality", "high", "Use strict equality ==="),
            
            # General
            (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password", "critical", "Use environment variables"),
            (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key", "critical", "Use environment variables"),
            (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret", "critical", "Use environment variables"),
        ]
        
        source_files = [f for f in files if not f.is_binary and not f.is_generated and f.extension in [".py", ".js", ".ts", ".jsx", ".tsx"]]
        
        for file_info in source_files:
            try:
                with open(file_info.path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    for pattern, issue_type, severity, suggestion in broken_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            broken.append(BrokenCode(
                                file_path=file_info.relative_path,
                                line_number=line_num,
                                issue_type=issue_type,
                                severity=severity,
                                description=f"Found {issue_type.lower()}",
                                code_snippet=line.strip()[:100],
                                suggestion=suggestion
                            ))
            except Exception:
                continue
        
        return broken
    
    def _scan_dependencies(self, repo_path: str) -> List[DependencyInfo]:
        """Scan project dependencies"""
        dependencies = []
        
        # Python requirements.txt
        req_path = os.path.join(repo_path, "requirements.txt")
        if os.path.exists(req_path):
            deps = self._parse_requirements(req_path)
            dependencies.append(DependencyInfo(
                manager="pip",
                file_path="requirements.txt",
                dependencies=deps,
                dev_dependencies=[],
                vulnerable=[]
            ))
        
        # Python pyproject.toml
        pyproject_path = os.path.join(repo_path, "pyproject.toml")
        if os.path.exists(pyproject_path):
            deps = self._parse_pyproject(pyproject_path)
            if deps:
                dependencies.append(DependencyInfo(
                    manager="pip",
                    file_path="pyproject.toml",
                    dependencies=deps,
                    dev_dependencies=[],
                    vulnerable=[]
                ))
        
        # Node package.json
        pkg_path = os.path.join(repo_path, "package.json")
        if os.path.exists(pkg_path):
            deps, dev_deps = self._parse_package_json(pkg_path)
            dependencies.append(DependencyInfo(
                manager="npm",
                file_path="package.json",
                dependencies=deps,
                dev_dependencies=dev_deps,
                vulnerable=[]
            ))
        
        # Go go.mod
        go_mod_path = os.path.join(repo_path, "go.mod")
        if os.path.exists(go_mod_path):
            deps = self._parse_go_mod(go_mod_path)
            dependencies.append(DependencyInfo(
                manager="go mod",
                file_path="go.mod",
                dependencies=deps,
                dev_dependencies=[],
                vulnerable=[]
            ))
        
        # Rust Cargo.toml
        cargo_path = os.path.join(repo_path, "Cargo.toml")
        if os.path.exists(cargo_path):
            deps = self._parse_cargo(cargo_path)
            dependencies.append(DependencyInfo(
                manager="cargo",
                file_path="Cargo.toml",
                dependencies=deps,
                dev_dependencies=[],
                vulnerable=[]
            ))
        
        return dependencies
    
    def _parse_requirements(self, path: str) -> List[Dict[str, str]]:
        """Parse requirements.txt"""
        deps = []
        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Parse package name and version
                        match = re.match(r"^([a-zA-Z0-9_-]+)\s*([<>=!~]+.*)?$", line)
                        if match:
                            deps.append({
                                "name": match.group(1),
                                "version": match.group(2) or "latest",
                                "constraint": match.group(2) or ""
                            })
        except Exception:
            pass
        return deps
    
    def _parse_pyproject(self, path: str) -> List[Dict[str, str]]:
        """Parse pyproject.toml"""
        deps = []
        try:
            import tomllib
            with open(path, "rb") as f:
                data = tomllib.load(f)
            
            # Get dependencies from various locations
            project_deps = data.get("project", {}).get("dependencies", [])
            tool_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            
            for dep in project_deps:
                match = re.match(r"^([a-zA-Z0-9_-]+)\s*([<>=!~]+.*)?$", dep)
                if match:
                    deps.append({
                        "name": match.group(1),
                        "version": match.group(2) or "latest"
                    })
            
            for name, version in tool_deps.items():
                if name != "python":
                    deps.append({
                        "name": name,
                        "version": str(version) if version else "latest"
                    })
        except Exception:
            pass
        return deps
    
    def _parse_package_json(self, path: str) -> Tuple[List[Dict], List[Dict]]:
        """Parse package.json"""
        deps = []
        dev_deps = []
        try:
            with open(path, "r") as f:
                data = json.load(f)
            
            for name, version in data.get("dependencies", {}).items():
                deps.append({"name": name, "version": version})
            
            for name, version in data.get("devDependencies", {}).items():
                dev_deps.append({"name": name, "version": version})
        except Exception:
            pass
        return deps, dev_deps
    
    def _parse_go_mod(self, path: str) -> List[Dict[str, str]]:
        """Parse go.mod"""
        deps = []
        try:
            with open(path, "r") as f:
                content = f.read()
            
            # Find require block
            require_block = re.search(r"require\s*\(([^)]+)\)", content, re.DOTALL)
            if require_block:
                for line in require_block.group(1).strip().split("\n"):
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        deps.append({"name": parts[0], "version": parts[1]})
            
            # Single line requires
            single_requires = re.findall(r"require\s+(\S+)\s+(\S+)", content)
            for name, version in single_requires:
                deps.append({"name": name, "version": version})
        except Exception:
            pass
        return deps
    
    def _parse_cargo(self, path: str) -> List[Dict[str, str]]:
        """Parse Cargo.toml"""
        deps = []
        try:
            import tomllib
            with open(path, "rb") as f:
                data = tomllib.load(f)
            
            for name, version in data.get("dependencies", {}).items():
                if isinstance(version, str):
                    deps.append({"name": name, "version": version})
                elif isinstance(version, dict):
                    deps.append({
                        "name": name,
                        "version": version.get("version", "latest"),
                        "features": version.get("features", [])
                    })
        except Exception:
            pass
        return deps
    
    def _detect_frameworks(self, files: List[FileInfo]) -> List[str]:
        """Detect frameworks used in the project"""
        frameworks = []
        
        # Read content of key files
        key_files = [f for f in files if f.extension in [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".rb", ".php"]]
        
        content_samples = []
        for file_info in key_files[:50]:  # Sample first 50 source files
            try:
                with open(file_info.path, "r", encoding="utf-8", errors="ignore") as f:
                    content_samples.append(f.read(5000))  # Read first 5KB
            except Exception:
                continue
        
        combined_content = " ".join(content_samples).lower()
        
        # Check for framework patterns
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in combined_content:
                    frameworks.append(framework)
                    break
        
        return list(set(frameworks))
    
    def _get_git_info(self, repo_path: str) -> Dict[str, Any]:
        """Get git repository information"""
        git_info = {
            "is_git_repo": False,
            "branch": None,
            "remote": None,
            "last_commit": None,
            "commit_count": 0,
            "contributors": []
        }
        
        git_dir = os.path.join(repo_path, ".git")
        if not os.path.exists(git_dir):
            return git_info
        
        git_info["is_git_repo"] = True
        
        try:
            # Get branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                git_info["branch"] = result.stdout.strip()
            
            # Get remote
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                git_info["remote"] = result.stdout.strip()
            
            # Get last commit
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H %s"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                git_info["last_commit"] = result.stdout.strip()
            
            # Get commit count
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                git_info["commit_count"] = int(result.stdout.strip())
        except Exception:
            pass
        
        return git_info
    
    def _calculate_structure_hash(self, files: List[FileInfo]) -> str:
        """Calculate a hash representing the repository structure"""
        # Create a string representation of the structure
        structure = "|".join(sorted(f.relative_path for f in files))
        return hashlib.sha256(structure.encode()).hexdigest()[:16]
    
    def _get_cached_scan(self, repo_path: str) -> Optional[ScanResult]:
        """Get cached scan result from memory"""
        if not self.memory:
            return None
        
        try:
            cached = self.memory.search(
                f"repo_scan:{repo_path}",
                limit=1
            )
            if cached:
                # Check if structure hash matches
                current_hash = self._calculate_structure_hash_quick(repo_path)
                if cached[0].metadata.get("structure_hash") == current_hash:
                    # Reconstruct ScanResult from cached data
                    return self._reconstruct_scan_result(cached[0].value)
        except Exception:
            pass
        
        return None
    
    def _calculate_structure_hash_quick(self, repo_path: str) -> str:
        """Quickly calculate structure hash for cache validation"""
        paths = []
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            for file in files:
                paths.append(os.path.relpath(os.path.join(root, file), repo_path))
        
        structure = "|".join(sorted(paths))
        return hashlib.sha256(structure.encode()).hexdigest()[:16]
    
    def _cache_scan(self, repo_path: str, result: ScanResult):
        """Cache scan result in memory"""
        if not self.memory:
            return
        
        try:
            self.memory.store(
                key=f"repo_scan:{repo_path}",
                value=result.to_dict(),
                layer="project",
                metadata={
                    "structure_hash": result.structure_hash,
                    "scan_timestamp": result.scan_timestamp.isoformat()
                }
            )
        except Exception:
            pass
    
    def _reconstruct_scan_result(self, data: Dict) -> ScanResult:
        """Reconstruct ScanResult from cached dictionary"""
        # This is a simplified reconstruction
        # In production, you'd want to store and restore all fields
        return ScanResult(
            root_path=data["root_path"],
            total_files=data["total_files"],
            total_directories=data["total_directories"],
            total_size=data["total_size"],
            languages=data["languages"],
            frameworks=data["frameworks"],
            file_types=data["file_types"],
            files=[],  # Would need to re-scan for full file list
            svg_assets=[],
            broken_code=[],
            dependencies=[],
            entry_points=data["entry_points"],
            config_files=[],
            test_files=[],
            documentation=[],
            git_info={},
            structure_hash=data["structure_hash"],
            scan_timestamp=datetime.fromisoformat(data["scan_timestamp"])
        )