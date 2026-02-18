"""
SYNTHIA Design System
=====================
UI/UX Pro Max integration with 50+ styles, 97 color palettes, 57 font pairings.
Awwwards-level design system for production-grade output.
"""

from .design_system import DesignSystem, DesignTokens
from .awwwards import AwwwardsInspiration, DesignPattern
from .theme_generator import ThemeGenerator, ThemeConfig
from .steve_krug import SteveKrugPrinciples, BreakpointSystem

__all__ = [
    "DesignSystem",
    "DesignTokens",
    "AwwwardsInspiration",
    "DesignPattern",
    "ThemeGenerator",
    "ThemeConfig",
    "SteveKrugPrinciples",
    "BreakpointSystem",
]