"""Ralphy enforcement hook

Implements a lightweight pre-execute hook that enforces the Ralphy execution
pattern (Architectural > Integration > Unknown > Standard > Polish) and
applies simple checks before agents run. This file is intentionally local and
minimal — it should be expanded to call into the Ralphy reference repo if
desired.
"""
from typing import Any
from .agent_registry import AgentMetadata
from .ralphy_loop import RalphyLoop


def enforce(agent_name: str, context: Any, *args, **kwargs):
    """Pre-execute hook registered by AgentRegistry.

    Current behavior:
    - Logs (prints) the Ralphy-priority for the given context when available
    - Injects a `ralphy_priority` flag into context if missing
    This is a safe, idempotent enforcer that other agents can rely on.
    """
    try:
        loop = RalphyLoop()
        if isinstance(context, dict):
            if "ralphy_priority" not in context:
                decision = loop.classify(context)
                context["ralphy_priority"] = decision.priority
                context["ralphy_reason"] = decision.reason
        else:
            # not a dict; no-op
            pass
    except Exception as e:
        print(f"Ralphy enforcer error for {agent_name}: {e}")
