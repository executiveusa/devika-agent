"""
SYNTHIA Unified Orchestrator - Ralphy + Lightning Integration
=========================================================

The core orchestrator that combines:
1. Ralphy's execution patterns (priority-based task execution)
2. Agent Lightning's mentor/observer system
3. Quality Gates for production-ready output

This creates the "flywheel" effect:
SYNTHIA executes → Quality Gates validate → Agent Lightning observes/trains → Memory syncs → Improved execution
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import logging

from src.synthia.execution import (
    RalphyExecutionEngine, 
    TaskPriority, 
    Task,
    RetryConfig
)
from src.synthia.trainer.lightning_core import AgentLightning
from src.synthia.trainer.hooks import QualityGateHook, QualityThresholds
from src.synthia.memory import MemoryLayer

logger = logging.getLogger("synthia.orchestrator")


class ExecutionMode(Enum):
    """Execution modes for SYNTHIA"""
    STANDARD = "standard"        # Sequential with Ralphy priority
    PARALLEL = "parallel"        # Parallel task execution
    SANDBOX = "sandbox"          # Isolated execution
    AUTO = "auto"               # Auto-detect best mode


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator"""
    execution_mode: ExecutionMode = ExecutionMode.AUTO
    enable_lightning: bool = True
    enable_quality_gates: bool = True
    quality_thresholds: Optional[QualityThresholds] = None
    retry_config: Optional[RetryConfig] = None
    max_parallel_tasks: int = 3
    lightning_api_key: Optional[str] = None


@dataclass
class ExecutionContext:
    """Context for task execution"""
    project_name: str
    user_request: str
    investigation_data: dict = field(default_factory=dict)
    design_system: dict = field(default_factory=dict)
    niche: str = "general"
    additional_context: dict = field(default_factory=dict)


@dataclass
class ExecutionReport:
    """Final execution report"""
    success: bool
    tasks_completed: int
    tasks_failed: int
    quality_results: list = field(default_factory=list)
    lightning_insights: list = field(default_factory=list)
    execution_time: float = 0.0
    errors: list = field(default_factory=list)


