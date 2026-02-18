"""
SYNTHIA Core - The Central Nervous System
=========================================
Orchestrates all agent operations, memory management, and task execution.

Based on Ralphy's execution patterns and Agent Zero's architecture.
"""

import os
import json
import time
import hashlib
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .memory import MemoryManager, MemoryLayer
from .webhook import ArchonXWebhook
from .agent_registry import AgentRegistry


class AgentState(Enum):
    """Agent execution states"""
    IDLE = "idle"
    INVESTIGATING = "investigating"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(Enum):
    """Task priority levels based on Ralphy's prioritization"""
    ARCHITECTURAL = 1      # Core abstractions and foundation
    INTEGRATION = 2        # Module connection points
    UNKNOWN = 3            # Spike work and de-risking
    STANDARD = 4           # Regular features
    POLISH = 5             # Cleanup and quick wins


@dataclass
class AgentContext:
    """Context passed between agents during execution"""
    project_name: str
    task_id: str
    user_prompt: str
    step_plan: List[str] = field(default_factory=list)
    researched_context: Dict[str, Any] = field(default_factory=dict)
    generated_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result of a task execution"""
    success: bool
    task_id: str
    agent_name: str
    output: str
    files_modified: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    token_usage: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SynthiaCore:
    """
    The central orchestrator for all SYNTHIA operations.
    
    Responsibilities:
    - Coordinate agent swarm execution
    - Manage memory layers (project, team, global)
    - Handle task prioritization and delegation
    - Integrate with Archon X for knowledge sync
    - Provide real-time state updates
    
    Usage:
        core = SynthiaCore()
        result = await core.execute("Create a landing page for a crypto startup")
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        archon_x_webhook_url: Optional[str] = None,
        memory_backend: str = "sqlite",
        max_parallel_agents: int = 4,
        enable_telemetry: bool = True
    ):
        self.config = config or {}
        self.state = AgentState.IDLE
        self.memory = MemoryManager(backend=memory_backend)
        self.webhook = ArchonXWebhook(
            url=archon_x_webhook_url or os.getenv("ARCHON_X_WEBHOOK_URL", "")
        )
        self.registry = AgentRegistry()
        self.max_parallel_agents = max_parallel_agents
        self.enable_telemetry = enable_telemetry
        
        # Execution tracking
        self._current_task_id: Optional[str] = None
        self._execution_history: List[TaskResult] = []
        self._active_agents: Dict[str, AgentState] = {}
        self._lock = threading.Lock()
        
        # Callbacks for real-time updates
        self._state_callbacks: List[Callable] = []
        self._progress_callbacks: List[Callable] = []
        
        # Initialize from Ralphy patterns
        self._init_from_ralphy_patterns()
    
    def _init_from_ralphy_patterns(self):
        """Initialize execution patterns from Ralphy reference"""
        # Task prioritization from Ralphy
        self.priority_order = [
            TaskPriority.ARCHITECTURAL,
            TaskPriority.INTEGRATION,
            TaskPriority.UNKNOWN,
            TaskPriority.STANDARD,
            TaskPriority.POLISH
        ]
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2.0
        
        # Quality gates
        self.quality_gates_enabled = True
        self.lighthouse_target = 95
        self.accessibility_level = "WCAG2.1_AA"
    
    def register_state_callback(self, callback: Callable):
        """Register a callback for state changes"""
        self._state_callbacks.append(callback)
    
    def register_progress_callback(self, callback: Callable):
        """Register a callback for progress updates"""
        self._progress_callbacks.append(callback)
    
    def _emit_state(self, state: AgentState, context: Optional[Dict] = None):
        """Emit state change to all registered callbacks"""
        self.state = state
        payload = {
            "state": state.value,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {}
        }
        for callback in self._state_callbacks:
            try:
                callback(payload)
            except Exception as e:
                print(f"State callback error: {e}")
    
    def _emit_progress(self, agent_name: str, progress: float, message: str):
        """Emit progress update to all registered callbacks"""
        payload = {
            "agent": agent_name,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        for callback in self._progress_callbacks:
            try:
                callback(payload)
            except Exception as e:
                print(f"Progress callback error: {e}")
    
    def generate_task_id(self, prompt: str) -> str:
        """Generate a unique task ID based on prompt and timestamp"""
        content = f"{prompt}:{datetime.utcnow().isoformat()}:{os.urandom(4).hex()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def plan_execution(self, prompt: str, context: AgentContext) -> List[Dict]:
        """
        Create an execution plan based on the prompt.
        
        Uses Ralphy's task prioritization:
        1. Architectural decisions first
        2. Integration points second
        3. Unknown/spike work third
        4. Standard features fourth
        5. Polish last
        """
        # Check memory for similar past executions
        similar = self.memory.search(
            query=prompt,
            layer=MemoryLayer.GLOBAL,
            limit=5
        )
        
        # Build execution plan
        plan = []
        
        # Phase 1: Investigation (always first)
        plan.append({
            "phase": "investigation",
            "priority": TaskPriority.ARCHITECTURAL,
            "agents": ["planner", "researcher"],
            "description": "Analyze requirements and gather context"
        })
        
        # Phase 2: Architecture (if complex task)
        if self._is_complex_task(prompt):
            plan.append({
                "phase": "architecture",
                "priority": TaskPriority.ARCHITECTURAL,
                "agents": ["architect"],
                "description": "Design system architecture"
            })
        
        # Phase 3: Implementation
        plan.append({
            "phase": "implementation",
            "priority": TaskPriority.STANDARD,
            "agents": ["coder"],
            "description": "Generate code based on plan"
        })
        
        # Phase 4: Quality Gates
        if self.quality_gates_enabled:
            plan.append({
                "phase": "quality",
                "priority": TaskPriority.INTEGRATION,
                "agents": ["tester", "linter"],
                "description": "Run tests and quality checks"
            })
        
        # Phase 5: Polish
        plan.append({
            "phase": "polish",
            "priority": TaskPriority.POLISH,
            "agents": ["formatter", "documenter"],
            "description": "Format code and generate docs"
        })
        
        return plan
    
    def _is_complex_task(self, prompt: str) -> bool:
        """Determine if a task requires architectural planning"""
        complexity_indicators = [
            "architecture", "system", "multiple", "integrate",
            "api", "database", "authentication", "microservice",
            "scale", "distributed", "real-time"
        ]
        prompt_lower = prompt.lower()
        return any(indicator in prompt_lower for indicator in complexity_indicators)
    
    def execute_agent(
        self,
        agent_name: str,
        context: AgentContext,
        **kwargs
    ) -> TaskResult:
        """Execute a single agent and return the result"""
        start_time = time.time()
        
        # Get agent from registry
        agent = self.registry.get_agent(agent_name)
        if not agent:
            return TaskResult(
                success=False,
                task_id=context.task_id,
                agent_name=agent_name,
                output="",
                errors=[f"Agent '{agent_name}' not found in registry"]
            )
        
        # Update state
        self._active_agents[agent_name] = AgentState.EXECUTING
        self._emit_progress(agent_name, 0.0, f"Starting {agent_name} execution")
        
        try:
            # Execute with retry logic from Ralphy
            result = self._execute_with_retry(agent, context, **kwargs)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Create result
            task_result = TaskResult(
                success=True,
                task_id=context.task_id,
                agent_name=agent_name,
                output=result.get("output", ""),
                files_modified=result.get("files_modified", []),
                files_created=result.get("files_created", []),
                execution_time=execution_time,
                token_usage=result.get("token_usage", 0),
                metadata=result.get("metadata", {})
            )
            
            # Store in memory
            self.memory.store(
                key=f"task:{context.task_id}:{agent_name}",
                value=task_result.__dict__,
                layer=MemoryLayer.PROJECT,
                project_name=context.project_name
            )
            
            # Sync to Archon X
            self.webhook.sync_knowledge(
                agent_name=agent_name,
                task_id=context.task_id,
                result=task_result.__dict__
            )
            
            self._emit_progress(agent_name, 1.0, f"{agent_name} completed successfully")
            return task_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TaskResult(
                success=False,
                task_id=context.task_id,
                agent_name=agent_name,
                output="",
                errors=[str(e)],
                execution_time=execution_time
            )
        finally:
            self._active_agents[agent_name] = AgentState.IDLE
    
    def _execute_with_retry(
        self,
        agent: Any,
        context: AgentContext,
        **kwargs
    ) -> Dict:
        """Execute agent with retry logic from Ralphy patterns"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return agent.execute(context, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        raise last_error
    
    def execute_parallel(
        self,
        agents: List[str],
        context: AgentContext,
        **kwargs
    ) -> List[TaskResult]:
        """
        Execute multiple agents in parallel.
        
        Based on Ralphy's parallel execution pattern with worktrees.
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_parallel_agents) as executor:
            futures = {
                executor.submit(
                    self.execute_agent, agent, context, **kwargs
                ): agent for agent in agents
            }
            
            for future in as_completed(futures):
                agent = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(TaskResult(
                        success=False,
                        task_id=context.task_id,
                        agent_name=agent,
                        output="",
                        errors=[str(e)]
                    ))
        
        return results
    
    def execute(self, prompt: str, project_name: str = "default") -> TaskResult:
        """
        Main entry point for task execution.
        
        Orchestrates the full pipeline:
        1. Create context
        2. Plan execution
        3. Execute phases
        4. Run quality gates
        5. Return result
        """
        # Generate task ID
        task_id = self.generate_task_id(prompt)
        
        # Create context
        context = AgentContext(
            project_name=project_name,
            task_id=task_id,
            user_prompt=prompt
        )
        
        # Store initial context in memory
        self.memory.store(
            key=f"context:{task_id}",
            value={"prompt": prompt, "project": project_name},
            layer=MemoryLayer.PROJECT,
            project_name=project_name
        )
        
        # Emit state
        self._emit_state(AgentState.PLANNING, {"task_id": task_id})
        
        # Create execution plan
        plan = self.plan_execution(prompt, context)
        context.step_plan = [p["phase"] for p in plan]
        
        # Execute each phase
        all_results = []
        for phase in plan:
            self._emit_state(AgentState.EXECUTING, {
                "phase": phase["phase"],
                "agents": phase["agents"]
            })
            
            # Execute agents for this phase
            if len(phase["agents"]) == 1:
                result = self.execute_agent(
                    phase["agents"][0],
                    context,
                    **phase.get("params", {})
                )
                all_results.append(result)
            else:
                results = self.execute_parallel(
                    phase["agents"],
                    context,
                    **phase.get("params", {})
                )
                all_results.extend(results)
            
            # Check for failures
            failures = [r for r in all_results if not r.success]
            if failures:
                context.errors.extend([e for f in failures for e in f.errors])
        
        # Determine final result
        final_result = self._aggregate_results(all_results, context)
        
        # Store final result
        self._execution_history.append(final_result)
        
        # Sync to Archon X
        self.webhook.sync_task_completion(
            task_id=task_id,
            project_name=project_name,
            result=final_result.__dict__
        )
        
        # Emit final state
        self._emit_state(
            AgentState.COMPLETED if final_result.success else AgentState.FAILED,
            {"task_id": task_id}
        )
        
        return final_result
    
    def _aggregate_results(
        self,
        results: List[TaskResult],
        context: AgentContext
    ) -> TaskResult:
        """Aggregate multiple agent results into a single result"""
        success = all(r.success for r in results)
        
        return TaskResult(
            success=success,
            task_id=context.task_id,
            agent_name="orchestrator",
            output="\n".join([r.output for r in results if r.output]),
            files_modified=list(set(
                f for r in results for f in r.files_modified
            )),
            files_created=list(set(
                f for r in results for f in r.files_created
            )),
            errors=context.errors,
            execution_time=sum(r.execution_time for r in results),
            token_usage=sum(r.token_usage for r in results),
            metadata={
                "agents_executed": [r.agent_name for r in results],
                "phases_completed": context.step_plan
            }
        )
    
    def get_agent_status(self) -> Dict[str, str]:
        """Get current status of all agents"""
        return {
            name: state.value 
            for name, state in self._active_agents.items()
        }
    
    def get_execution_history(self, limit: int = 10) -> List[Dict]:
        """Get recent execution history"""
        return [
            r.__dict__ for r in self._execution_history[-limit:]
        ]