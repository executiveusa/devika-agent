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
- Ralphy execution engine (priority-based task execution)
- Agent Lightning mentor/trainer integration
- Quality gates for production-ready code
- Unified orchestrator
- Global skill sharing system (Universal Skills Manager integration)
- n8n workflow integration

Architecture:
    User Request → SYNTHIA Core → Memory Layer → Investigation → Execution → Quality Gates → Deployment
    
Flywheel Effect:
    SYNTHIA executes → Quality Gates validate → Agent Lightning observes/trains → Memory syncs → Improved execution

Skill Sharing:
    Skill Manager → Multi-source discovery → Security scan → Cross-tool sync → n8n integration
"""

from .core import SynthiaCore
from .memory import MemoryManager
from .webhook import ArchonXWebhook
from .agent_registry import AgentRegistry
from .orchestrator import (
    SynthiaOrchestrator, 
    ExecutionContext, 
    ExecutionReport,
    ExecutionMode,
    OrchestratorConfig
)
from .execution import RalphyExecutionEngine, TaskPriority, detect_priority
from .trainer import AgentLightning
from .skill_manager import (
    SkillManager,
    Skill,
    SkillSource,
    SkillScope,
    SearchResult,
    get_skill_manager,
)
from .n8n_integration import (
    N8nIntegration,
    N8nWorkflow,
    get_n8n_integration,
)

__version__ = "4.2.1"
__author__ = "SYNTHIA Team"
__all__ = [
    # Core
    "SynthiaCore",
    "MemoryManager", 
    "ArchonXWebhook",
    "AgentRegistry",
    
    # Orchestrator
    "SynthiaOrchestrator",
    "ExecutionContext",
    "ExecutionReport",
    "ExecutionMode",
    "OrchestratorConfig",
    
    # Ralphy Execution
    "RalphyExecutionEngine",
    "TaskPriority",
    "detect_priority",
    
    # Agent Lightning
    "AgentLightning",
    
    # Skill Manager
    "SkillManager",
    "Skill",
    "SkillSource",
    "SkillScope",
    "SearchResult",
    "get_skill_manager",
    
    # n8n Integration
    "N8nIntegration",
    "N8nWorkflow",
    "get_n8n_integration",
]