class SynthiaOrchestrator:
    """
    Unified Orchestrator combining Ralphy + Agent Lightning + Quality Gates.
    
    This is the heart of SYNTHIA's autonomous execution system:
    
    ┌─────────────────────────────────────────────────────────────┐
    │                    SYNTHIA ORCHESTRATOR                     │
    │                                                              │
    │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
    │   │   RALPHY    │───▶│   QUALITY   │───▶│   LIGHTNING │    │
    │   │  EXECUTION  │    │    GATES    │    │   MENTOR    │    │
    │   └─────────────┘    └─────────────┘    └─────────────┘    │
    │         │                  │                  │          │
    │         ▼                  ▼                  ▼          │
    │   ┌─────────────────────────────────────────────────┐    │
    │   │              MEMORY LAYER                        │    │
    │   │   (Project → Team → Global → Archon X)         │    │
    │   └─────────────────────────────────────────────────┘    │
    │                          │                                │
    │                          ▼                                │
    │   ┌─────────────────────────────────────────────────┐    │
    │   │            FLYWHEEL EFFECT                      │    │
    │   │   Continuous improvement on every execution    │    │
    │   └─────────────────────────────────────────────────┘    │
    └─────────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        
        # Initialize components
        self.ralphy = RalphyExecutionEngine(
            retry_config=self.config.retry_config or RetryConfig()
        )
        self.ralphy.max_parallel = self.config.max_parallel_tasks
        
        self.quality_gates = QualityGateHook(
            thresholds=self.config.quality_thresholds or QualityThresholds()
        )
        
        self.lightning: Optional[AgentLightning] = None
        if self.config.enable_lightning:
            self.lightning = AgentLightning(
                api_key=self.config.lightning_api_key
            )
        
        self.memory: Optional[MemoryLayer] = None
        
        # Execution state
        self._running = False
        self._execution_start: Optional[datetime] = None
        
        logger.info("SYNTHIA Orchestrator initialized")
        logger.info(f"  Mode: {self.config.execution_mode.value}")
        logger.info(f"  Lightning: {'Enabled' if self.lightning else 'Disabled'}")
        logger.info(f"  Quality Gates: {'Enabled' if self.config.enable_quality_gates else 'Disabled'}")
    
    async def initialize(self, memory: MemoryLayer):
        """Initialize orchestrator with memory layer"""
        self.memory = memory
        
        if self.lightning:
            await self.lightning.initialize()
        
        logger.info("Orchestrator ready for execution")
    
    async def execute(self, context: ExecutionContext, 
                     executor: Callable[[Task], Any]) -> ExecutionReport:
        """
        Execute tasks with Ralphy priority, quality gates, and Lightning observation.
        
        This is the main entry point for SYNTHIA's autonomous execution.
        """
        self._running = True
        self._execution_start = datetime.now()
        
        logger.info(f"Starting execution for: {context.project_name}")
        logger.info(f"User request: {context.user_request}")
        
        # Store context in memory
        await self._store_context(context)
        
        # Notify Lightning of execution start
        if self.lightning:
            await self.lightning.observe_execution_start(context)
        
        # Build tasks from context
        tasks = self._build_tasks(context)
        
        # Add tasks to Ralphy
        for task in tasks:
            self.ralphy.add_task(
                title=task.title,
                description=task.description,
                priority=task.priority,
                parallel_group=task.parallel_group,
                context=task.context
            )
        
        # Execute based on mode
        if self.config.execution_mode == ExecutionMode.PARALLEL:
            results = await self.ralphy.execute_parallel(executor)
        else:
            results = await self.ralphy.execute_all(executor)
        
        # Run quality gates
        quality_results = []
        if self.config.enable_quality_gates:
            for task, result in zip(tasks, results):
                if result.success:
                    quality_result = await self.quality_gates.enforce(
                        code=str(result.output or ""),
                        context=task.context
                    )
                    quality_results.append({
                        "task_id": task.task_id,
                        "result": quality_result
                    })
        
        # Notify Lightning of execution complete
        lightning_insights = []
        if self.lightning:
            insights = await self.lightning.observe_execution_complete(
                context=context,
                results=results,
                quality_results=quality_results
            )
            lightning_insights = insights
        
        # Calculate execution time
        execution_time = (datetime.now() - self._execution_start).total_seconds()
        
        # Build final report
        report = ExecutionReport(
            success=all(r.success for r in results),
            tasks_completed=len([r for r in results if r.success]),
            tasks_failed=len([r for r in results if not r.success]),
            quality_results=quality_results,
            lightning_insights=lightning_insights,
            execution_time=execution_time,
            errors=[r.error for r in results if r.error]
        )
        
        # Store results in memory
        await self._store_results(context, report)
        
        self._running = False
        
        logger.info(f"Execution complete in {execution_time:.2f}s")
        logger.info(f"  Success: {report.tasks_completed}/{report.tasks_completed + report.tasks_failed}")
        
        return report
    
    def _build_tasks(self, context: ExecutionContext) -> list[Task]:
        """Build task list from execution context"""
        tasks = []
        
        # Add investigation phase
        if context.investigation_data:
            tasks.append(Task(
                task_id="task_investigation",
                title="Investigate repository",
                description="Scan and analyze repository structure",
                priority=TaskPriority.ARCHITECTURAL,
                parallel_group=0,
                context=context.investigation_data
            ))
        
        # Add design phase
        if context.design_system:
            tasks.append(Task(
                task_id="task_design",
                title="Apply design system",
                description="Integrate design tokens and components",
                priority=TaskPriority.POLISH,
                parallel_group=0,
                context=context.design_system
            ))
        
        # Add code generation task
        tasks.append(Task(
            task_id="task_code_generation",
            title="Generate code",
            description=context.user_request,
            priority=TaskPriority.STANDARD,
            parallel_group=1,
            context={
                "user_request": context.user_request,
                "niche": context.niche
            }
        ))
        
        return tasks
    
    async def _store_context(self, context: ExecutionContext):
        """Store execution context in memory"""
        if not self.memory:
            return
        
        await self.memory.store(
            key=f"context:{context.project_name}:{datetime.now().isoformat()}",
            value={
                "user_request": context.user_request,
                "niche": context.niche,
                "timestamp": datetime.now().isoformat()
            },
            layer="project"
        )
    
    async def _store_results(self, context: ExecutionContext, report: ExecutionReport):
        """Store execution results in memory"""
        if not self.memory:
            return
        
        # Store summary
        await self.memory.store(
            key=f"results:{context.project_name}:{datetime.now().isoformat()}",
            value={
                "success": report.success,
                "tasks_completed": report.tasks_completed,
                "tasks_failed": report.tasks_failed,
                "execution_time": report.execution_time,
                "quality_passed": len([r for r in report.quality_results if r.get('result', {}).passed])
            },
            layer="project"
        )
        
        # Sync to team/global for Lightning insights
        if self.lightning and report.lightning_insights:
            await self.memory.store(
                key=f"lightning_insights:{datetime.now().isoformat()}",
                value=report.lightning_insights,
                layer="team"
            )
    
    async def close(self):
        """Cleanup resources"""
        if self.lightning:
            await self.lightning.close()
        
        logger.info("Orchestrator closed")


# Convenience function for quick execution
async def quick_execute(
    project_name: str,
    user_request: str,
    memory: Optional[MemoryLayer] = None,
    lightning_api_key: Optional[str] = None
) -> ExecutionReport:
    """Quick execution with default configuration"""
    
    config = OrchestratorConfig(
        execution_mode=ExecutionMode.AUTO,
        enable_lightning=True,
        enable_quality_gates=True,
        lightning_api_key=lightning_api_key
    )
    
    context = ExecutionContext(
        project_name=project_name,
        user_request=user_request
    )
    
    orchestrator = SynthiaOrchestrator(config)
    
    if memory:
        await orchestrator.initialize(memory)
    
    # Dummy executor for testing
    async def test_executor(task: Task):
        await asyncio.sleep(0.1)
        return {"status": "completed", "task": task.title}
    
    report = await orchestrator.execute(context, test_executor)
    
    await orchestrator.close()
    
    return report
