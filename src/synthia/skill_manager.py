"""
SYNTHIA Skill Manager - Global Skill Sharing System

This module provides a centralized skill management system for SYNTHIA,
integrating with the Universal Skills Manager for cross-platform skill sharing.

Features:
- Multi-source skill discovery (SkillsMP, SkillHub, ClawHub)
- Local skill registry with versioning
- Cross-tool synchronization
- Security scanning at install time
- n8n workflow integration
"""

import json
import os
import subprocess
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error


class SkillSource(Enum):
    """Available skill sources."""
    SKILLSMP = "skillsmp"
    SKILLHUB = "skillhub"
    CLAWHUB = "clawhub"
    LOCAL = "local"
    N8N = "n8n"


class SkillScope(Enum):
    """Skill installation scopes."""
    GLOBAL = "global"  # User-level, available across all projects
    PROJECT = "project"  # Project-level, only for current project


@dataclass
class Skill:
    """Represents a skill with metadata."""
    name: str
    description: str
    source: SkillSource
    path: Path
    version: str = "1.0.0"
    author: str = "unknown"
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    compatible_tools: List[str] = field(default_factory=list)
    installed_at: Optional[datetime] = None
    security_scanned: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "source": self.source.value,
            "path": str(self.path),
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "compatible_tools": self.compatible_tools,
            "installed_at": self.installed_at.isoformat() if self.installed_at else None,
            "security_scanned": self.security_scanned,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        return cls(
            name=data["name"],
            description=data["description"],
            source=SkillSource(data["source"]),
            path=Path(data["path"]),
            version=data.get("version", "1.0.0"),
            author=data.get("author", "unknown"),
            tags=data.get("tags", []),
            dependencies=data.get("dependencies", []),
            compatible_tools=data.get("compatible_tools", []),
            installed_at=datetime.fromisoformat(data["installed_at"]) if data.get("installed_at") else None,
            security_scanned=data.get("security_scanned", False),
        )


@dataclass
class SearchResult:
    """Skill search result."""
    id: str
    name: str
    description: str
    source: SkillSource
    url: Optional[str] = None
    stars: int = 0
    downloads: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source": self.source.value,
            "url": self.url,
            "stars": self.stars,
            "downloads": self.downloads,
        }


class SecurityScanner:
    """Security scanner for skill validation."""
    
    CRITICAL_PATTERNS = [
        (r"rm\s+-rf\s+/", "Destructive filesystem command"),
        (r"sudo\s+rm", "Sudo rm command"),
        (r">\s*/dev/sd[a-z]", "Direct disk write"),
        (r"mkfs\.", "Filesystem format command"),
        (r"dd\s+if=.*of=/dev/", "Disk dump command"),
        (r"curl.*\|\s*(sudo\s+)?bash", "Remote code execution"),
        (r"wget.*\|\s*(sudo\s+)?bash", "Remote code execution"),
        (r"eval\s*\(", "Dynamic code evaluation"),
        (r"exec\s*\(", "Dynamic code execution"),
        (r"__import__\s*\(", "Dynamic import"),
        (r"subprocess\.call\s*\([^)]*shell=True", "Shell injection risk"),
        (r"os\.system\s*\(", "System command execution"),
    ]
    
    HIGH_PATTERNS = [
        (r"base64\.b64decode", "Base64 encoded content"),
        (r"pickle\.loads", "Pickle deserialization"),
        (r"yaml\.load\s*\([^)]*\)", "Unsafe YAML loading"),
        (r"requests\.(get|post)\s*\([^)]*verify=False", "SSL verification disabled"),
        (r"\bpassword\b\s*=\s*['\"]", "Hardcoded password"),
        (r"\bapi_key\b\s*=\s*['\"]", "Hardcoded API key"),
        (r"\bsecret\b\s*=\s*['\"]", "Hardcoded secret"),
    ]
    
    MEDIUM_PATTERNS = [
        (r"#\s*TODO", "Unresolved TODO comment"),
        (r"#\s*FIXME", "Unresolved FIXME comment"),
        (r"#\s*XXX", "XXX comment"),
        (r"print\s*\(", "Debug print statement"),
        (r"console\.log\s*\(", "Debug console.log"),
        (r"pass\s*$", "Empty code block"),
    ]
    
    def scan(self, content: str) -> Dict[str, Any]:
        """Scan content for security issues."""
        import re
        
        findings = {
            "critical": [],
            "high": [],
            "medium": [],
            "passed": True,
        }
        
        for pattern, description in self.CRITICAL_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                findings["critical"].append({
                    "pattern": pattern,
                    "description": description,
                    "severity": "critical",
                })
                findings["passed"] = False
        
        for pattern, description in self.HIGH_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                findings["high"].append({
                    "pattern": pattern,
                    "description": description,
                    "severity": "high",
                })
        
        for pattern, description in self.MEDIUM_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                findings["medium"].append({
                    "pattern": pattern,
                    "description": description,
                    "severity": "medium",
                })
        
        return findings


