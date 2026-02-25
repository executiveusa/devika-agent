"""Run dependency and static analysis audits with fail-fast behavior."""

import subprocess
import sys


def _run(cmd):
    print(f"[audit] running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=False).returncode


def main() -> int:
    failures = 0

    # Prefer module invocation for deterministic behavior in virtualenvs.
    failures += _run([sys.executable, "-m", "pip_audit", "-r", "requirements.txt"])
    failures += _run([sys.executable, "-m", "bandit", "-q", "-r", "src"])

    # Semgrep may be unavailable in some runners; keep it optional but visible.
    try:
        semgrep_rc = subprocess.run(["semgrep", "scan", "src", "--error"], check=False).returncode
        failures += semgrep_rc
    except FileNotFoundError:
        print("[audit] semgrep command not found; skipping semgrep")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
