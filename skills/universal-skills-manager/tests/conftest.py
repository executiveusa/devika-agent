import sys
from pathlib import Path

import pytest

# Add scripts dir to path so we can import scan_skill
sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "universal-skills-manager" / "scripts"),
)

from scan_skill import Finding, SkillScanner


@pytest.fixture
def scanner():
    """Fresh scanner instance per test."""
    return SkillScanner()


@pytest.fixture
def tmp_skill(tmp_path):
    """Create a temporary skill directory and return a helper."""

    class SkillDir:
        def __init__(self, base):
            self.base = base

        def add_file(self, name, content=""):
            p = self.base / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return p

        def add_symlink(self, name, target):
            p = self.base / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.symlink_to(target)
            return p

    return SkillDir(tmp_path)
