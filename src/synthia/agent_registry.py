"""
SYNTHIA Agent Registry
=====================
Central registry for all agents in the SYNTHIA ecosystem.

Each agent has:
- Unique name and ID
- Defined capabilities and skills
- Memory and repo linking to Archon X
- Webhook for knowledge sync
- Execution interface

Agent Team Structure:
- Primary Agents: Always active (Planner, Researcher, Coder, Formatter)
- Action Agents: Triggered by user intent (Runner, Patcher, Feature, Reporter)
- Support Agents: Background operations (Architect, Tester, Documenter)
"""

import os
import json
from typing import Optional, Dict, List, Any, Type, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import importlib
import inspect


class AgentCategory(Enum):
    """Agent categories"""
    PRIMARY = "primary"        # Always active in execution
    ACTION = "action"          # Triggered by user intent
    SUPPORT = "support"        # Background operations
    DOMAIN = "domain"          # Domain-specific experts
    ORCHESTRATOR = "orchestrator"  # Coordinates other agents


class AgentCapability(Enum):
    """Agent capabilities"""
    PLANNING = "planning"
    RESEARCH = "research"
    CODING = "coding"
    TESTING = "testing"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    DESIGN = "design"
    SECURITY = "security"


@dataclass
class AgentMetadata:
    """Metadata for an agent"""
    name: str
    display_name: str
    description: str
    category: AgentCategory
    capabilities: List[AgentCapability]
    triggers: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "SYNTHIA Team"
    repo_url: Optional[str] = None
    memory_namespace: str = ""
    webhook_enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentInfo:
    """Complete agent information"""
    metadata: AgentMetadata
    module_path: str
    class_name: str
    is_loaded: bool = False
    last_execution: Optional[str] = None
    execution_count: int = 0
    error_count: int = 0


