from typing import Any, Dict
import os
import subprocess


class PythonEnvBootstrapSkill:
    """Skill to bootstrap local Python environment using repo script."""

    @staticmethod
    def trigger_matches(text: str) -> bool:
        value = (text or "").lower()
        return (
            "bootstrap python env" in value
            or "setup python environment" in value
            or "python env fix" in value
        )

    def execute(self, context: Any, **kwargs) -> Dict[str, Any]:
        run_tests = bool(kwargs.get("run_tests", False))
        repo_root = kwargs.get("repo_root", os.getcwd())
        script_path = os.path.join(repo_root, "scripts", "bootstrap_python_env.ps1")

        if not os.path.exists(script_path):
            return {"ok": False, "error": f"Script not found: {script_path}"}

        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            script_path,
        ]
        if run_tests:
            cmd.append("-RunTests")

        try:
            proc = subprocess.run(
                cmd,
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            return {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "command": " ".join(cmd),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc), "command": " ".join(cmd)}
