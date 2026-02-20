"""Ralphy loop integration utilities.

Implements a deterministic priority loop that can be shared across agents.
Reference repository: https://github.com/michaelshimeles/ralphy.git
"""

from dataclasses import dataclass
from typing import Any, Iterable, List, Tuple


@dataclass
class RalphyDecision:
    priority: str
    reason: str


class RalphyLoop:
    """Local prioritization loop inspired by the Ralphy execution model."""

    ORDER = ["architectural", "integration", "unknown", "standard", "polish"]

    def classify(self, context: Any) -> RalphyDecision:
        text = ""
        if isinstance(context, dict):
            text = " ".join(str(v) for v in context.values() if v is not None).lower()
        else:
            text = str(context).lower()

        if any(k in text for k in ["architecture", "system design", "refactor core"]):
            return RalphyDecision(priority="architectural", reason="architecture-related objective")
        if any(k in text for k in ["integrate", "connect", "sync", "mcp", "agent mail", "beads"]):
            return RalphyDecision(priority="integration", reason="integration-related objective")
        if any(k in text for k in ["todo", "unknown", "investigate"]):
            return RalphyDecision(priority="unknown", reason="unknown/investigation objective")
        if any(k in text for k in ["ui polish", "style", "animation", "copy tweak"]):
            return RalphyDecision(priority="polish", reason="polish objective")
        return RalphyDecision(priority="standard", reason="default objective")

    def rank_items(self, items: Iterable[Any]) -> List[Tuple[Any, RalphyDecision]]:
        """Rank arbitrary work items according to the Ralphy priority order."""
        scored: List[Tuple[Any, RalphyDecision]] = []
        for item in items:
            decision = self.classify(item)
            scored.append((item, decision))
        scored.sort(key=lambda x: self.ORDER.index(x[1].priority))
        return scored