class AgentRegistry:
    """
    Central registry for all SYNTHIA agents.
    
    Manages agent discovery, loading, and execution.
    Each agent has its own memory namespace and syncs to Archon X.
    
    Usage:
        registry = AgentRegistry()
        
        # Register an agent
        registry.register(
            name="planner",
            module_path="src.agents.planner.planner",
            class_name="Planner",
            metadata=AgentMetadata(
                name="planner",
                display_name="Planner",
                description="Creates step-by-step plans",
                category=AgentCategory.PRIMARY,
                capabilities=[AgentCapability.PLANNING]
            )
        )
        
        # Get an agent
        planner = registry.get_agent("planner")
        
        # List all agents
        agents = registry.list_agents()
    """
    
    def __init__(self, auto_discover: bool = True):
        self._agents: Dict[str, AgentInfo] = {}
        self._instances: Dict[str, Any] = {}
        self._hooks: Dict[str, List[Callable]] = {
            "pre_execute": [],
            "post_execute": [],
            "on_error": []
        }
        
        if auto_discover:
            self._discover_builtin_agents()
            # Attempt to register Ralphy enforcement hook so every agent
            # goes through the Ralphy priority checks before execution.
            try:
                from .ralphy_enforcer import enforce as _ralphy_enforce
                self.register_hook("pre_execute", _ralphy_enforce)
            except Exception:
                # Non-fatal if enforcer is not present
                pass
    
    def _discover_builtin_agents(self):
        """Discover and register built-in agents from Devika"""
        builtin_agents = [
            # Primary Agents
            {
                "name": "planner",
                "module_path": "src.agents.planner.planner",
                "class_name": "Planner",
                "metadata": AgentMetadata(
                    name="planner",
                    display_name="Planner",
                    description="Creates step-by-step execution plans from user prompts",
                    category=AgentCategory.PRIMARY,
                    capabilities=[AgentCapability.PLANNING, AgentCapability.ANALYSIS],
                    triggers=["new_project", "new_task"],
                    memory_namespace="planner"
                )
            },
            {
                "name": "researcher",
                "module_path": "src.agents.researcher.researcher",
                "class_name": "Researcher",
                "metadata": AgentMetadata(
                    name="researcher",
                    display_name="Researcher",
                    description="Extracts search queries and gathers relevant information",
                    category=AgentCategory.PRIMARY,
                    capabilities=[AgentCapability.RESEARCH, AgentCapability.ANALYSIS],
                    triggers=["after_planning"],
                    dependencies=["planner"],
                    memory_namespace="researcher"
                )
            },
            {
                "name": "coder",
                "module_path": "src.agents.coder.coder",
                "class_name": "Coder",
                "metadata": AgentMetadata(
                    name="coder",
                    display_name="Coder",
                    description="Generates multi-file code projects based on plans",
                    category=AgentCategory.PRIMARY,
                    capabilities=[AgentCapability.CODING, AgentCapability.DESIGN],
                    triggers=["after_research"],
                    dependencies=["planner", "researcher"],
                    memory_namespace="coder"
                )
            },
            {
                "name": "formatter",
                "module_path": "src.agents.formatter.formatter",
                "class_name": "Formatter",
                "metadata": AgentMetadata(
                    name="formatter",
                    display_name="Formatter",
                    description="Cleans and formats crawled web content",
                    category=AgentCategory.PRIMARY,
                    capabilities=[AgentCapability.ANALYSIS],
                    triggers=["during_research"],
                    memory_namespace="formatter"
                )
            },
            # Action Agents
            {
                "name": "action",
                "module_path": "src.agents.action.action",
                "class_name": "Action",
                "metadata": AgentMetadata(
                    name="action",
                    display_name="Action Router",
                    description="Routes user intent to appropriate action agent",
                    category=AgentCategory.ORCHESTRATOR,
                    capabilities=[AgentCapability.ANALYSIS],
                    triggers=["follow_up_message"],
                    memory_namespace="action"
                )
            },
            {
                "name": "runner",
                "module_path": "src.agents.runner.runner",
                "class_name": "Runner",
                "metadata": AgentMetadata(
                    name="runner",
                    display_name="Runner",
                    description="Executes code commands in sandboxed environment",
                    category=AgentCategory.ACTION,
                    capabilities=[AgentCapability.TESTING, AgentCapability.DEPLOYMENT],
                    triggers=["run", "execute", "test"],
                    memory_namespace="runner"
                )
            },
            {
                "name": "patcher",
                "module_path": "src.agents.patcher.patcher",
                "class_name": "Patcher",
                "metadata": AgentMetadata(
                    name="patcher",
                    display_name="Patcher",
                    description="Debugs and fixes issues in existing code",
                    category=AgentCategory.ACTION,
                    capabilities=[AgentCapability.DEBUGGING, AgentCapability.CODING],
                    triggers=["bug", "fix", "error", "patch"],
                    memory_namespace="patcher"
                )
            },
            {
                "name": "feature",
                "module_path": "src.agents.feature.feature",
                "class_name": "Feature",
                "metadata": AgentMetadata(
                    name="feature",
                    display_name="Feature Implementer",
                    description="Implements new features in existing projects",
                    category=AgentCategory.ACTION,
                    capabilities=[AgentCapability.CODING, AgentCapability.DESIGN],
                    triggers=["feature", "implement", "add"],
                    memory_namespace="feature"
                )
            },
            {
                "name": "reporter",
                "module_path": "src.agents.reporter.reporter",
                "class_name": "Reporter",
                "metadata": AgentMetadata(
                    name="reporter",
                    display_name="Reporter",
                    description="Generates comprehensive project reports and documentation",
                    category=AgentCategory.ACTION,
                    capabilities=[AgentCapability.DOCUMENTATION],
                    triggers=["report", "document", "summary"],
                    memory_namespace="reporter"
                )
            },
            {
                "name": "answer",
                "module_path": "src.agents.answer.answer",
                "class_name": "Answer",
                "metadata": AgentMetadata(
                    name="answer",
                    display_name="Answer Agent",
                    description="Provides direct answers to user questions",
                    category=AgentCategory.ACTION,
                    capabilities=[AgentCapability.ANALYSIS],
                    triggers=["question", "explain", "what", "how", "why"],
                    memory_namespace="answer"
                )
            },
            # Decision Agent
            {
                "name": "decision",
                "module_path": "src.agents.decision.decision",
                "class_name": "Decision",
                "metadata": AgentMetadata(
                    name="decision",
                    display_name="Decision Agent",
                    description="Handles special commands and routing decisions",
                    category=AgentCategory.ORCHESTRATOR,
                    capabilities=[AgentCapability.ANALYSIS],
                    triggers=["git_clone", "browser", "pdf"],
                    memory_namespace="decision"
                )
            },
            # Internal Monologue
            {
                "name": "internal_monologue",
                "module_path": "src.agents.internal_monologue.internal_monologue",
                "class_name": "InternalMonologue",
                "metadata": AgentMetadata(
                    name="internal_monologue",
                    display_name="Internal Monologue",
                    description="Tracks agent thoughts and reasoning process",
                    category=AgentCategory.SUPPORT,
                    capabilities=[AgentCapability.ANALYSIS],
                    triggers=["always"],
                    memory_namespace="monologue"
                )
            },
            # SYNTHIA-specific agents
            {
                "name": "architect",
                "module_path": "src.synthia.agents.architect",
                "class_name": "Architect",
                "metadata": AgentMetadata(
                    name="architect",
                    display_name="Architect",
                    description="Designs system architecture and component relationships",
                    category=AgentCategory.SUPPORT,
                    capabilities=[AgentCapability.DESIGN, AgentCapability.ANALYSIS],
                    triggers=["architecture", "design", "structure"],
                    memory_namespace="architect"
                )
            },
            {
                "name": "tester",
                "module_path": "src.synthia.agents.tester",
                "class_name": "Tester",
                "metadata": AgentMetadata(
                    name="tester",
                    display_name="Quality Assurance Tester",
                    description="Generates and runs tests, validates code quality",
                    category=AgentCategory.SUPPORT,
                    capabilities=[AgentCapability.TESTING, AgentCapability.SECURITY],
                    triggers=["test", "validate", "quality"],
                    memory_namespace="tester"
                )
            },
            {
                "name": "documenter",
                "module_path": "src.synthia.agents.documenter",
                "class_name": "Documenter",
                "metadata": AgentMetadata(
                    name="documenter",
                    display_name="Documenter",
                    description="Generates documentation and code comments",
                    category=AgentCategory.SUPPORT,
                    capabilities=[AgentCapability.DOCUMENTATION],
                    triggers=["document", "readme", "docs"],
                    memory_namespace="documenter"
                )
            },
            {
                "name": "security",
                "module_path": "src.synthia.agents.security",
                "class_name": "Security",
                "metadata": AgentMetadata(
                    name="security",
                    display_name="Security Analyst",
                    description="Analyzes code for security vulnerabilities",
                    category=AgentCategory.SUPPORT,
                    capabilities=[AgentCapability.SECURITY, AgentCapability.ANALYSIS],
                    triggers=["security", "vulnerability", "audit"],
                    memory_namespace="security"
                )
            }
            ,
            {
                "name": "ast",
                "module_path": "src.synthia.agents.ast_agent",
                "class_name": "ASTAgent",
                "metadata": AgentMetadata(
                    name="ast",
                    display_name="AST Analyzer",
                    description="Performs static AST analysis and suggests fixes",
                    category=AgentCategory.SUPPORT,
                    capabilities=[AgentCapability.ANALYSIS, AgentCapability.CODING],
                    triggers=["analyze", "lint", "ast", "static-analysis"],
                    memory_namespace="ast"
                )
            }
            ,
            {
                "name": "brenner",
                "module_path": "src.synthia.skills.brenner_skill.brenner_skill",
                "class_name": "BrennerSkill",
                "metadata": AgentMetadata(
                    name="brenner",
                    display_name="Brenner Skill",
                    description="Bridge to the Brenner Bot deep-reasoning service (simulated by default)",
                    category=AgentCategory.DOMAIN,
                    capabilities=[AgentCapability.ANALYSIS],
                    triggers=["brenner:deepreason", "brenner"],
                    memory_namespace="brenner"
                )
            }
            ,
            {
                "name": "python_env_bootstrap",
                "module_path": "src.synthia.skills.python_env_bootstrap.python_env_bootstrap",
                "class_name": "PythonEnvBootstrapSkill",
                "metadata": AgentMetadata(
                    name="python_env_bootstrap",
                    display_name="Python Env Bootstrap",
                    description="Bootstraps local Python environment and requirements via a deterministic script",
                    category=AgentCategory.DOMAIN,
                    capabilities=[AgentCapability.DEPLOYMENT, AgentCapability.TESTING],
                    triggers=["bootstrap python env", "setup python environment", "python env fix"],
                    memory_namespace="python_env_bootstrap"
                )
            }
        ]
        
        for agent_def in builtin_agents:
            self.register(
                name=agent_def["name"],
                module_path=agent_def["module_path"],
                class_name=agent_def["class_name"],
                metadata=agent_def["metadata"]
            )
    
    def register(
        self,
        name: str,
        module_path: str,
        class_name: str,
        metadata: AgentMetadata
    ) -> bool:
        """
        Register a new agent.
        
        Args:
            name: Unique agent name
            module_path: Python module path
            class_name: Agent class name
            metadata: Agent metadata
            
        Returns:
            True if registered successfully
        """
        if name in self._agents:
            return False
        
        self._agents[name] = AgentInfo(
            metadata=metadata,
            module_path=module_path,
            class_name=class_name
        )
        
        return True
    
    def unregister(self, name: str) -> bool:
        """Unregister an agent"""
        if name in self._agents:
            del self._agents[name]
            if name in self._instances:
                del self._instances[name]
            return True
        return False
    
    def get_agent(self, name: str) -> Optional[Any]:
        """
        Get an agent instance by name.
        
        Loads the agent class if not already loaded.
        Returns None if agent not found.
        """
        if name not in self._agents:
            return None
        
        agent_info = self._agents[name]
        
        # Return cached instance if available
        if name in self._instances:
            return self._instances[name]
        
        # Try to load the agent class
        try:
            module = importlib.import_module(agent_info.module_path)
            agent_class = getattr(module, agent_info.class_name)
            
            # Create instance
            instance = agent_class()
            self._instances[name] = instance
            agent_info.is_loaded = True
            
            return instance
            
        except ImportError as e:
            print(f"Failed to import agent {name}: {e}")
            return None
        except AttributeError as e:
            print(f"Agent class not found for {name}: {e}")
            return None
        except Exception as e:
            print(f"Failed to instantiate agent {name}: {e}")
            return None
    
    def get_agent_metadata(self, name: str) -> Optional[AgentMetadata]:
        """Get agent metadata by name"""
        if name in self._agents:
            return self._agents[name].metadata
        return None
    
    def list_agents(
        self,
        category: Optional[AgentCategory] = None,
        capability: Optional[AgentCapability] = None
    ) -> List[AgentMetadata]:
        """
        List all registered agents.
        
        Optionally filter by category or capability.
        """
        agents = []
        
        for agent_info in self._agents.values():
            if category and agent_info.metadata.category != category:
                continue
            if capability and capability not in agent_info.metadata.capabilities:
                continue
            agents.append(agent_info.metadata)
        
        return agents
    
    def get_agents_by_trigger(self, trigger: str) -> List[AgentMetadata]:
        """Get agents that respond to a specific trigger"""
        agents = []
        for agent_info in self._agents.values():
            if trigger.lower() in [t.lower() for t in agent_info.metadata.triggers]:
                agents.append(agent_info.metadata)
        return agents
    
    def get_agents_by_capability(
        self,
        capability: AgentCapability
    ) -> List[AgentMetadata]:
        """Get agents with a specific capability"""
        return self.list_agents(capability=capability)
    
    def register_hook(
        self,
        hook_name: str,
        callback: Callable
    ):
        """Register a hook callback"""
        if hook_name in self._hooks:
            self._hooks[hook_name].append(callback)
    
    def _run_hooks(
        self,
        hook_name: str,
        agent_name: str,
        *args,
        **kwargs
    ):
        """Run hooks for an event"""
        if hook_name in self._hooks:
            for callback in self._hooks[hook_name]:
                try:
                    callback(agent_name, *args, **kwargs)
                except Exception as e:
                    print(f"Hook callback error: {e}")
    
    def execute_agent(
        self,
        name: str,
        context: Any,
        **kwargs
    ) -> Any:
        """
        Execute an agent with context.
        
        Runs pre/post hooks and tracks execution.
        """
        agent = self.get_agent(name)
        if not agent:
            raise ValueError(f"Agent '{name}' not found")
        
        agent_info = self._agents[name]
        
        # Run pre-execute hooks
        self._run_hooks("pre_execute", name, context)
        
        try:
            # Execute agent
            result = agent.execute(context, **kwargs)
            
            # Update stats
            agent_info.last_execution = datetime.utcnow().isoformat()
            agent_info.execution_count += 1
            
            # Run post-execute hooks
            self._run_hooks("post_execute", name, context, result)
            
            return result
            
        except Exception as e:
            agent_info.error_count += 1
            self._run_hooks("on_error", name, context, e)
            raise
    
    def get_team_structure(self) -> Dict[str, List[Dict]]:
        """Get the complete agent team structure"""
        structure = {}
        
        for category in AgentCategory:
            agents = self.list_agents(category=category)
            structure[category.value] = [
                {
                    "name": a.name,
                    "display_name": a.display_name,
                    "description": a.description,
                    "capabilities": [c.value for c in a.capabilities],
                    "triggers": a.triggers
                }
                for a in agents
            ]
        
        return structure
    
    def export_registry(self) -> Dict:
        """Export registry for Archon X sync"""
        return {
            "agents": [
                {
                    "name": info.metadata.name,
                    "display_name": info.metadata.display_name,
                    "description": info.metadata.description,
                    "category": info.metadata.category.value,
                    "capabilities": [c.value for c in info.metadata.capabilities],
                    "triggers": info.metadata.triggers,
                    "dependencies": info.metadata.dependencies,
                    "version": info.metadata.version,
                    "is_loaded": info.is_loaded,
                    "execution_count": info.execution_count,
                    "error_count": info.error_count
                }
                for info in self._agents.values()
            ]
        }
    
    def import_registry(self, data: Dict) -> int:
        """Import registry data"""
        count = 0
        for agent_data in data.get("agents", []):
            try:
                metadata = AgentMetadata(
                    name=agent_data["name"],
                    display_name=agent_data["display_name"],
                    description=agent_data["description"],
                    category=AgentCategory(agent_data["category"]),
                    capabilities=[AgentCapability(c) for c in agent_data.get("capabilities", [])],
                    triggers=agent_data.get("triggers", []),
                    dependencies=agent_data.get("dependencies", []),
                    version=agent_data.get("version", "1.0.0")
                )
                # Note: module_path and class_name would need to be provided
                count += 1
            except Exception as e:
                print(f"Failed to import agent: {e}")
        
        return count
    
    def get_stats(self) -> Dict:
        """Get registry statistics"""
        return {
            "total_agents": len(self._agents),
            "loaded_agents": sum(1 for a in self._agents.values() if a.is_loaded),
            "total_executions": sum(a.execution_count for a in self._agents.values()),
            "total_errors": sum(a.error_count for a in self._agents.values()),
            "by_category": {
                cat.value: len(self.list_agents(category=cat))
                for cat in AgentCategory
            }
        }