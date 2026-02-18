"""
Improvement Engine - SYNTHIA's Learning System
==============================================

Analyzes observations, extracts patterns, and generates
improvements to SYNTHIA's performance.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import logging

from .lightning_core import AgentLightning, Observation, Pattern, QualityMetrics

logger = logging.getLogger("synthia.trainer.improver")


@dataclass
class Improvement:
    """An improvement to apply to SYNTHIA"""
    improvement_id: str
    improvement_type: str
    description: str
    priority: int
    expected_impact: float
    implementation_notes: str
    applied: bool = False


@dataclass
class ImprovementConfig:
    """Configuration for improvement engine"""
    min_success_rate_for_promotion: float = 0.8
    max_success_rate_for_avoidance: float = 0.5
    min_observations: int = 10
    improvement_priority_threshold: float = 0.7


class ImprovementEngine:
    """
    Analyzes patterns and generates improvements for SYNTHIA.
    
    Creates a continuous learning loop:
    1. Analyze observations
    2. Extract success/failure patterns
    3. Generate improvements
    4. Apply improvements
    5. Sync to Archon X
    """
    
    def __init__(self, lightning: AgentLightning, config: Optional[ImprovementConfig] = None):
        self.lightning = lightning
        self.config = config or ImprovementConfig()
        self.improvements: list[Improvement] = []
        self._improvement_count = 0
    
    async def analyze_and_improve(self) -> list[Improvement]:
        """Main improvement cycle - analyze observations and generate improvements."""
        improvements = []
        
        # Get recent observations
        recent_obs = self.lightning.observations[-self.config.min_observations:]
        if len(recent_obs) < self.config.min_observations:
            logger.debug(f"Not enough observations: {len(recent_obs)}/{self.config.min_observations}")
            return improvements
        
        # Analyze patterns
        success_patterns = self._find_success_patterns(recent_obs)
        failure_patterns = self._find_failure_patterns(recent_obs)
        
        # Generate improvements from patterns
        for pattern in success_patterns:
            improvement = self._create_promotion_improvement(pattern)
            if improvement:
                improvements.append(improvement)
        
        for pattern in failure_patterns:
            improvement = self._create_avoidance_improvement(pattern)
            if improvement:
                improvements.append(improvement)
        
        # Analyze decision quality
        decision_improvements = await self._analyze_decisions(recent_obs)
        improvements.extend(decision_improvements)
        
        # Apply improvements
        applied = await self._apply_improvements(improvements)
        
        logger.info(f"Applied {applied} improvements from {len(improvements)} generated")
        return improvements
    
    def _find_success_patterns(self, observations: list[Observation]) -> list[Pattern]:
        """Find patterns with high success rates"""
        success_rate_by_type: dict[str, tuple[int, int]] = {}
        
        for obs in observations:
            task_type = self._classify_task(obs.task_description)
            if task_type not in success_rate_by_type:
                success_rate_by_type[task_type] = (0, 0)
            
            total = success_rate_by_type[task_type][1] + 1
            success = success_rate_by_type[task_type][0] + (1 if obs.success else 0)
            success_rate_by_type[task_type] = (success, total)
        
        patterns = []
        for task_type, (success, total) in success_rate_by_type.items():
            rate = success / total if total > 0 else 0
            if rate >= self.config.min_success_rate_for_promotion:
                patterns.append(Pattern(
                    pattern_id=f"success_{task_type}",
                    pattern_type=task_type,
                    description=f"Successful {task_type} pattern",
                    success_rate=rate,
                    occurrence_count=total,
                    first_observed=datetime.now(),
                    last_observed=datetime.now()
                ))
        
        return patterns
    
    def _find_failure_patterns(self, observations: list[Observation]) -> list[Pattern]:
        """Find patterns with low success rates"""
        return [p for p in self._find_success_patterns(observations)
                if p.success_rate <= self.config.max_success_rate_for_avoidance]
    
    def _classify_task(self, task_description: str) -> str:
        """Classify task type"""
        task_lower = task_description.lower()
        
        if any(w in task_lower for w in ["create", "build", "generate"]):
            return "code_generation"
        elif any(w in task_lower for w in ["fix", "debug", "repair"]):
            return "bug_fixing"
        elif any(w in task_lower for w in ["test", "verify"]):
            return "testing"
        elif any(w in task_lower for w in ["deploy", "release"]):
            return "deployment"
        elif any(w in task_lower for w in ["analyze", "review"]):
            return "analysis"
        return "general"
    
    def _create_promotion_improvement(self, pattern: Pattern) -> Optional[Improvement]:
        """Create improvement to promote a successful pattern"""
        self._improvement_count += 1
        
        return Improvement(
            improvement_id=f"imp_{self._improvement_count}",
            improvement_type="promote_pattern",
            description=f"Promote {pattern.pattern_type} - {pattern.success_rate:.1%} success rate",
            priority=int(pattern.success_rate * 10),
            expected_impact=pattern.success_rate,
            implementation_notes=f"Increase usage of {pattern.pattern_type} pattern in similar tasks"
        )
    
    def _create_avoidance_improvement(self, pattern: Pattern) -> Optional[Improvement]:
        """Create improvement to avoid a failing pattern"""
        self._improvement_count += 1
        
        return Improvement(
            improvement_id=f"imp_{self._improvement_count}",
            improvement_type="avoid_pattern",
            description=f"Avoid {pattern.pattern_type} - only {pattern.success_rate:.1%} success rate",
            priority=int((1 - pattern.success_rate) * 10),
            expected_impact=1 - pattern.success_rate,
            implementation_notes=f"Reduce usage of {pattern.pattern_type}, try alternative approaches"
        )
    
    async def _analyze_decisions(self, observations: list[Observation]) -> list[Improvement]:
        """Analyze decision quality and generate improvements"""
        improvements = []
        
        # Check for common decision issues
        decision_issues: dict[str, int] = {}
        
        for obs in observations:
            if not obs.success and obs.decisions_made:
                for decision in obs.decisions_made:
                    decision_issues[decision] = decision_issues.get(decision, 0) + 1
        
        # Generate improvements for problematic decisions
        for decision, count in decision_issues.items():
            if count >= 3:  # Repeated issue
                self._improvement_count += 1
                improvements.append(Improvement(
                    improvement_id=f"imp_{self._improvement_count}",
                    improvement_type="improve_decision",
                    description=f"Improve decision: {decision} (occurred {count} times in failures)",
                    priority=count,
                    expected_impact=0.3,
                    implementation_notes=f"Analyze and improve decision-making for: {decision}"
                ))
        
        return improvements
    
    async def _apply_improvements(self, improvements: list[Improvement]) -> int:
        """Apply improvements to SYNTHIA"""
        applied = 0
        
        for imp in improvements:
            if imp.priority >= 5:  # Only apply high priority improvements
                imp.applied = True
                applied += 1
                self.improvements.append(imp)
                
                logger.info(f"Applied improvement: {imp.improvement_id} - {imp.description}")
        
        return applied
    
    async def sync_improvements_to_archon_x(self, webhook_url: str) -> dict:
        """Sync improvements to Archon X brain"""
        payload = {
            "source": "synthia_improvement_engine",
            "timestamp": datetime.now().isoformat(),
            "improvements": [
                {
                    "id": i.improvement_id,
                    "type": i.improvement_type,
                    "description": i.description,
                    "priority": i.priority,
                    "applied": i.applied
                }
                for i in self.improvements[-20:]
            ],
            "total_applied": sum(1 for i in self.improvements if i.applied)
        }
        
        logger.info(f"Synced {len(payload['improvements'])} improvements to Archon X")
        return payload
