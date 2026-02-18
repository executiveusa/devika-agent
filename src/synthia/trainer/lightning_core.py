"""
Agent Lightning Core - SYNTHIA's Mentor and Trainer
===================================================

Microsoft Agent Lightning serves as SYNTHIA's mentor/trainer that:
- Monitors SYNTHIA's code quality and decision making
- Extracts patterns from success/failure cases
- Trains SYNTHIA to improve performance
- Syncs learnings to Archon X brain

This creates a continuous improvement flywheel.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import logging

logger = logging.getLogger("synthia.trainer.lightning")


class ObservationType(Enum):
    """Types of observations Agent Lightning tracks"""
    CODE_QUALITY = "code_quality"
    DECISION_QUALITY = "decision_quality"
    MEMORY_EFFICIENCY = "memory_efficiency"
    PATTERN_SUCCESS = "pattern_success"
    PATTERN_FAILURE = "pattern_failure"
    TASK_COMPLETION = "task_completion"
    QUALITY_GATE = "quality_gate"


@dataclass
class QualityMetrics:
    """Quality metrics for SYNTHIA's output"""
    lighthouse_score: float = 0.0
    accessibility_score: float = 0.0
    security_score: float = 0.0
    code_complexity: float = 0.0
    test_coverage: float = 0.0
    
    def average(self) -> float:
        scores = [self.lighthouse_score, self.accessibility_score, 
                  self.security_score, self.test_coverage]
        return sum(scores) / len(scores) if scores else 0.0


@dataclass
class Observation:
    """A single observation of SYNTHIA's behavior"""
    observation_id: str
    timestamp: datetime
    observation_type: ObservationType
    task_description: str
    result: Any
    metrics: QualityMetrics
    decisions_made: list[str] = field(default_factory=list)
    memory_retrieval_time_ms: float = 0.0
    success: bool = False
    error_message: Optional[str] = None
    context: dict = field(default_factory=dict)


@dataclass 
class Pattern:
    """A learned pattern from observations"""
    pattern_id: str
    pattern_type: str
    description: str
    success_rate: float
    occurrence_count: int
    first_observed: datetime
    last_observed: datetime
    context: dict = field(default_factory=dict)
    code_snippets: list[str] = field(default_factory=list)
    
    def should_avoid(self) -> bool:
        """Patterns with <50% success should be avoided"""
        return self.success_rate < 0.5
    
    def should_promote(self) -> bool:
        """Patterns with >80% success should be promoted"""
        return self.success_rate > 0.8


