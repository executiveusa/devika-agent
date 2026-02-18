"""
SYNTHIA Sandbox Code Runner
===========================
Secure code execution in isolated Docker containers.

Based on Ralphy's sandbox patterns with additional security layers.

Features:
- Docker container isolation
- Resource limits (CPU, memory, time)
- Network isolation options
- File system sandboxing
- Output streaming
- Security scanning before execution
- Support for multiple languages
"""

import os
import json
import time
import subprocess
import tempfile
import shutil
import threading
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import hashlib


class Language(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    C = "c"
    CPP = "cpp"
    BASH = "bash"
    POWERSHELL = "powershell"


class ExecutionStatus(Enum):
    """Status of code execution"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    KILLED = "killed"
    SECURITY_VIOLATION = "security_violation"


@dataclass
class ExecutionResult:
    """Result of code execution"""
    status: ExecutionStatus
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    memory_used: int = 0
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    security_warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SandboxConfig:
    """Configuration for sandbox environment"""
    image: str = "python:3.11-slim"
    cpu_limit: str = "1.0"
    memory_limit: str = "512m"
    timeout: int = 60
    network_enabled: bool = False
    volume_mounts: Dict[str, str] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    workdir: str = "/sandbox"
    user: str = "nobody"
    security_scan: bool = True


class SecurityScanner:
    """
    Scans code for security issues before execution.
    
    Checks for:
    - Dangerous imports (os.system, subprocess with shell=True)
    - File system access outside sandbox
    - Network operations
    - Code injection patterns
    - Resource exhaustion patterns
    """
    
    DANGEROUS_PATTERNS = {
        Language.PYTHON: [
            "os.system",
            "subprocess.call.*shell=True",
            "subprocess.Popen.*shell=True",
            "eval(",
            "exec(",
            "__import__",
            "compile(",
            "open('/etc/",
            "open('/root",
            "os.popen",
            "commands.getoutput",
            "pickle.loads",
            "yaml.unsafe_load",
        ],
        Language.JAVASCRIPT: [
            "eval(",
            "Function(",
            "child_process.exec",
            "require('child_process').exec",
            "process.exit",
            "fs.unlinkSync('/",
        ],
        Language.BASH: [
            "rm -rf /",
            "mkfs",
            "dd if=",
            "> /dev/sd",
            "chmod 777 /",
            "chown root",
        ]
    }
    
    @classmethod
    def scan(cls, code: str, language: Language) -> List[str]:
        """Scan code for security issues"""
        warnings = []
        patterns = cls.DANGEROUS_PATTERNS.get(language, [])
        
        for pattern in patterns:
            if pattern in code:
                warnings.append(f"Potentially dangerous pattern found: {pattern}")
        
        # Check for infinite loops (basic detection)
        if language == Language.PYTHON:
            if "while True:" in code and "break" not in code:
                warnings.append("Possible infinite loop detected (while True without break)")
        
        return warnings


class CodeRunner:
    """
    Secure code execution in Docker sandbox.
    
    Usage:
        runner = CodeRunner()
        
        result = runner.execute(
            code='print("Hello, World!")',
            language=Language.PYTHON,
            config=SandboxConfig(timeout=30)
        )
        
        print(result.stdout)
    """
    
    def __init__(
        self,
        docker_url: Optional[str] = None,
        default_config: Optional[SandboxConfig] = None
    ):
        self.docker_url = docker_url or os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")
        self.default_config = default_config or SandboxConfig()
        self._temp_dirs: List[str] = []
        
        # Check Docker availability
        self._docker_available = self._check_docker()
    
    def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _create_temp_dir(self) -> str:
        """Create a temporary directory for execution"""
        temp_dir = tempfile.mkdtemp(prefix="synthia_sandbox_")
        self._temp_dirs.append(temp_dir)
        return temp_dir
    
    def _cleanup_temp_dirs(self):
        """Clean up all temporary directories"""
        for temp_dir in self._temp_dirs:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        self._temp_dirs.clear()
    
    def _get_file_extension(self, language: Language) -> str:
        """Get file extension for language"""
        extensions = {
            Language.PYTHON: ".py",
            Language.JAVASCRIPT: ".js",
            Language.TYPESCRIPT: ".ts",
            Language.GO: ".go",
            Language.RUST: ".rs",
            Language.JAVA: ".java",
            Language.C: ".c",
            Language.CPP: ".cpp",
            Language.BASH: ".sh",
            Language.POWERSHELL: ".ps1"
        }
        return extensions.get(language, ".txt")
    
    def _get_run_command(self, language: Language, filename: str) -> List[str]:
        """Get command to run code for language"""
        commands = {
            Language.PYTHON: ["python", filename],
            Language.JAVASCRIPT: ["node", filename],
            Language.TYPESCRIPT: ["npx", "ts-node", filename],
            Language.GO: ["go", "run", filename],
            Language.RUST: ["rustc", filename, "-o", "/tmp/out", "&&", "/tmp/out"],
            Language.JAVA: ["javac", filename, "&&", "java", filename.replace(".java", "")],
            Language.C: ["gcc", filename, "-o", "/tmp/out", "&&", "/tmp/out"],
            Language.CPP: ["g++", filename, "-o", "/tmp/out", "&&", "/tmp/out"],
            Language.BASH: ["bash", filename],
            Language.POWERSHELL: ["pwsh", "-File", filename]
        }
        return commands.get(language, ["cat", filename])
    
    def _build_docker_command(
        self,
        config: SandboxConfig,
        code_dir: str,
        command: List[str]
    ) -> List[str]:
        """Build Docker run command"""
        cmd = [
            "docker", "run",
            "--rm",
            "--name", f"synthia_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}",
            "--cpus", config.cpu_limit,
            "--memory", config.memory_limit,
            "--network", "none" if not config.network_enabled else "bridge",
            "-v", f"{code_dir}:{config.workdir}",
            "-w", config.workdir,
            "-u", config.user,
        ]
        
        # Add environment variables
        for key, value in config.environment.items():
            cmd.extend(["-e", f"{key}={value}"])
        
        # Add volume mounts
        for host_path, container_path in config.volume_mounts.items():
            cmd.extend(["-v", f"{host_path}:{container_path}"])
        
        cmd.append(config.image)
        cmd.extend(command)
        
        return cmd
    
    def execute(
        self,
        code: str,
        language: Language = Language.PYTHON,
        config: Optional[SandboxConfig] = None,
        files: Optional[Dict[str, str]] = None,
        stdin: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute code in sandbox.
        
        Args:
            code: Code to execute
            language: Programming language
            config: Sandbox configuration
            files: Additional files to create {filename: content}
            stdin: Input to pass via stdin
            
        Returns:
            ExecutionResult with output and status
        """
        config = config or self.default_config
        start_time = time.time()
        
        # Security scan if enabled
        security_warnings = []
        if config.security_scan:
            security_warnings = SecurityScanner.scan(code, language)
            if security_warnings:
                # Check for critical violations
                critical = [w for w in security_warnings if "dangerous" in w.lower()]
                if critical:
                    return ExecutionResult(
                        status=ExecutionStatus.SECURITY_VIOLATION,
                        stdout="",
                        stderr="\n".join(security_warnings),
                        exit_code=1,
                        execution_time=0,
                        security_warnings=security_warnings
                    )
        
        # Check Docker availability
        if not self._docker_available:
            return self._execute_local(code, language, config, files, stdin, security_warnings)
        
        # Create temp directory
        code_dir = self._create_temp_dir()
        
        try:
            # Write code file
            ext = self._get_file_extension(language)
            code_file = f"main{ext}"
            code_path = os.path.join(code_dir, code_file)
            
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            # Write additional files
            if files:
                for filename, content in files.items():
                    file_path = os.path.join(code_dir, filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
            
            # Build command
            run_cmd = self._get_run_command(language, code_file)
            docker_cmd = self._build_docker_command(config, code_dir, run_cmd)
            
            # Execute
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=config.timeout,
                input=stdin
            )
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if result.returncode == 0 else ExecutionStatus.FAILED,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time=execution_time,
                security_warnings=security_warnings
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                stdout="",
                stderr=f"Execution timed out after {config.timeout} seconds",
                exit_code=-1,
                execution_time=config.timeout,
                security_warnings=security_warnings
            )
            
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                stdout="",
                stderr=str(e),
                exit_code=1,
                execution_time=time.time() - start_time,
                security_warnings=security_warnings
            )
    
    def _execute_local(
        self,
        code: str,
        language: Language,
        config: SandboxConfig,
        files: Optional[Dict[str, str]],
        stdin: Optional[str],
        security_warnings: List[str]
    ) -> ExecutionResult:
        """Execute code locally (fallback when Docker unavailable)"""
        start_time = time.time()
        
        # Create temp directory
        code_dir = self._create_temp_dir()
        
        try:
            # Write code file
            ext = self._get_file_extension(language)
            code_file = f"main{ext}"
            code_path = os.path.join(code_dir, code_file)
            
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            # Write additional files
            if files:
                for filename, content in files.items():
                    file_path = os.path.join(code_dir, filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
            
            # Get interpreter
            interpreters = {
                Language.PYTHON: ["python3"],
                Language.JAVASCRIPT: ["node"],
                Language.BASH: ["bash"],
            }
            
            interpreter = interpreters.get(language)
            if not interpreter:
                return ExecutionResult(
                    status=ExecutionStatus.FAILED,
                    stdout="",
                    stderr=f"Language {language.value} not supported for local execution",
                    exit_code=1,
                    execution_time=0,
                    security_warnings=security_warnings
                )
            
            # Execute
            cmd = interpreter + [code_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config.timeout,
                input=stdin,
                cwd=code_dir
            )
            
            execution_time = time.time() - start_time
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if result.returncode == 0 else ExecutionStatus.FAILED,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time=execution_time,
                security_warnings=security_warnings
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                stdout="",
                stderr=f"Execution timed out after {config.timeout} seconds",
                exit_code=-1,
                execution_time=config.timeout,
                security_warnings=security_warnings
            )
            
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                stdout="",
                stderr=str(e),
                exit_code=1,
                execution_time=time.time() - start_time,
                security_warnings=security_warnings
            )
    
    def execute_project(
        self,
        project_path: str,
        language: Language = Language.PYTHON,
        config: Optional[SandboxConfig] = None,
        entry_point: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute an entire project in sandbox.
        
        Args:
            project_path: Path to project directory
            language: Primary language
            config: Sandbox configuration
            entry_point: Entry point file (e.g., "main.py")
            
        Returns:
            ExecutionResult
        """
        config = config or self.default_config
        
        # Find entry point
        if not entry_point:
            entry_points = {
                Language.PYTHON: ["main.py", "app.py", "run.py", "index.py"],
                Language.JAVASCRIPT: ["index.js", "main.js", "app.js", "server.js"],
                Language.GO: ["main.go"],
            }
            
            for ep in entry_points.get(language, []):
                if os.path.exists(os.path.join(project_path, ep)):
                    entry_point = ep
                    break
        
        if not entry_point:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                stdout="",
                stderr="No entry point found",
                exit_code=1,
                execution_time=0
            )
        
        # Read entry point code
        entry_path = os.path.join(project_path, entry_point)
        with open(entry_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        # Collect additional files
        files = {}
        for root, _, filenames in os.walk(project_path):
            for filename in filenames:
                if filename == entry_point:
                    continue
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, project_path)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        files[rel_path] = f.read()
                except Exception:
                    pass  # Skip binary files
        
        return self.execute(code, language, config, files)
    
    def cleanup(self):
        """Clean up resources"""
        self._cleanup_temp_dirs()
    
    def __del__(self):
        """Destructor - cleanup on exit"""
        self.cleanup()


# Convenience function for quick execution
def run_code(
    code: str,
    language: str = "python",
    timeout: int = 60
) -> ExecutionResult:
    """
    Quick code execution helper.
    
    Usage:
        result = run_code('print("Hello")', "python", timeout=30)
        print(result.stdout)
    """
    lang_map = {
        "python": Language.PYTHON,
        "javascript": Language.JAVASCRIPT,
        "js": Language.JAVASCRIPT,
        "typescript": Language.TYPESCRIPT,
        "ts": Language.TYPESCRIPT,
        "go": Language.GO,
        "rust": Language.RUST,
        "java": Language.JAVA,
        "c": Language.C,
        "cpp": Language.CPP,
        "bash": Language.BASH,
        "sh": Language.BASH,
    }
    
    lang = lang_map.get(language.lower(), Language.PYTHON)
    config = SandboxConfig(timeout=timeout)
    
    runner = CodeRunner()
    return runner.execute(code, lang, config)