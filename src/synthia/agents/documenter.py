"""
SYNTHIA Documenter Agent
========================
Documentation generation and management agent.

Responsibilities:
- Generate README files
- Create API documentation
- Write code comments
- Generate changelogs
- Create user guides
- Maintain documentation consistency
"""

import os
import re
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class DocumentationSection:
    """A section of documentation"""
    title: str
    content: str
    level: int = 1
    subsections: List["DocumentationSection"] = field(default_factory=list)


@dataclass
class DocumentationResult:
    """Result of documentation generation"""
    readme: str
    api_docs: Dict[str, str]
    changelog: str
    contributing: str
    license_text: str
    files_created: List[str] = field(default_factory=list)


class Documenter:
    """
    Documentation generation agent.
    
    Creates comprehensive documentation for projects.
    
    Usage:
        documenter = Documenter()
        docs = documenter.generate("/path/to/project")
        print(docs.readme)
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
    
    def execute(self, context: Any, **kwargs) -> Dict:
        """Execute documentation generation"""
        project_path = kwargs.get("project_path") or context.metadata.get("project_path")
        project_name = kwargs.get("project_name", "Project")
        
        if not project_path:
            return {
                "output": "No project path provided for documentation",
                "errors": ["Missing project_path"]
            }
        
        docs = self.generate(project_path, project_name)
        
        return {
            "output": f"Generated documentation: README, API docs, CHANGELOG, CONTRIBUTING",
            "files_modified": [],
            "files_created": docs.files_created,
            "metadata": {
                "readme_length": len(docs.readme),
                "api_docs_count": len(docs.api_docs),
                "files_created": docs.files_created
            }
        }
    
    def generate(
        self,
        project_path: str,
        project_name: str = "Project"
    ) -> DocumentationResult:
        """
        Generate complete documentation for a project.
        
        Args:
            project_path: Path to project root
            project_name: Name of the project
            
        Returns:
            DocumentationResult with all documentation
        """
        files_created = []
        
        # Analyze project
        project_info = self._analyze_project(project_path)
        
        # Generate README
        readme = self._generate_readme(project_path, project_name, project_info)
        readme_path = os.path.join(project_path, "README.md")
        if not os.path.exists(readme_path):
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(readme)
            files_created.append(readme_path)
        
        # Generate API docs
        api_docs = self._generate_api_docs(project_path, project_info)
        docs_dir = os.path.join(project_path, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        for doc_name, doc_content in api_docs.items():
            doc_path = os.path.join(docs_dir, f"{doc_name}.md")
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(doc_content)
            files_created.append(doc_path)
        
        # Generate CHANGELOG
        changelog = self._generate_changelog(project_path, project_info)
        changelog_path = os.path.join(project_path, "CHANGELOG.md")
        if not os.path.exists(changelog_path):
            with open(changelog_path, "w", encoding="utf-8") as f:
                f.write(changelog)
            files_created.append(changelog_path)
        
        # Generate CONTRIBUTING
        contributing = self._generate_contributing(project_path, project_name, project_info)
        contributing_path = os.path.join(project_path, "CONTRIBUTING.md")
        if not os.path.exists(contributing_path):
            with open(contributing_path, "w", encoding="utf-8") as f:
                f.write(contributing)
            files_created.append(contributing_path)
        
        # Generate LICENSE text
        license_text = self._generate_license(project_info)
        
        return DocumentationResult(
            readme=readme,
            api_docs=api_docs,
            changelog=changelog,
            contributing=contributing,
            license_text=license_text,
            files_created=files_created
        )
    
    def _analyze_project(self, project_path: str) -> Dict:
        """Analyze project structure and extract information"""
        info = {
            "language": None,
            "framework": None,
            "dependencies": [],
            "entry_points": [],
            "modules": [],
            "has_tests": False,
            "has_docker": False,
            "has_ci": False,
            "license": None
        }
        
        # Detect language
        if os.path.exists(os.path.join(project_path, "requirements.txt")):
            info["language"] = "python"
            info["dependencies"] = self._parse_requirements(project_path)
        elif os.path.exists(os.path.join(project_path, "package.json")):
            info["language"] = "javascript"
            with open(os.path.join(project_path, "package.json")) as f:
                pkg = __import__("json").load(f)
                info["dependencies"] = list(pkg.get("dependencies", {}).keys())
                info["framework"] = self._detect_js_framework(pkg)
        elif os.path.exists(os.path.join(project_path, "go.mod")):
            info["language"] = "go"
        
        # Find entry points
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "__pycache__"]]
            
            for file in files:
                if file in ["main.py", "app.py", "index.py", "index.js", "main.go"]:
                    info["entry_points"].append(os.path.join(root, file))
                if file.startswith("test_") or file.endswith("_test.py") or file.endswith(".test.js"):
                    info["has_tests"] = True
        
        # Check for Docker
        if os.path.exists(os.path.join(project_path, "Dockerfile")) or \
           os.path.exists(os.path.join(project_path, "docker-compose.yml")):
            info["has_docker"] = True
        
        # Check for CI
        if os.path.exists(os.path.join(project_path, ".github", "workflows")) or \
           os.path.exists(os.path.join(project_path, ".gitlab-ci.yml")):
            info["has_ci"] = True
        
        # Check for license
        for license_file in ["LICENSE", "LICENSE.md", "LICENSE.txt"]:
            if os.path.exists(os.path.join(project_path, license_file)):
                info["license"] = license_file
                break
        
        return info
    
    def _parse_requirements(self, project_path: str) -> List[str]:
        """Parse requirements.txt"""
        req_path = os.path.join(project_path, "requirements.txt")
        if not os.path.exists(req_path):
            return []
        
        with open(req_path) as f:
            deps = []
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract package name
                    pkg = re.split(r"[<>=!~]", line)[0]
                    deps.append(pkg)
            return deps
    
    def _detect_js_framework(self, pkg: Dict) -> Optional[str]:
        """Detect JavaScript framework from package.json"""
        deps = pkg.get("dependencies", {})
        dev_deps = pkg.get("devDependencies", {})
        all_deps = {**deps, **dev_deps}
        
        if "react" in all_deps:
            return "react"
        if "vue" in all_deps:
            return "vue"
        if "svelte" in all_deps:
            return "svelte"
        if "angular" in all_deps or "@angular/core" in all_deps:
            return "angular"
        if "next" in all_deps:
            return "nextjs"
        if "express" in all_deps:
            return "express"
        
        return None
    
    def _generate_readme(
        self,
        project_path: str,
        project_name: str,
        project_info: Dict
    ) -> str:
        """Generate README.md content"""
        sections = []
        
        # Title and description
        sections.append(f"# {project_name}\n")
        sections.append("A brief description of what this project does.\n")
        
        # Badges
        badges = []
        if project_info["language"]:
            badges.append(f"![Language](https://img.shields.io/badge/language-{project_info['language']}-blue)")
        if project_info["has_tests"]:
            badges.append("![Tests](https://img.shields.io/badge/tests-passing-green)")
        if project_info["license"]:
            badges.append("![License](https://img.shields.io/badge/license-MIT-green)")
        
        if badges:
            sections.append("\n" + " ".join(badges) + "\n")
        
        # Table of Contents
        sections.append("\n## Table of Contents\n")
        sections.append("- [Installation](#installation)\n")
        sections.append("- [Usage](#usage)\n")
        sections.append("- [API Reference](#api-reference)\n")
        sections.append("- [Contributing](#contributing)\n")
        sections.append("- [License](#license)\n")
        
        # Installation
        sections.append("\n## Installation\n")
        if project_info["language"] == "python":
            sections.append("```bash\npip install -r requirements.txt\n```\n")
        elif project_info["language"] == "javascript":
            sections.append("```bash\nnpm install\n```\n")
        
        # Usage
        sections.append("\n## Usage\n")
        if project_info["entry_points"]:
            entry = project_info["entry_points"][0]
            if project_info["language"] == "python":
                sections.append(f"```bash\npython {os.path.basename(entry)}\n```\n")
            elif project_info["language"] == "javascript":
                sections.append("```bash\nnpm start\n```\n")
        
        # Features
        sections.append("\n## Features\n")
        sections.append("- Feature 1: Description\n")
        sections.append("- Feature 2: Description\n")
        sections.append("- Feature 3: Description\n")
        
        # API Reference
        sections.append("\n## API Reference\n")
        sections.append("See [docs/API.md](docs/API.md) for detailed API documentation.\n")
        
        # Development
        sections.append("\n## Development\n")
        if project_info["has_tests"]:
            sections.append("### Running Tests\n")
            if project_info["language"] == "python":
                sections.append("```bash\npytest\n```\n")
            elif project_info["language"] == "javascript":
                sections.append("```bash\nnpm test\n```\n")
        
        # Contributing
        sections.append("\n## Contributing\n")
        sections.append("See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.\n")
        
        # License
        sections.append("\n## License\n")
        if project_info["license"]:
            sections.append(f"This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.\n")
        else:
            sections.append("This project is licensed under the MIT License.\n")
        
        return "\n".join(sections)
    
    def _generate_api_docs(
        self,
        project_path: str,
        project_info: Dict
    ) -> Dict[str, str]:
        """Generate API documentation"""
        api_docs = {}
        
        # Scan for API endpoints
        endpoints = self._scan_api_endpoints(project_path, project_info)
        
        if endpoints:
            api_content = ["# API Reference\n"]
            api_content.append("## Endpoints\n\n")
            
            for endpoint in endpoints:
                api_content.append(f"### {endpoint['method']} {endpoint['path']}\n\n")
                if endpoint.get("description"):
                    api_content.append(f"{endpoint['description']}\n\n")
                if endpoint.get("parameters"):
                    api_content.append("**Parameters:**\n\n")
                    for param in endpoint["parameters"]:
                        api_content.append(f"- `{param['name']}` ({param['type']}): {param.get('description', '')}\n")
                api_content.append("\n---\n\n")
            
            api_docs["API"] = "".join(api_content)
        
        # Generate module documentation
        modules_doc = self._generate_modules_doc(project_path, project_info)
        if modules_doc:
            api_docs["Modules"] = modules_doc
        
        return api_docs
    
    def _scan_api_endpoints(
        self,
        project_path: str,
        project_info: Dict
    ) -> List[Dict]:
        """Scan for API endpoints"""
        endpoints = []
        
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "__pycache__"]]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Python Flask/FastAPI
                if file.endswith(".py"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        # Flask routes
                        flask_routes = re.findall(r"@app\.route\(['\"]([^'\"]+)['\"].*?\).*?def\s+(\w+)", content, re.DOTALL)
                        for path, func in flask_routes:
                            endpoints.append({
                                "method": "GET",  # Default
                                "path": path,
                                "function": func
                            })
                        
                        # FastAPI routes
                        fastapi_routes = re.findall(r"@(?:app|router)\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"].*?\).*?def\s+(\w+)", content, re.DOTALL | re.IGNORECASE)
                        for method, path, func in fastapi_routes:
                            endpoints.append({
                                "method": method.upper(),
                                "path": path,
                                "function": func
                            })
                    except Exception:
                        continue
                
                # Express routes
                elif file.endswith(".js") or file.endswith(".ts"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        express_routes = re.findall(r"app\.(get|post|put|delete|patch)\(['\"]([^'\"]+)['\"]", content, re.IGNORECASE)
                        for method, path in express_routes:
                            endpoints.append({
                                "method": method.upper(),
                                "path": path
                            })
                    except Exception:
                        continue
        
        return endpoints
    
    def _generate_modules_doc(
        self,
        project_path: str,
        project_info: Dict
    ) -> str:
        """Generate module documentation"""
        content = ["# Module Reference\n\n"]
        
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "__pycache__", "tests", "test"]]
            
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    module_path = os.path.join(root, file)
                    rel_path = os.path.relpath(module_path, project_path)
                    
                    try:
                        with open(module_path, "r", encoding="utf-8") as f:
                            file_content = f.read()
                        
                        # Extract docstring
                        docstring = re.search(r'"""(.*?)"""', file_content, re.DOTALL)
                        if docstring:
                            module_name = file[:-3]  # Remove .py
                            content.append(f"## `{module_name}`\n\n")
                            content.append(f"{docstring.group(1).strip()}\n\n")
                            
                            # Extract classes and functions
                            classes = re.findall(r"class\s+(\w+).*?\"\"\"(.*?)\"\"\"", file_content, re.DOTALL)
                            for class_name, class_doc in classes:
                                content.append(f"### {class_name}\n\n")
                                content.append(f"{class_doc.strip()}\n\n")
                    except Exception:
                        continue
        
        return "".join(content) if len(content) > 2 else ""
    
    def _generate_changelog(
        self,
        project_path: str,
        project_info: Dict
    ) -> str:
        """Generate CHANGELOG.md"""
        content = ["# Changelog\n\n"]
        content.append("All notable changes to this project will be documented in this file.\n\n")
        content.append("The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\n")
        content.append("and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n")
        
        # Try to get version from git tags
        try:
            import subprocess
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                content.append(f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\n")
        except Exception:
            content.append("## [Unreleased]\n\n")
        
        content.append("### Added\n")
        content.append("- Initial release\n\n")
        content.append("### Changed\n")
        content.append("- Nothing yet\n\n")
        content.append("### Fixed\n")
        content.append("- Nothing yet\n")
        
        return "".join(content)
    
    def _generate_contributing(
        self,
        project_path: str,
        project_name: str,
        project_info: Dict
    ) -> str:
        """Generate CONTRIBUTING.md"""
        content = [f"# Contributing to {project_name}\n\n"]
        
        content.append("Thank you for your interest in contributing to this project! ")
        content.append("This document provides guidelines and instructions for contributing.\n\n")
        
        content.append("## Development Setup\n\n")
        
        if project_info["language"] == "python":
            content.append("1. Clone the repository\n")
            content.append("2. Create a virtual environment:\n")
            content.append("   ```bash\n")
            content.append("   python -m venv venv\n")
            content.append("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate\n")
            content.append("   ```\n")
            content.append("3. Install dependencies:\n")
            content.append("   ```bash\n")
            content.append("   pip install -r requirements.txt\n")
            content.append("   ```\n\n")
        elif project_info["language"] == "javascript":
            content.append("1. Clone the repository\n")
            content.append("2. Install dependencies:\n")
            content.append("   ```bash\n")
            content.append("   npm install\n")
            content.append("   ```\n\n")
        
        content.append("## Pull Request Process\n\n")
        content.append("1. Fork the repository\n")
        content.append("2. Create a feature branch (`git checkout -b feature/amazing-feature`)\n")
        content.append("3. Make your changes\n")
        content.append("4. Run tests to ensure they pass\n")
        content.append("5. Commit your changes (`git commit -m 'Add amazing feature'`)\n")
        content.append("6. Push to the branch (`git push origin feature/amazing-feature`)\n")
        content.append("7. Open a Pull Request\n\n")
        
        content.append("## Code Style\n\n")
        if project_info["language"] == "python":
            content.append("- Follow PEP 8 guidelines\n")
            content.append("- Use type hints where appropriate\n")
            content.append("- Write docstrings for all public functions\n")
        elif project_info["language"] == "javascript":
            content.append("- Follow the project's ESLint configuration\n")
            content.append("- Use meaningful variable names\n")
            content.append("- Comment complex logic\n")
        
        return "".join(content)
    
    def _generate_license(self, project_info: Dict) -> str:
        """Generate license text"""
        year = datetime.now().year
        
        return f"""MIT License

Copyright (c) {year} Project Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""