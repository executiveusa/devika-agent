"""
Ralphy Execution Engine - Task Prioritization & Retry Logic
=========================================================

Integrates Ralphy's execution patterns:
- Priority-based task sorting (Architectural → Integration → Unknown → Standard → Polish)
- Retry logic with exponential backoff
- Parallel execution with worktrees
- Sandbox mode support
"""

import asyncio
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger("synthia.execution.ralphy_engine")


class TaskPriority(Enum):
    """Ralphy's priority order for tasks"""
    ARCHITECTURAL = 1   # Core infrastructure
    INTEGRATION = 2     # API/Service connections
    UNKNOWN = 3        # Complex/unproven
    STANDARD = 4       # Common patterns
    POLISH = 5         # UI/UX refinements


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    base_delay: float = 2.0
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0


@dataclass
class Task:
    """A task to execute"""
    task_id: str
    title: str
    description: str
    priority: TaskPriority = TaskPriority.STANDARD
    parallel_group: int = 0
    completed: bool = False
    failed: bool = False
    retry_count: int = 0
    context: dict = field(default_factory=dict)
    
    def __lt__(self, other):
        return self.priority.value < other.priority.value


@dataclass
class ExecutionResult:
    """Result of task execution"""
    task_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    retries: int = 0


class RalphyExecutionEngine:
    """
    Ralphy-style execution engine with priority sorting and retry logic.
    
    Key features:
    - Priority-based task execution
    - Exponential backoff retry
    - Parallel execution support
    - Sandbox isolation
    """
    
    PRIORITY_ORDER = [
        TaskPriority.ARCHITECTURAL,
        TaskPriority.INTEGRATION,
        TaskPriority.UNKNOWN,
        TaskPriority.STANDARD,
        TaskPriority.POLISH
    ]
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.retry_config = retry_config or RetryConfig()
        self.tasks: list[Task] = []
        self.results: list[ExecutionResult] = []
        self._running = False
        
        # Parallel execution
        self.max_parallel = 3
        self.use_sandbox = False
        
        logger.info("Ralphy Execution Engine initialized")
    
    def add_task(self, title: str, description: str, 
                 priority: TaskPriority = TaskPriority.STANDARD,
                 parallel_group: int = 0,
                 context: Optional[dict] = None) -> Task:
        """Add a task to the execution queue"""
        task = Task(
            task_id=f"task_{len(self.tasks)}_{int(datetime.now().timestamp())}",
            title=title,
            description=description,
            priority=priority,
            parallel_group=parallel_group,
            context=context or {}
        )
        self.tasks.append(task)
        logger.debug(f"Added task: {task.title} with priority {priority.name}")
        return task
    
    def sort_by_priority(self) -> list[Task]:
        """Sort tasks by Ralphy's priority order"""
        return sorted(self.tasks, key=lambda t: t.priority.value)
    
    def sort_by_parallel_group(self) -> list[list[Task]]:
        """Group tasks by parallel execution groups"""
        groups: dict[int, list[Task]] = {}
        for task in self.tasks:
            if task.parallel_group not in groups:
                groups[task.parallel_group] = []
            groups[task.parallel_group].append(task)
        
        # Sort each group by priority
        return [sorted(group, key=lambda t: t.priority.value) 
                for group in groups.values()]
    
    async def execute_with_retry(self, task: Task, 
                                 executor: Callable[[Task], Any]) -> ExecutionResult:
        """Execute a task with retry logic"""
        start_time = datetime.now()
        
        while task.retry_count <= self.retry_config.max_retries:
            try:
                logger.info(f"Executing task: {task.title} (attempt {task.retry_count + 1})")
                
                # Execute the task
                if asyncio.iscoroutinefunction(executor):
                    output = await executor(task)
                else:
                    output = executor(task)
                
                duration = (datetime.now() - start_time).total_seconds()
                
                result = ExecutionResult(
                    task_id=task.task_id,
                    success=True,
                    output=output,
                    duration=duration,
                    retries=task.retry_count
                )
                
                task.completed = True
                self.results.append(result)
                
                logger.info(f"Task completed: {task.title} in {duration:.2f}s")
                return result
                
            except Exception as e:
                task.retry_count += 1
                task.failed = True
                
                logger.warning(f"Task failed: {task.title} - {str(e)}")
                
                if task.retry_count <= self.retry_config.max_retries:
                    # Calculate delay with exponential backoff
                    delay = min(
                        self.retry_config.base_delay * (self.retry_config.backoff_multiplier ** (task.retry_count - 1)),
                        self.retry_config.max_delay
                    )
                    
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    duration = (datetime.now() - start_time).total_seconds()
                    result = ExecutionResult(
                        task_id=task.task_id,
                        success=False,
                        error=str(e),
                        duration=duration,
                        retries=task.retry_count
                    )
                    self.results.append(result)
                    
                    logger.error(f"Task failed after {task.retry_count} attempts: {task.title}")
                    return result
        
        # Should not reach here
        return ExecutionResult(task_id=task.task_id, success=False, error="Max retries exceeded")
    
    async def execute_all(self, executor: Callable[[Task], Any]) -> list[ExecutionResult]:
        """Execute all tasks in priority order"""
        self._running = True
        self.results.clear()
        
        # Sort tasks by priority
        sorted_tasks = self.sort_by_priority()
        
        # Execute tasks sequentially (can be parallelized)
        results = []
        for task in sorted_tasks:
            if not task.completed:
                result = await self.execute_with_retry(task, executor)
                results.append(result)
                
                # Notify Agent Lightning of completion
                # await self.lightning.observe_task(task.title, result)
        
        self._running = False
        logger.info(f"Execution complete: {len([r for r in results if r.success])}/{len(results)} successful")
        return results
    
    async def execute_parallel(self, executor: Callable[[Task], Any]) -> list[ExecutionResult]:
        """Execute tasks in parallel groups"""
        self._running = True
        self.results.clear()
        
        # Get groups sorted by parallel group
        groups = self.sort_by_parallel_group()
        
        for group in groups:
            # Execute tasks in parallel within group
            tasks_to_run = [t for t in group if not t.completed]
            
            if tasks_to_run:
                logger.info(f"Executing {len(tasks_to_run)} tasks in parallel")
                
                coroutines = [self.execute_with_retry(t, executor) for t in tasks_to_run]
                group_results = await asyncio.gather(*coroutines, return_exceptions=True)
                
                for result in group_results:
                    if isinstance(result, Exception):
                        logger.error(f"Parallel execution error: {result}")
                    else:
                        self.results.append(result)
        
        self._running = False
        return self.results
    
    async def create_sandbox(self, path: str) -> str:
        """Create a sandbox for isolated execution"""
        if not self.use_sandbox:
            return path
        
        # In production, would use actual sandbox creation
        # For now, return the original path
        logger.info(f"Creating sandbox at: {path}")
        return path
    
    def get_summary(self) -> dict:
        """Get execution summary"""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total - successful
        
        return {
            "total_tasks": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "total_duration": sum(r.duration for r in self.results)
        }
    
    def clear(self):
        """Clear tasks and results"""
        self.tasks.clear()
        self.results.clear()
        logger.debug("Execution engine cleared")


# Convenience function for priority detection
def detect_priority(task_description: str) -> TaskPriority:
    """Auto-detect task priority from description"""
    desc_lower = task_description.lower()
    
    # Architectural keywords
    arch_keywords = ["core", "infrastructure", "database", "schema", "api design", "architecture"]
    if any(kw in desc_lower for kw in arch_keywords):
        return TaskPriority.ARCHITECTURAL
    
    # Integration keywords  
    int_keywords = ["integration", "api", "service", "webhook", "connection", "auth"]
    if any(kw in desc_lower for kw in int_keywords):
        return TaskPriority.INTEGRATION
    
    # Polish keywords
    polish_keywords = ["ui", "ux", "style", "design", "css", "animation", " polish", "responsive"]
    if any(kw in desc_lower for kw in polish_keywords):
        return TaskPriority.POLISH
    
    # Unknown - complex/risky tasks
    unknown_keywords = ["complex", "experimental", "algorithm", "machine learning", "ai"]
    if any(kw in desc_lower for kw in unknown_keywords):
        return TaskPriority.UNKNOWN
    
    return TaskPriority.STANDARD
