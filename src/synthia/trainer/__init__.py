"""
SYNTHIA Trainer Module - Agent Lightning Integration
===================================================

Microsoft Agent Lightning serves as SYNTHIA's mentor and trainer,
monitoring performance and continuously improving code quality.
"""

from .lightning_core import AgentLightning
from .monitor import PerformanceMonitor
from .improver import ImprovementEngine
from .hooks import QualityGateHook

__all__ = [
    "AgentLightning",
    "PerformanceMonitor", 
    "ImprovementEngine",
    "QualityGateHook"
]