class SkillManager:
    """
    Centralized skill manager for SYNTHIA.
    
    Integrates with Universal Skills Manager for cross-platform skill sharing.
    Manages skill discovery, installation, synchronization, and security scanning.
    """
    
    # Supported AI tools and their skill paths
    TOOL_PATHS = {
        "claude": {
            "global": Path.home() / ".claude" / "skills",
            "local": Path.cwd() / ".claude" / "skills",
        },
        "gemini": {
            "global": Path.home() / ".gemini" / "skills",
            "local": Path.cwd() / ".gemini" / "skills",
        },
        "cursor": {
            "global": Path.home() / ".cursor" / "skills",
            "local": Path.cwd() / ".cursor" / "skills",
        },
        "codex": {
            "global": Path.home() / ".codex" / "skills",
            "local": Path.cwd() / ".codex" / "skills",
        },
        "opencode": {
            "global": Path.home() / ".config" / "opencode" / "skills",
            "local": Path.cwd() / ".opencode" / "skills",
        },
        "cline": {
            "global": Path.home() / ".cline" / "skills",
            "local": Path.cwd() / ".cline" / "skills",
        },
        "roo": {
            "global": Path.home() / ".roo" / "skills",
            "local": Path.cwd() / ".roo" / "skills",
        },
        "goose": {
            "global": Path.home() / ".config" / "goose" / "skills",
            "local": Path.cwd() / ".goose" / "agents",
        },
        "synthia": {
            "global": Path.home() / ".synthia" / "skills",
            "local": Path.cwd() / "devika-agent-main" / "skills",
        },
    }
    
    # API endpoints for skill sources
    API_ENDPOINTS = {
        "skillsmp": "https://api.skillsmp.com/v1",
        "skillhub": "https://skills.palebluedot.live/api",
        "clawhub": "https://clawhub.ai/api",
    }
    
    def __init__(
        self,
        skills_dir: Optional[Path] = None,
        config_path: Optional[Path] = None,
        skillsmp_api_key: Optional[str] = None,
    ):
        self.skills_dir = skills_dir or Path.cwd() / "devika-agent-main" / "skills"
        self.config_path = config_path or self.skills_dir / "config.json"
        self.skillsmp_api_key = skillsmp_api_key or os.environ.get("SKILLSMP_API_KEY")
        self.registry_path = self.skills_dir / "registry.json"
        self.scanner = SecurityScanner()
        self._registry: Dict[str, Skill] = {}
        
        # Ensure directories exist
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing registry
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load skill registry from disk."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._registry = {
                        name: Skill.from_dict(skill_data)
                        for name, skill_data in data.get("skills", {}).items()
                    }
            except (json.JSONDecodeError, KeyError):
                self._registry = {}
    
    def _save_registry(self) -> None:
        """Save skill registry to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump({
                "version": "1.0.0",
                "updated_at": datetime.now().isoformat(),
                "skills": {
                    name: skill.to_dict()
                    for name, skill in self._registry.items()
                },
            }, f, indent=2)
    
    def _fetch_json(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[Dict]:
        """Fetch JSON from URL."""
        req = urllib.request.Request(
            url,
            headers={"Content-Type": "application/json", **(headers or {})},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError):
            return None
    
    def search(
        self,
        query: str,
        sources: Optional[List[SkillSource]] = None,
        limit: int = 10,
    ) -> List[SearchResult]:
        """
        Search for skills across multiple sources.
        
        Args:
            query: Search query string
            sources: List of sources to search (default: all)
            limit: Maximum results per source
            
        Returns:
            List of search results
        """
        sources = sources or list(SkillSource)
        results = []
        
        # Search SkillHub (no API key required)
        if SkillSource.SKILLHUB in sources:
            skillhub_results = self._search_skillhub(query, limit)
            results.extend(skillhub_results)
        
        # Search ClawHub (no API key required)
        if SkillSource.CLAWHUB in sources:
            clawhub_results = self._search_clawhub(query, limit)
            results.extend(clawhub_results)
        
        # Search SkillsMP (API key required)
        if SkillSource.SKILLSMP in sources and self.skillsmp_api_key:
            skillsmp_results = self._search_skillsmp(query, limit)
            results.extend(skillsmp_results)
        
        # Search local skills
        if SkillSource.LOCAL in sources:
            local_results = self._search_local(query)
            results.extend(local_results)
        
        # Sort by relevance (stars/downloads)
        results.sort(key=lambda x: x.stars + x.downloads, reverse=True)
        
        return results[:limit]
    
    def _search_skillhub(self, query: str, limit: int) -> List[SearchResult]:
        """Search SkillHub for skills."""
        results = []
        try:
            url = f"{self.API_ENDPOINTS['skillhub']}/skills?search={query}&limit={limit}"
            data = self._fetch_json(url)
            if data and "skills" in data:
                for skill in data["skills"]:
                    results.append(SearchResult(
                        id=skill.get("id", ""),
                        name=skill.get("name", ""),
                        description=skill.get("description", ""),
                        source=SkillSource.SKILLHUB,
                        url=skill.get("github_url"),
                        stars=skill.get("stars", 0),
                        downloads=skill.get("downloads", 0),
                    ))
        except Exception:
            pass
        return results
    
    def _search_clawhub(self, query: str, limit: int) -> List[SearchResult]:
        """Search ClawHub for skills."""
        results = []
        try:
            url = f"{self.API_ENDPOINTS['clawhub']}/search?q={query}&limit={limit}"
            data = self._fetch_json(url)
            if data and "results" in data:
                for skill in data["results"]:
                    results.append(SearchResult(
                        id=skill.get("slug", ""),
                        name=skill.get("name", ""),
                        description=skill.get("description", ""),
                        source=SkillSource.CLAWHUB,
                        url=skill.get("url"),
                        stars=skill.get("stars", 0),
                        downloads=skill.get("downloads", 0),
                    ))
        except Exception:
            pass
        return results
    
    def _search_skillsmp(self, query: str, limit: int) -> List[SearchResult]:
        """Search SkillsMP for skills."""
        results = []
        if not self.skillsmp_api_key:
            return results
        
        try:
            url = f"{self.API_ENDPOINTS['skillsmp']}/search"
            headers = {"Authorization": f"Bearer {self.skillsmp_api_key}"}
            # Note: This would need a POST request with query body
            # Simplified for this implementation
        except Exception:
            pass
        return results
    
    def _search_local(self, query: str) -> List[SearchResult]:
        """Search local skills directory."""
        results = []
        if not self.skills_dir.exists():
            return results
        
        query_lower = query.lower()
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    try:
                        content = skill_md.read_text(encoding="utf-8")
                        # Simple search in content
                        if query_lower in content.lower():
                            # Extract frontmatter
                            name = skill_dir.name
                            description = ""
                            if "---" in content:
                                parts = content.split("---", 2)
                                if len(parts) >= 2:
                                    frontmatter = parts[1]
                                    for line in frontmatter.split("\n"):
                                        if line.startswith("name:"):
                                            name = line.split(":", 1)[1].strip()
                                        elif line.startswith("description:"):
                                            description = line.split(":", 1)[1].strip().strip('"')
                            
                            results.append(SearchResult(
                                id=skill_dir.name,
                                name=name,
                                description=description,
                                source=SkillSource.LOCAL,
                                url=str(skill_dir),
                            ))
                    except Exception:
                        pass
        
        return results
    
    def install(
        self,
        skill_id: str,
        source: SkillSource,
        scope: SkillScope = SkillScope.GLOBAL,
        target_tools: Optional[List[str]] = None,
        skip_security_scan: bool = False,
    ) -> Dict[str, Any]:
        """
        Install a skill from a source.
        
        Args:
            skill_id: Skill ID or URL
            source: Skill source
            scope: Installation scope
            target_tools: Tools to install to (default: all detected)
            skip_security_scan: Skip security scanning (not recommended)
            
        Returns:
            Installation result
        """
        result = {
            "success": False,
            "skill": None,
            "installed_to": [],
            "security_findings": None,
            "errors": [],
        }
        
        # Determine target paths
        target_tools = target_tools or self._detect_installed_tools()
        target_paths = []
        
        for tool in target_tools:
            if tool in self.TOOL_PATHS:
                path_key = "global" if scope == SkillScope.GLOBAL else "local"
                target_paths.append((tool, self.TOOL_PATHS[tool][path_key]))
        
        if not target_paths:
            result["errors"].append("No target tools detected")
            return result
        
        # Fetch skill content
        skill_content = self._fetch_skill(skill_id, source)
        if not skill_content:
            result["errors"].append(f"Failed to fetch skill from {source.value}")
            return result
        
        # Security scan
        if not skip_security_scan:
            scan_result = self.scanner.scan(skill_content.get("content", ""))
            result["security_findings"] = scan_result
            if not scan_result["passed"]:
                result["errors"].append("Security scan failed")
                return result
        
        # Install to each target
        skill_name = skill_content.get("name", skill_id)
        for tool, target_path in target_paths:
            try:
                install_path = target_path / skill_name
                install_path.mkdir(parents=True, exist_ok=True)
                
                # Write SKILL.md
                skill_md = install_path / "SKILL.md"
                skill_md.write_text(skill_content.get("content", ""), encoding="utf-8")
                
                # Write additional files
                for filename, content in skill_content.get("files", {}).items():
                    file_path = install_path / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding="utf-8")
                
                result["installed_to"].append({
                    "tool": tool,
                    "path": str(install_path),
                })
                
            except Exception as e:
                result["errors"].append(f"Failed to install to {tool}: {str(e)}")
        
        # Update registry
        if result["installed_to"]:
            skill = Skill(
                name=skill_name,
                description=skill_content.get("description", ""),
                source=source,
                path=Path(result["installed_to"][0]["path"]),
                version=skill_content.get("version", "1.0.0"),
                author=skill_content.get("author", "unknown"),
                tags=skill_content.get("tags", []),
                security_scanned=not skip_security_scan,
                installed_at=datetime.now(),
            )
            self._registry[skill_name] = skill
            self._save_registry()
            
            result["success"] = True
            result["skill"] = skill.to_dict()
        
        return result
    
    def _fetch_skill(self, skill_id: str, source: SkillSource) -> Optional[Dict[str, Any]]:
        """Fetch skill content from source."""
        if source == SkillSource.LOCAL:
            local_path = self.skills_dir / skill_id / "SKILL.md"
            if local_path.exists():
                return {
                    "name": skill_id,
                    "content": local_path.read_text(encoding="utf-8"),
                }
            return None
        
        # For remote sources, use the install_skill.py script from universal-skills-manager
        usm_path = self.skills_dir / "universal-skills-manager" / "universal-skills-manager" / "scripts" / "install_skill.py"
        if usm_path.exists():
            # Use the USM install script
            pass  # Would call the script here
        
        # Simplified fetch for ClawHub
        if source == SkillSource.CLAWHUB:
            url = f"{self.API_ENDPOINTS['clawhub']}/skills/{skill_id}/file"
            data = self._fetch_json(url)
            if data:
                return {
                    "name": skill_id,
                    "content": data.get("content", ""),
                    "description": data.get("description", ""),
                    "version": data.get("version", "1.0.0"),
                    "author": data.get("author", "unknown"),
                }
        
        return None
    
    def _detect_installed_tools(self) -> List[str]:
        """Detect which AI tools are installed on the system."""
        installed = []
        for tool, paths in self.TOOL_PATHS.items():
            if paths["global"].exists() or paths["local"].exists():
                installed.append(tool)
        return installed
    
    def sync(
        self,
        skill_name: str,
        target_tools: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Synchronize a skill across multiple tools.
        
        Args:
            skill_name: Name of the skill to sync
            target_tools: Tools to sync to (default: all detected)
            
        Returns:
            Sync result
        """
        result = {
            "success": False,
            "synced_to": [],
            "errors": [],
        }
        
        if skill_name not in self._registry:
            result["errors"].append(f"Skill '{skill_name}' not found in registry")
            return result
        
        skill = self._registry[skill_name]
        source_path = skill.path
        
        if not source_path.exists():
            result["errors"].append(f"Skill path does not exist: {source_path}")
            return result
        
        target_tools = target_tools or self._detect_installed_tools()
        
        for tool in target_tools:
            if tool in self.TOOL_PATHS:
                target_path = self.TOOL_PATHS[tool]["global"] / skill_name
                try:
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    shutil.copytree(source_path, target_path)
                    result["synced_to"].append({
                        "tool": tool,
                        "path": str(target_path),
                    })
                except Exception as e:
                    result["errors"].append(f"Failed to sync to {tool}: {str(e)}")
        
        result["success"] = len(result["synced_to"]) > 0
        return result
    
    def list_installed(self) -> List[Dict[str, Any]]:
        """List all installed skills."""
        return [skill.to_dict() for skill in self._registry.values()]
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self._registry.get(name)
    
    def uninstall(self, name: str, remove_from_all_tools: bool = True) -> Dict[str, Any]:
        """
        Uninstall a skill.
        
        Args:
            name: Skill name
            remove_from_all_tools: Remove from all installed tools
            
        Returns:
            Uninstall result
        """
        result = {
            "success": False,
            "removed_from": [],
            "errors": [],
        }
        
        if name not in self._registry:
            result["errors"].append(f"Skill '{name}' not found in registry")
            return result
        
        skill = self._registry[name]
        
        if remove_from_all_tools:
            for tool in self._detect_installed_tools():
                if tool in self.TOOL_PATHS:
                    for scope in ["global", "local"]:
                        tool_path = self.TOOL_PATHS[tool][scope] / name
                        if tool_path.exists():
                            try:
                                shutil.rmtree(tool_path)
                                result["removed_from"].append({
                                    "tool": tool,
                                    "scope": scope,
                                    "path": str(tool_path),
                                })
                            except Exception as e:
                                result["errors"].append(f"Failed to remove from {tool}: {str(e)}")
        
        # Remove from registry
        del self._registry[name]
        self._save_registry()
        
        result["success"] = True
        return result
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a skill report showing installed skills across tools."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "tools": {},
            "skills": {},
            "summary": {
                "total_skills": len(self._registry),
                "tools_detected": 0,
            },
        }
        
        for tool in self._detect_installed_tools():
            tool_skills = []
            if tool in self.TOOL_PATHS:
                for scope in ["global", "local"]:
                    skills_path = self.TOOL_PATHS[tool][scope]
                    if skills_path.exists():
                        for skill_dir in skills_path.iterdir():
                            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                                tool_skills.append({
                                    "name": skill_dir.name,
                                    "scope": scope,
                                    "path": str(skill_dir),
                                })
            
            report["tools"][tool] = {
                "skills": tool_skills,
                "count": len(tool_skills),
            }
        
        report["skills"] = self.list_installed()
        report["summary"]["tools_detected"] = len(report["tools"])
        
        return report


# Singleton instance
_skill_manager: Optional[SkillManager] = None


def get_skill_manager() -> SkillManager:
    """Get the global skill manager instance."""
    global _skill_manager
    if _skill_manager is None:
        _skill_manager = SkillManager()
    return _skill_manager
