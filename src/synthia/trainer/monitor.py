"""
Performance Monitor - SYNTHIA's Observation System
===============================================

Monitors SYNTHIA's code quality, decision making, and memory efficiency
in real-time during task execution.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional
import logging

from .lightning_core import QualityMetrics, ObservationType

logger = logging.getLogger("synthia.trainer.monitor")


@dataclass
class MonitorConfig:
    """Configuration for performance monitoring"""
    sample_interval: float = 1.0
    memory_check_interval: float = 0.1
    quality_threshold: float = 80.0
    enable_real_time: bool = True


class PerformanceMonitor:
    """
    Monitors SYNTHIA's performance in real-time.
    
    Tracks:
    - Code quality metrics
    - Memory retrieval efficiency  
    - Decision quality
    - Task completion rates
    """
    
    def __init__(self, config: Optional[MonitorConfig] = None):
        self.config = config or MonitorConfig()
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Metrics tracking
        self.task_start_time: float = 0.0
        self.current_task: Optional[str] = None
        self.memory_queries: list[dict] = []
        self.decisions: list[str] = []
        self.quality_scores: list[float] = []
        
        # Callbacks
        self.on_task_start: Optional[Callable] = None
        self.on_task_complete: Optional[Callable] = None
        self.on_quality_check: Optional[Callable] = None
    
    async def start_monitoring(self):
        """Start the performance monitoring loop"""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop the performance monitoring loop"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                if self.current_task and self.config.enable_real_time:
                    # Record memory query time
                    query_time = time.time()
                    await asyncio.sleep(self.config.memory_check_interval)
                    retrieval_time = (time.time() - query_time) * 1000  # ms
                    
                    self.memory_queries.append({
                        "timestamp": datetime.now(),
                        "retrieval_time_ms": retrieval_time,
                        "task": self.current_task
                    })
                
                await asyncio.sleep(self.config.sample_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
    
    def start_task(self, task_name: str):
        """Mark the start of a task"""
        self.task_start_time = time.time()
        self.current_task = task_name
        self.memory_queries.clear()
        self.decisions.clear()
        self.quality_scores.clear()
        
        if self.on_task_start:
            self.on_task_start(task_name)
        
        logger.debug(f"Task started: {task_name}")
    
    def record_decision(self, decision: str):
        """Record a decision made during task execution"""
        self.decisions.append({
            "decision": decision,
            "timestamp": datetime.now(),
            "task": self.current_task
        })
    
    def record_quality_score(self, score: float):
        """Record a quality score"""
        self.quality_scores.append(score)
        
        if self.on_quality_check and score < self.config.quality_threshold:
            self.on_quality_check(score)
    
    def end_task(self, result: Any) -> dict:
        """Mark the end of a task and return metrics"""
        duration = time.time() - self.task_start_time
        
        metrics = QualityMetrics()
        
        if self.quality_scores:
            metrics.lighthouse_score = sum(self.quality_scores) / len(self.quality_scores)
        
        if self.memory_queries:
            avg_retrieval = sum(q["retrieval_time_ms"] for q in self.memory_queries) / len(self.memory_queries)
            metrics.code_complexity = avg_retrieval
        
        summary = {
            "task": self.current_task,
            "duration_seconds": duration,
            "metrics": metrics,
            "decisions": self.decisions,
            "memory_queries": len(self.memory_queries),
            "quality_scores": self.quality_scores,
            "success": metrics.average() >= self.config.quality_threshold
        }
        
        if self.on_task_complete:
            self.on_task_complete(summary)
        
        logger.debug(f"Task completed: {self.current_task}, success: {summary['success']}")
        
        self.current_task = None
        return summary
    
    def get_current_stats(self) -> dict:
        """Get current monitoring statistics"""
        return {
            "running": self._running,
            "current_task": self.current_task,
            "task_duration": time.time() - self.task_start_time if self.task_start_time else 0,
            "memory_queries_count": len(self.memory_queries),
            "decisions_count": len(self.decisions),
            "avg_quality": sum(self.quality_scores) / len(self.quality_scores) if self.quality_scores else 0
        }
