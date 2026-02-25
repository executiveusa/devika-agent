"""Production smoke tests for scheduled CI runs."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


TESTS = [
    "tests/test_brenner_skill.py",
    "tests/test_ralphy_loop.py",
    "tests/test_quality_imports.py",
]


def main() -> int:
    compile_step = subprocess.run([sys.executable, "-m", "compileall", "src"], check=False)
    if compile_step.returncode != 0:
        return compile_step.returncode

    test_step = subprocess.run([sys.executable, "-m", "pytest", "-q", *TESTS], check=False)
    return test_step.returncode


if __name__ == "__main__":
    raise SystemExit(main())