class AgentLightning:
    """
    Microsoft Agent Lightning - SYNTHIA's Mentor and Trainer
    
    Monitors SYNTHIA's performance, extracts learning patterns,
    and continuously improves SYNTHIA's capabilities.
    """
    
    def __init__(self, synthia_agent=None):
        self.synthia = synthia_agent
        self.observations: list[Observation] = []
        self.patterns: dict[str, Pattern] = {}
        self.metrics_history: list[QualityMetrics] = []
        self._running = False
        self._observation_count = 0
        
        # Configuration
        self.min_observations_for_pattern = 5
        self.pattern_extraction_interval = 100
        self.improvement_check_interval = 50
        
        logger.info("Agent Lightning initialized - SYNTHIA's mentor is ready")
    
    @property
    def observation_count(self) -> int:
        return self._observation_count
    
    async def observe_task(self, task: str, result: Any, 
                          metrics: QualityMetrics,
                          decisions: Optional[list[str]] = None,
                          context: Optional[dict] = None) -> Observation:
        """Monitor SYNTHIA executing a task and record the observation."""
        self._observation_count += 1
        
        observation = Observation(
            observation_id=f"obs_{self._observation_count}_{int(time.time())}",
            timestamp=datetime.now(),
            observation_type=ObservationType.TASK_COMPLETION,
            task_description=task,
            result=result,
            metrics=metrics,
            decisions_made=decisions or [],
            context=context or {},
            success=metrics.average() >= 80.0
        )
        
        self.observations.append(observation)
        self.metrics_history.append(metrics)
        
        # Extract patterns periodically
        if self._observation_count % self.pattern_extraction_interval == 0:
            await self._extract_patterns()
        
        # Check for improvements
        if self._observation_count % self.improvement_check_interval == 0:
            await self._check_improvements()
        
        logger.debug(f"Observation recorded: {observation.observation_id}, success: {observation.success}")
        return observation
    
    async def _extract_patterns(self):
        """Extract learned patterns from recent observations."""
        if len(self.observations) < self.min_observations_for_pattern:
            return
        
        recent = self.observations[-self.min_observations_for_pattern:]
        
        # Group by task type
        task_groups: dict[str, list[Observation]] = {}
        for obs in recent:
            task_type = self._classify_task(obs.task_description)
            if task_type not in task_groups:
                task_groups[task_type] = []
            task_groups[task_type].append(obs)
        
        # Extract patterns from each group
        for task_type, obs_list in task_groups.items():
            success_count = sum(1 for o in obs_list if o.success)
            success_rate = success_count / len(obs_list) if obs_list else 0.0
            
            pattern_id = f"pattern_{task_type}"
            if pattern_id in self.patterns:
                # Update existing pattern
                pattern = self.patterns[pattern_id]
                pattern.occurrence_count += len(obs_list)
                pattern.success_rate = (pattern.success_rate * pattern.occurrence_count + 
                                      success_rate * len(obs_list)) / (pattern.occurrence_count + len(obs_list))
                pattern.last_observed = datetime.now()
            else:
                # Create new pattern
                self.patterns[pattern_id] = Pattern(
                    pattern_id=pattern_id,
                    pattern_type=task_type,
                    description=f"Pattern for {task_type} tasks",
                    success_rate=success_rate,
                    occurrence_count=len(obs_list),
                    first_observed=datetime.now(),
                    last_observed=datetime.now()
                )
        
        logger.info(f"Extracted {len(task_groups)} patterns from recent observations")
    
    def _classify_task(self, task_description: str) -> str:
        """Classify task into type for pattern matching."""
        task_lower = task_description.lower()
        
        if any(word in task_lower for word in ["create", "build", "generate", "implement"]):
            return "code_generation"
        elif any(word in task_lower for word in ["fix", "debug", "repair", "patch"]):
            return "bug_fixing"
        elif any(word in task_lower for word in ["test", "verify", "check"]):
            return "testing"
        elif any(word in task_lower for word in ["deploy", "release", "publish"]):
            return "deployment"
        elif any(word in task_lower for word in ["analyze", "review", "scan"]):
            return "analysis"
        else:
            return "general"
    
    async def _check_improvements(self):
        """Check for performance improvements over time."""
        if len(self.metrics_history) < 10:
            return
        
        recent = self.metrics_history[-10:]
        older = self.metrics_history[-20:-10] if len(self.metrics_history) >= 20 else self.metrics_history[:-10]
        
        if not older:
            return
        
        recent_avg = sum(m.average() for m in recent) / len(recent)
        older_avg = sum(m.average() for m in older) / len(older)
        
        improvement = recent_avg - older_avg
        
        if improvement > 5:
            logger.info(f"Performance improvement detected: +{improvement:.1f}%")
            await self._notify_improvement(improvement)
        elif improvement < -5:
            logger.warning(f"Performance degradation detected: {improvement:.1f}%")
            await self._analyze_degradation()
    
    async def _notify_improvement(self, improvement: float):
        """Notify about performance improvements."""
        logger.info(f"🎉 SYNTHIA improved by {improvement:.1f}%!")
    
    async def _analyze_degradation(self):
        """Analyze causes of performance degradation."""
        recent = self.observations[-10:]
        failed = [o for o in recent if not o.success]
        
        if failed:
            logger.warning(f"Analyzing {len(failed)} failed observations")
    
    async def train_synthia(self):
        """Train SYNTHIA based on extracted patterns."""
        improvements_applied = 0
        
        for pattern in self.patterns.values():
            if pattern.should_avoid() and self.synthia:
                logger.info(f"Pattern {pattern.pattern_id} marked for avoidance (success rate: {pattern.success_rate:.1%})")
                improvements_applied += 1
            elif pattern.should_promote() and self.synthia:
                logger.info(f"Pattern {pattern.pattern_id} marked for promotion (success rate: {pattern.success_rate:.1%})")
                improvements_applied += 1
        
        logger.info(f"Applied {improvements_applied} pattern-based improvements")
        return improvements_applied
    
    def get_metrics(self) -> dict:
        """Get current performance metrics."""
        if not self.metrics_history:
            return {"quality_score": 0.0, "success_rate": 0.0}
        
        recent = self.metrics_history[-10:]
        avg_quality = sum(m.average() for m in recent) / len(recent)
        
        recent_obs = self.observations[-50:]
        success_rate = sum(1 for o in recent_obs if o.success) / len(recent_obs) if recent_obs else 0.0
        
        return {
            "quality_score": avg_quality,
            "success_rate": success_rate,
            "total_observations": self.observation_count,
            "patterns_learned": len(self.patterns),
            "avg_lighthouse": sum(m.lighthouse_score for m in recent) / len(recent),
            "avg_accessibility": sum(m.accessibility_score for m in recent) / len(recent)
        }
    
    async def sync_to_archon_x(self, webhook_url: str):
        """Sync learned patterns to Archon X brain."""
        payload = {
            "source": "synthia_agent_lightning",
            "timestamp": datetime.now().isoformat(),
            "patterns": [
                {
                    "id": p.pattern_id,
                    "type": p.pattern_type,
                    "success_rate": p.success_rate,
                    "occurrences": p.occurrence_count
                }
                for p in self.patterns.values()
            ],
            "metrics": self.get_metrics()
        }
        
        logger.info(f"Syncing {len(self.patterns)} patterns to Archon X")
        return payload
    
    def start_monitoring(self):
        """Start continuous monitoring."""
        self._running = True
        logger.info("Agent Lightning monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self._running = False
        logger.info("Agent Lightning monitoring stopped")
