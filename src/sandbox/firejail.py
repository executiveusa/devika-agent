"""
SYNTHIA Firejail Sandbox
========================
Additional security layer using Firejail for Linux systems.

Firejail is a Linux namespaces sandbox that provides:
- File system isolation
- Network isolation
- Resource limits
- Seccomp filters
- Capability dropping

This module provides an alternative to Docker for Linux systems
where Firejail is available.
"""

import os
import subprocess
import tempfile
import shutil
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .code_runner import (
    Language,
    ExecutionStatus,
    ExecutionResult,
    SandboxConfig,
    SecurityScanner
)


@dataclass
class FirejailConfig:
    """Configuration for Firejail sandbox"""
    # File system
    private_tmp: bool = True
    private_dev: bool = True
    private_etc: Optional[List[str]] = None  # List of allowed /etc files
    no_root: bool = True
    
    # Network
    net_none: bool = True
    net_filter: Optional[str] = None  # Custom network filter
    
    # Resources
    cpu_limit: Optional[int] = None  # CPU time in seconds
    memory_limit: Optional[int] = None  # Memory in MB
    
    # Security
    seccomp: bool = True
    caps_drop_all: bool = True
    no_debugger: bool = True
    no_new_privs: bool = True
    
    # Execution
    timeout: int = 60
    quiet: bool = True


