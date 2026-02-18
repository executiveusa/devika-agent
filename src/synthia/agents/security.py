"""
SYNTHIA Security Agent
======================
Security analysis and vulnerability detection agent.

Responsibilities:
- Scan for security vulnerabilities
- Detect secrets in code
- Check dependency vulnerabilities
- Validate input sanitization
- Review authentication patterns
- Generate security reports
"""

import os
import re
import json
import subprocess
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib


@dataclass
class SecurityIssue:
    """A security issue found in code"""
    severity: str  # critical, high, medium, low, info
    title: str
    description: str
    file_path: str
    line_number: int
    recommendation: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None


@dataclass
class SecurityReport:
    """Complete security analysis report"""
    issues: List[SecurityIssue]
    secrets_found: List[Dict]
    vulnerable_dependencies: List[Dict]
    security_score: float
    recommendations: List[str]
    compliance_status: Dict[str, bool]


class Security:
    """
    Security analysis agent.
    
    Scans code for vulnerabilities, secrets, and security issues.
    
    Usage:
        security = Security()
        report = security.analyze("/path/to/project")
        print(f"Security score: {report.security_score}")
    """
    
    # Secret patterns to detect
    SECRET_PATTERNS = {
        "aws_access_key": r"AKIA[0-9A-Z]{16}",
        "aws_secret_key": r"aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{40}['\"]",
        "github_token": r"ghp_[A-Za-z0-9]{36}",
        "github_oauth": r"gho_[A-Za-z0-9]{36}",
        "github_app": r"(?:ghu|ghs)_[A-Za-z0-9]{36}",
        "slack_token": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}",
        "stripe_key": r"sk_live_[0-9a-zA-Z]{24}",
        "stripe_publishable": r"pk_live_[0-9a-zA-Z]{24}",
        "twilio_sid": r"AC[a-f0-9]{32}",
        "twilio_token": r"[a-f0-9]{32}",
        "jwt_secret": r"jwt[_-]?secret\s*=\s*['\"][^'\"]+['\"]",
        "api_key_generic": r"(?:api[_-]?key|apikey)\s*=\s*['\"][^'\"]{16,}['\"]",
        "password": r"(?:password|passwd|pwd)\s*=\s*['\"][^'\"]+['\"]",
        "private_key": r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----",
        "database_url": r"(?:mysql|postgres|mongodb)://[^:]+:[^@]+@[^/]+",
    }
    
    # Vulnerability patterns
    VULNERABILITY_PATTERNS = {
        "sql_injection": {
            "pattern": r"(?:execute|executemany)\s*\([^)]*%s[^)]*\+|f['\"].*?SELECT.*?{",
            "severity": "critical",
            "title": "Potential SQL Injection",
            "cwe": "CWE-89",
            "owasp": "A03:2021 - Injection"
        },
        "xss": {
            "pattern": r"(?:innerHTML|document\.write)\s*\(|render_template_string\s*\(",
            "severity": "high",
            "title": "Potential Cross-Site Scripting (XSS)",
            "cwe": "CWE-79",
            "owasp": "A03:2021 - Injection"
        },
        "command_injection": {
            "pattern": r"(?:os\.system|subprocess\.(?:call|run|Popen))\s*\([^)]*\+|eval\s*\(",
            "severity": "critical",
            "title": "Potential Command Injection",
            "cwe": "CWE-78",
            "owasp": "A03:2021 - Injection"
        },
        "path_traversal": {
            "pattern": r"open\s*\([^)]*\+|readFile\s*\([^)]*\+|sendfile\s*\([^)]*\+",
            "severity": "high",
            "title": "Potential Path Traversal",
            "cwe": "CWE-22",
            "owasp": "A01:2021 - Broken Access Control"
        },
        "hardcoded_credentials": {
            "pattern": r"(?:password|passwd|pwd|secret|token|api_key)\s*=\s*['\"][^'\"]{8,}['\"]",
            "severity": "high",
            "title": "Hardcoded Credentials",
            "cwe": "CWE-798",
            "owasp": "A07:2021 - Identification and Authentication Failures"
        },
        "insecure_random": {
            "pattern": r"random\.(?:random|randint|choice)\s*\([^)]*\)",
            "severity": "medium",
            "title": "Insecure Random Number Generator",
            "cwe": "CWE-338",
            "owasp": "A02:2021 - Cryptographic Failures"
        },
        "debug_enabled": {
            "pattern": r"DEBUG\s*=\s*True|debug\s*=\s*true",
            "severity": "medium",
            "title": "Debug Mode Enabled",
            "cwe": "CWE-215",
            "owasp": "A05:2021 - Security Misconfiguration"
        },
        "ssl_verification_disabled": {
            "pattern": r"verify\s*=\s*False|CERT_NONE|ssl\._create_unverified_context",
            "severity": "high",
            "title": "SSL Verification Disabled",
            "cwe": "CWE-295",
            "owasp": "A02:2021 - Cryptographic Failures"
        },
        "yaml_unsafe_load": {
            "pattern": r"yaml\.load\s*\([^)]*\)(?!.*Loader)",
            "severity": "high",
            "title": "Unsafe YAML Load",
            "cwe": "CWE-502",
            "owasp": "A08:2021 - Software and Data Integrity Failures"
        },
        "pickle_unsafe": {
            "pattern": r"pickle\.loads?\s*\(",
            "severity": "high",
            "title": "Unsafe Pickle Usage",
            "cwe": "CWE-502",
            "owasp": "A08:2021 - Software and Data Integrity Failures"
        }
    }
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
    
    def execute(self, context: Any, **kwargs) -> Dict:
        """Execute security analysis"""
        project_path = kwargs.get("project_path") or context.metadata.get("project_path")
        
        if not project_path:
            return {
                "output": "No project path provided for security analysis",
                "errors": ["Missing project_path"]
            }
        
        report = self.analyze(project_path)
        
        return {
            "output": f"Security score: {report.security_score:.1f}/100. Found {len(report.issues)} issues.",
            "files_modified": [],
            "files_created": [],
            "metadata": {
                "security_score": report.security_score,
                "issues_count": len(report.issues),
                "critical": sum(1 for i in report.issues if i.severity == "critical"),
                "high": sum(1 for i in report.issues if i.severity == "high"),
                "medium": sum(1 for i in report.issues if i.severity == "medium"),
                "secrets_found": len(report.secrets_found),
                "vulnerable_deps": len(report.vulnerable_dependencies),
                "recommendations": report.recommendations
            }
        }
    
    def analyze(self, project_path: str) -> SecurityReport:
        """
        Analyze project for security issues.
        
        Args:
            project_path: Path to project root
            
        Returns:
            SecurityReport with all findings
        """
        # Scan for vulnerabilities
        issues = self._scan_vulnerabilities(project_path)
        
        # Scan for secrets
        secrets = self._scan_secrets(project_path)
        
        # Check dependencies
        vulnerable_deps = self._check_dependencies(project_path)
        
        # Calculate security score
        score = self._calculate_score(issues, secrets, vulnerable_deps)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues, secrets, vulnerable_deps)
        
        # Check compliance
        compliance = self._check_compliance(issues)
        
        return SecurityReport(
            issues=issues,
            secrets_found=secrets,
            vulnerable_dependencies=vulnerable_deps,
            security_score=score,
            recommendations=recommendations,
            compliance_status=compliance
        )
    
    def _scan_vulnerabilities(self, project_path: str) -> List[SecurityIssue]:
        """Scan code for vulnerability patterns"""
        issues = []
        
        for root, dirs, files in os.walk(project_path):
            # Skip hidden and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in [
                "node_modules", "__pycache__", "venv", ".venv", "dist", "build",
                ".git", "data", "logs", "cache", "vendor"
            ]]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Only scan source files
                if not file.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".php", ".rb")):
                    continue
                
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        lines = content.split("\n")
                    
                    for vuln_name, vuln_info in self.VULNERABILITY_PATTERNS.items():
                        pattern = vuln_info["pattern"]
                        
                        for match in re.finditer(pattern, content, re.IGNORECASE):
                            # Find line number
                            line_num = content[:match.start()].count("\n") + 1
                            
                            issues.append(SecurityIssue(
                                severity=vuln_info["severity"],
                                title=vuln_info["title"],
                                description=f"Found pattern matching {vuln_name} vulnerability",
                                file_path=os.path.relpath(file_path, project_path),
                                line_number=line_num,
                                recommendation=self._get_remediation(vuln_name),
                                cwe_id=vuln_info.get("cwe"),
                                owasp_category=vuln_info.get("owasp")
                            ))
                
                except Exception:
                    continue
        
        return issues
    
    def _scan_secrets(self, project_path: str) -> List[Dict]:
        """Scan for hardcoded secrets"""
        secrets = []
        
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in [
                "node_modules", "__pycache__", "venv", ".venv", ".git"
            ]]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Skip binary files and common non-text files
                if file.endswith((".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz")):
                    continue
                
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    for secret_name, pattern in self.SECRET_PATTERNS.items():
                        for match in re.finditer(pattern, content, re.IGNORECASE):
                            line_num = content[:match.start()].count("\n") + 1
                            
                            # Mask the secret
                            matched_text = match.group(0)
                            masked = matched_text[:10] + "*" * (len(matched_text) - 15) + matched_text[-5:]
                            
                            secrets.append({
                                "type": secret_name,
                                "file": os.path.relpath(file_path, project_path),
                                "line": line_num,
                                "masked_value": masked,
                                "severity": "critical" if secret_name in ["private_key", "aws_secret_key", "password"] else "high"
                            })
                
                except Exception:
                    continue
        
        return secrets
    
    def _check_dependencies(self, project_path: str) -> List[Dict]:
        """Check for vulnerable dependencies"""
        vulnerable = []
        
        # Python - check requirements.txt
        req_path = os.path.join(project_path, "requirements.txt")
        if os.path.exists(req_path):
            try:
                # Try using safety or pip-audit if available
                result = subprocess.run(
                    ["pip-audit", "-r", req_path, "--format", "json"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0 and result.stdout:
                    audit_result = json.loads(result.stdout)
                    for vuln in audit_result.get("vulnerabilities", []):
                        vulnerable.append({
                            "package": vuln.get("name"),
                            "installed_version": vuln.get("version"),
                            "severity": "high",
                            "description": vuln.get("description", ""),
                            "cve": vuln.get("id", "")
                        })
            except Exception:
                pass
        
        # JavaScript - check package.json
        pkg_path = os.path.join(project_path, "package.json")
        if os.path.exists(pkg_path):
            try:
                result = subprocess.run(
                    ["npm", "audit", "--json"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.stdout:
                    audit_result = json.loads(result.stdout)
                    for name, info in audit_result.get("vulnerabilities", {}).items():
                        if info.get("severity") in ["critical", "high"]:
                            vulnerable.append({
                                "package": name,
                                "severity": info.get("severity"),
                                "via": info.get("via", [])
                            })
            except Exception:
                pass
        
        return vulnerable
    
    def _get_remediation(self, vuln_name: str) -> str:
        """Get remediation advice for a vulnerability"""
        remediations = {
            "sql_injection": "Use parameterized queries or prepared statements instead of string concatenation.",
            "xss": "Sanitize and escape user input before rendering. Use textContent instead of innerHTML.",
            "command_injection": "Avoid passing user input to shell commands. Use allowlists for permitted commands.",
            "path_traversal": "Validate and sanitize file paths. Use os.path.basename() or equivalent.",
            "hardcoded_credentials": "Use environment variables or secure secret management systems.",
            "insecure_random": "Use secrets module for cryptographic operations instead of random.",
            "debug_enabled": "Disable debug mode in production environments.",
            "ssl_verification_disabled": "Always verify SSL certificates in production.",
            "yaml_unsafe_load": "Use yaml.safe_load() instead of yaml.load().",
            "pickle_unsafe": "Avoid pickle for untrusted data. Use JSON or other safe serialization."
        }
        return remediations.get(vuln_name, "Review and fix the identified security issue.")
    
    def _calculate_score(
        self,
        issues: List[SecurityIssue],
        secrets: List[Dict],
        vulnerable_deps: List[Dict]
    ) -> float:
        """Calculate security score (0-100)"""
        score = 100.0
        
        # Deduct for issues
        severity_weights = {
            "critical": 25,
            "high": 15,
            "medium": 5,
            "low": 2,
            "info": 0
        }
        
        for issue in issues:
            score -= severity_weights.get(issue.severity, 0)
        
        # Deduct for secrets
        for secret in secrets:
            score -= severity_weights.get(secret.get("severity", "high"), 15)
        
        # Deduct for vulnerable dependencies
        for dep in vulnerable_deps:
            score -= severity_weights.get(dep.get("severity", "high"), 15)
        
        return max(0, min(100, score))
    
    def _generate_recommendations(
        self,
        issues: List[SecurityIssue],
        secrets: List[Dict],
        vulnerable_deps: List[Dict]
    ) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # Critical issues
        critical_count = sum(1 for i in issues if i.severity == "critical")
        if critical_count > 0:
            recommendations.append(f"URGENT: Fix {critical_count} critical security vulnerabilities immediately")
        
        # Secrets
        if secrets:
            recommendations.append("Remove all hardcoded secrets and use environment variables or secret management")
            recommendations.append("Rotate all exposed credentials immediately")
        
        # Vulnerable dependencies
        if vulnerable_deps:
            recommendations.append(f"Update {len(vulnerable_deps)} vulnerable dependencies to secure versions")
        
        # General recommendations based on findings
        issue_types = set(i.title for i in issues)
        
        if "Potential SQL Injection" in issue_types:
            recommendations.append("Implement parameterized queries throughout the codebase")
        
        if "Potential Cross-Site Scripting (XSS)" in issue_types:
            recommendations.append("Add Content Security Policy headers and sanitize all user inputs")
        
        if "Debug Mode Enabled" in issue_types:
            recommendations.append("Ensure debug mode is disabled in production")
        
        if "SSL Verification Disabled" in issue_types:
            recommendations.append("Enable SSL certificate verification in all HTTP requests")
        
        # Default recommendations
        if not recommendations:
            recommendations.append("Continue regular security audits and dependency updates")
        
        recommendations.append("Implement automated security scanning in CI/CD pipeline")
        
        return recommendations
    
    def _check_compliance(self, issues: List[SecurityIssue]) -> Dict[str, bool]:
        """Check compliance with security standards"""
        owasp_issues = {}
        
        for issue in issues:
            if issue.owasp_category:
                owasp_issues[issue.owasp_category] = True
        
        return {
            "OWASP_A01_Broken_Access_Control": "A01:2021" not in owasp_issues,
            "OWASP_A02_Cryptographic_Failures": "A02:2021" not in owasp_issues,
            "OWASP_A03_Injection": "A03:2021" not in owasp_issues,
            "OWASP_A05_Security_Misconfiguration": "A05:2021" not in owasp_issues,
            "OWASP_A07_Authentication_Failures": "A07:2021" not in owasp_issues,
            "OWASP_A08_Data_Integrity": "A08:2021" not in owasp_issues,
            "no_critical_issues": all(i.severity != "critical" for i in issues),
            "no_hardcoded_secrets": all(i.title != "Hardcoded Credentials" for i in issues)
        }
    
    def generate_security_md(self, report: SecurityReport) -> str:
        """Generate SECURITY.md file content"""
        content = ["# Security Policy\n\n"]
        
        content.append("## Supported Versions\n\n")
        content.append("| Version | Supported          |\n")
        content.append("| ------- | ------------------ |\n")
        content.append("| latest  | :white_check_mark: |\n")
        content.append("| < 1.0   | :x:                |\n\n")
        
        content.append("## Reporting a Vulnerability\n\n")
        content.append("If you discover a security vulnerability, please report it by emailing the maintainers.\n\n")
        content.append("Please include:\n")
        content.append("- Description of the vulnerability\n")
        content.append("- Steps to reproduce\n")
        content.append("- Potential impact\n")
        content.append("- Suggested fix (if any)\n\n")
        
        content.append("## Security Measures\n\n")
        content.append("This project implements the following security measures:\n\n")
        
        if report.security_score >= 80:
            content.append("- :white_check_mark: Regular security audits\n")
            content.append("- :white_check_mark: Dependency vulnerability scanning\n")
            content.append("- :white_check_mark: Code review process\n")
        else:
            content.append("- :warning: Security improvements needed\n")
        
        return "".join(content)