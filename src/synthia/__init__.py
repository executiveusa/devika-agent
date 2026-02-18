"""
SYNTHIA Core Integration Module
===============================
The central nervous system for Devika AI Software Engineer.

This module provides:
- System prompt management
- Memory layer integration (ByteRover)
- LLM abstraction layer
- MCP server registry
- Agent swarm orchestration
- Archon X webhook integration

Architecture:
    User Request → SYNTHIA Core → Memory Layer → Investigation → Execution → Quality Gates → Deployment
"""

from .core import SynthiaCore
from .memory import MemoryManager
from .webhook import ArchonXWebhook
from .agent_registry import AgentRegistry

__version__ = "4.2.0"
__author__ = "SYNTHIA Team"
__all__ = [
    "SynthiaCore",
    "MemoryManager", 
    "ArchonXWebhook",
    "AgentRegistry",
]