class FirejailSandbox:
    """
    Firejail-based sandbox for Linux systems.
    
    Provides lightweight isolation without Docker overhead.
    Falls back gracefully if Firejail is not available.
    
    Usage:
        sandbox = FirejailSandbox()
        
        result = sandbox.execute(
            code='print("Hello")',
            language=Language.PYTHON,
            config=FirejailConfig(timeout=30)
        )
    """
    
    def __init__(self):
        self._firejail_available = self._check_firejail()
        self._temp_dirs: List[str] = []
    
    def _check_firejail(self) -> bool:
        """Check if Firejail is available"""
        try:
            result = subprocess.run(
                ["firejail", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def is_available(self) -> bool:
        """Check if Firejail sandbox is available"""
        return self._firejail_available
    
    def _create_temp_dir(self) -> str:
        """Create a temporary directory for execution"""
        temp_dir = tempfile.mkdtemp(prefix="synthia_firejail_")
        self._temp_dirs.append(temp_dir)
        return temp_dir
    
    def _cleanup(self):
        """Clean up temporary directories"""
        for temp_dir in self._temp_dirs:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        self._temp_dirs.clear()
    
    def _build_firejail_command(
        self,
        config: FirejailConfig,
        workdir: str,
        command: List[str]
    ) -> List[str]:
        """Build Firejail command with configuration"""
        cmd = ["firejail"]
        
        if config.quiet:
            cmd.append("--quiet")
        
        # File system isolation
        if config.private_tmp:
            cmd.append("--private-tmp")
        
        if config.private_dev:
            cmd.append("--private-dev")
        
        if config.private_etc:
            for etc_file in config.private_etc:
                cmd.extend(["--private-etc", etc_file])
        
        if config.no_root:
            cmd.append("--noroot")
        
        # Network isolation
        if config.net_none:
            cmd.append("--net=none")
        elif config.net_filter:
            cmd.extend(["--netfilter", config.net_filter])
        
        # Resource limits
        if config.cpu_limit:
            cmd.extend(["--rlimit-cpu", str(config.cpu_limit)])
        
        if config.memory_limit:
            cmd.extend(["--rlimit-as", str(config.memory_limit * 1024 * 1024)])
        
        # Security
        if config.seccomp:
            cmd.append("--seccomp")
        
        if config.caps_drop_all:
            cmd.append("--caps.drop=all")
        
        if config.no_debugger:
            cmd.append("--nodbg")
        
        if config.no_new_privs:
            cmd.append("--nonewprivs")
        
        # Working directory
        cmd.extend(["--private", workdir])
        
        # Command to execute
        cmd.append("--")
        cmd.extend(command)
        
        return cmd
    
    def _get_interpreter(self, language: Language) -> Optional[List[str]]:
        """Get interpreter command for language"""
        interpreters = {
            Language.PYTHON: ["python3"],
            Language.JAVASCRIPT: ["node"],
            Language.BASH: ["bash"],
            Language.GO: ["go", "run"],
        }
        return interpreters.get(language)
    
    def _get_file_extension(self, language: Language) -> str:
        """Get file extension for language"""
        extensions = {
            Language.PYTHON: ".py",
            Language.JAVASCRIPT: ".js",
            Language.BASH: ".sh",
            Language.GO: ".go",
        }
        return extensions.get(language, ".txt")
    
    def execute(
        self,
        code: str,
        language: Language = Language.PYTHON,
        config: Optional[FirejailConfig] = None,
        files: Optional[Dict[str, str]] = None,
        stdin: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute code in Firejail sandbox.
        
        Args:
            code: Code to execute
            language: Programming language
            config: Firejail configuration
            files: Additional files to create
            stdin: Input to pass via stdin
            
        Returns:
            ExecutionResult
        """
        if not self._firejail_available:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                stdout="",
                stderr="Firejail is not available on this system",
                exit_code=1,
                execution_time=0
            )
        
        config = config or FirejailConfig()
        start_time = time.time()
        
        # Security scan
        security_warnings = SecurityScanner.scan(code, language)
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
        
        # Create temp directory
        workdir = self._create_temp_dir()
        
        try:
            # Write code file
            ext = self._get_file_extension(language)
            code_file = f"main{ext}"
            code_path = os.path.join(workdir, code_file)
            
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            # Write additional files
            if files:
                for filename, content in files.items():
                    file_path = os.path.join(workdir, filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
            
            # Get interpreter
            interpreter = self._get_interpreter(language)
            if not interpreter:
                return ExecutionResult(
                    status=ExecutionStatus.FAILED,
                    stdout="",
                    stderr=f"Language {language.value} not supported",
                    exit_code=1,
                    execution_time=time.time() - start_time
                )
            
            # Build command
            command = interpreter + [code_file]
            firejail_cmd = self._build_firejail_command(config, workdir, command)
            
            # Execute
            result = subprocess.run(
                firejail_cmd,
                capture_output=True,
                text=True,
                timeout=config.timeout,
                input=stdin,
                cwd=workdir
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
    
    def execute_file(
        self,
        file_path: str,
        config: Optional[FirejailConfig] = None,
        stdin: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute an existing file in sandbox.
        
        Args:
            file_path: Path to file to execute
            config: Firejail configuration
            stdin: Input to pass via stdin
            
        Returns:
            ExecutionResult
        """
        if not os.path.exists(file_path):
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                stdout="",
                stderr=f"File not found: {file_path}",
                exit_code=1,
                execution_time=0
            )
        
        # Read file
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        
        # Detect language from extension
        ext = Path(file_path).suffix.lower()
        lang_map = {
            ".py": Language.PYTHON,
            ".js": Language.JAVASCRIPT,
            ".sh": Language.BASH,
            ".go": Language.GO,
        }
        language = lang_map.get(ext, Language.PYTHON)
        
        return self.execute(code, language, config, stdin=stdin)
    
    def __del__(self):
        """Cleanup on exit"""
        self._cleanup()


def create_sandbox():
    """
    Factory function to create the best available sandbox.
    
    Returns Docker sandbox if Docker is available,
    otherwise Firejail if available,
    otherwise falls back to basic local execution.
    """
    from .code_runner import CodeRunner
    
    # Try Docker first
    docker_runner = CodeRunner()
    if docker_runner._docker_available:
        return docker_runner
    
    # Try Firejail
    firejail = FirejailSandbox()
    if firejail.is_available():
        return firejail
    
    # Fallback to Docker runner (which will use local execution)
    return docker_runner