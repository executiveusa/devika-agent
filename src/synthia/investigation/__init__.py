"""
SYNTHIA Investigation Engine
============================
Repository scanning, niche detection, architecture analysis, and strategic planning.
"""

from .repo_scanner import RepositoryScanner, ScanResult
from .niche_detector import NicheDetector, NicheProfile
from .architecture_analyzer import ArchitectureAnalyzer, ArchitectureReport
from .strategic_planner import StrategicPlanner, StrategicPlan

__all__ = [
    "RepositoryScanner",
    "ScanResult",
    "NicheDetector",
    "NicheProfile",
    "ArchitectureAnalyzer",
    "ArchitectureReport",
    "StrategicPlanner",
    "StrategicPlan",
]