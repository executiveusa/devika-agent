"""
SYNTHIA Agents Package
======================
Specialized agents for various tasks in the SYNTHIA ecosystem.

Each agent follows the Ralphy pattern:
- Small, focused execution
- One task per agent
- Clear input/output
- Memory integration
- Archon X webhook sync
"""

from .architect import Architect
from .tester import Tester
from .documenter import Documenter
from .security import Security

__all__ = [
    "Architect",
    "Tester",
    "Documenter",
    "Security",
]