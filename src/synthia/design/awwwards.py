"""
SYNTHIA Awwwards Inspiration Database
=====================================
Scrapes and indexes Awwwards-level design patterns for inspiration.
Provides context-aware design recommendations.
"""

import os
import re
import json
from typing import Optional, Dict, List, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class DesignPattern:
    """A design pattern extracted from Awwwards sites"""
    name: str
    category: str  # layout, animation, navigation, hero, etc.
    description: str
    tags: List[str]
    css_snippet: Optional[str]
    use_cases: List[str]
    complexity: str  # simple, moderate, complex
    mobile_friendly: bool
    accessibility_notes: str
    examples: List[str]  # URLs to example sites


@dataclass
class TrendData:
    """Current design trend data"""
    trend_name: str
    popularity_score: float  # 0-100
    growth_rate: str  # rising, stable, declining
    first_seen: str
    niche_affinity: List[str]  # Niches where this trend is popular
    description: str
    examples: List[str]


@dataclass
class SiteAnalysis:
    """Analysis of an Awwwards-winning site"""
    url: str
    name: str
    award_type: str  # sotd, honorable, developer award, etc.
    score: float
    design_patterns: List[str]
    color_palette: List[str]
    typography: Dict[str, str]
    animation_style: str
    layout_type: str
    niche: str
    mobile_score: float
    accessibility_score: float
    performance_score: float
    analyzed_at: datetime


class AwwwardsInspiration:
    """
    Awwwards inspiration database for design patterns and trends.
    
    Features:
    - Design pattern extraction
    - Trend tracking
    - Niche-specific recommendations
    - Mobile-first patterns
    - Accessibility-aware designs
    
    Usage:
        awwwards = AwwwardsInspiration()
        patterns = awwwards.get_patterns_for_niche("fintech")
        trends = awwwards.get_current_trends()
    """
    
    # Pre-defined design patterns (would be scraped from Awwwards in production)
    DESIGN_PATTERNS = {
        # Hero Patterns
        "split_hero": DesignPattern(
            name="Split Hero",
            category="hero",
            description="Two-column hero with text on one side and visual on the other",
            tags=["hero", "split", "balanced", "professional"],
            css_snippet="""
.hero-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
  gap: var(--spacing-8);
}
@media (max-width: 768px) {
  .hero-split {
    grid-template-columns: 1fr;
  }
}
""",
            use_cases=["SaaS landing", "Product showcase", "Agency sites"],
            complexity="simple",
            mobile_friendly=True,
            accessibility_notes="Ensure proper heading hierarchy and sufficient color contrast",
            examples=["linear.app", "vercel.com"]
        ),
        
        "immersive_hero": DesignPattern(
            name="Immersive Hero",
            category="hero",
            description="Full-screen hero with animated background and centered content",
            tags=["hero", "immersive", "animated", "bold"],
            css_snippet="""
.hero-immersive {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.hero-background {
  position: absolute;
  inset: 0;
  z-index: -1;
}
""",
            use_cases=["Creative agencies", "Gaming", "Entertainment"],
            complexity="moderate",
            mobile_friendly=True,
            accessibility_notes="Provide reduced-motion alternative for animations",
            examples=["stripe.com", "apple.com"]
        ),
        
        "gradient_mesh_hero": DesignPattern(
            name="Gradient Mesh Hero",
            category="hero",
            description="Hero with animated gradient mesh background",
            tags=["hero", "gradient", "mesh", "animated", "modern"],
            css_snippet="""
.gradient-mesh {
  background: 
    radial-gradient(at 40% 20%, var(--color-primary) 0px, transparent 50%),
    radial-gradient(at 80% 0%, var(--color-secondary) 0px, transparent 50%),
    radial-gradient(at 0% 50%, var(--color-accent) 0px, transparent 50%);
  animation: mesh-move 20s ease-in-out infinite;
}
@keyframes mesh-move {
  0%, 100% { background-position: 0% 0%; }
  50% { background-position: 100% 100%; }
}
""",
            use_cases=["SaaS", "Startups", "Tech products"],
            complexity="moderate",
            mobile_friendly=True,
            accessibility_notes="Ensure text remains readable over gradient",
            examples=["linear.app", "notion.so"]
        ),
        
        # Navigation Patterns
        "floating_nav": DesignPattern(
            name="Floating Navigation",
            category="navigation",
            description="Fixed navigation that floats above content with blur backdrop",
            tags=["navigation", "floating", "blur", "modern"],
            css_snippet="""
.nav-floating {
  position: fixed;
  top: var(--spacing-4);
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-radius: var(--radius-lg);
  padding: var(--spacing-3) var(--spacing-6);
  z-index: 100;
}
""",
            use_cases=["SaaS", "Portfolios", "Blogs"],
            complexity="simple",
            mobile_friendly=True,
            accessibility_notes="Ensure sufficient contrast with backdrop blur",
            examples=["vercel.com", "tailwindcss.com"]
        ),
        
        "sidebar_nav": DesignPattern(
            name="Sidebar Navigation",
            category="navigation",
            description="Persistent sidebar navigation for dashboard-style layouts",
            tags=["navigation", "sidebar", "dashboard", "persistent"],
            css_snippet="""
.sidebar-nav {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  width: 240px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  padding: var(--spacing-4);
}
@media (max-width: 1024px) {
  .sidebar-nav {
    transform: translateX(-100%);
    transition: transform var(--duration-normal);
  }
  .sidebar-nav.open {
    transform: translateX(0);
  }
}
""",
            use_cases=["Dashboards", "Documentation", "Admin panels"],
            complexity="moderate",
            mobile_friendly=True,
            accessibility_notes="Include skip link and proper focus management",
            examples=["linear.app", "notion.so"]
        ),
        
        # Card Patterns
        "glass_card": DesignPattern(
            name="Glass Card",
            category="card",
            description="Card with glassmorphism effect - blur and transparency",
            tags=["card", "glassmorphism", "blur", "modern"],
            css_snippet="""
.card-glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
}
""",
            use_cases=["Feature showcases", "Pricing cards", "Team sections"],
            complexity="simple",
            mobile_friendly=True,
            accessibility_notes="Ensure content is readable over varied backgrounds",
            examples=["apple.com", "microsoft.com"]
        ),
        
        "hover_lift_card": DesignPattern(
            name="Hover Lift Card",
            category="card",
            description="Card that lifts and shows shadow on hover",
            tags=["card", "hover", "lift", "interactive"],
            css_snippet="""
.card-lift {
  transition: transform var(--duration-normal) var(--easing-default),
              box-shadow var(--duration-normal) var(--easing-default);
}
.card-lift:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}
""",
            use_cases=["Product grids", "Blog posts", "Feature lists"],
            complexity="simple",
            mobile_friendly=True,
            accessibility_notes="Provide focus state for keyboard navigation",
            examples=["stripe.com", "vercel.com"]
        ),
        
        # Animation Patterns
        "stagger_fade_in": DesignPattern(
            name="Stagger Fade In",
            category="animation",
            description="Elements fade in with staggered timing on page load",
            tags=["animation", "fade", "stagger", "entrance"],
            css_snippet=""`
.stagger-item {
  opacity: 0;
  transform: translateY(20px);
  animation: fade-in-up 0.6s var(--easing-out) forwards;
}
.stagger-item:nth-child(1) { animation-delay: 0ms; }
.stagger-item:nth-child(2) { animation-delay: 100ms; }
.stagger-item:nth-child(3) { animation-delay: 200ms; }
@keyframes fade-in-up {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
""",
            use_cases=["Feature lists", "Team sections", "Card grids"],
            complexity="simple",
            mobile_friendly=True,
            accessibility_notes="Respect prefers-reduced-motion media query",
            examples=["linear.app", "framer.com"]
        ),
        
        "scroll_reveal": DesignPattern(
            name="Scroll Reveal",
            category="animation",
            description="Elements animate into view as user scrolls",
            tags=["animation", "scroll", "reveal", "intersection"],
            css_snippet="""
.reveal {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.6s var(--easing-out),
              transform 0.6s var(--easing-out);
}
.reveal.visible {
  opacity: 1;
  transform: translateY(0);
}
/* JavaScript: IntersectionObserver */
""",
            use_cases=["Long landing pages", "Storytelling", "Portfolios"],
            complexity="moderate",
            mobile_friendly=True,
            accessibility_notes="Content should be accessible without animation",
            examples=["apple.com", "stripe.com"]
        ),
        
        # Layout Patterns
        "bento_grid": DesignPattern(
            name="Bento Grid",
            category="layout",
            description="Grid layout with varied cell sizes like Japanese bento boxes",
            tags=["layout", "grid", "bento", "asymmetric"],
            css_snippet="""
.bento-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(3, minmax(200px, auto));
  gap: var(--spacing-4);
}
.bento-item-large {
  grid-column: span 2;
  grid-row: span 2;
}
@media (max-width: 768px) {
  .bento-grid {
    grid-template-columns: 1fr;
  }
  .bento-item-large {
    grid-column: span 1;
    grid-row: span 1;
  }
}
""",
            use_cases=["Feature showcases", "Dashboards", "Portfolios"],
            complexity="moderate",
            mobile_friendly=True,
            accessibility_notes="Ensure logical reading order in grid",
            examples=["linear.app", "raycast.com"]
        ),
        
        "masonry_layout": DesignPattern(
            name="Masonry Layout",
            category="layout",
            description="Pinterest-style masonry grid with varying heights",
            tags=["layout", "masonry", "grid", "pinterest"],
            css_snippet="""
.masonry {
  column-count: 3;
  column-gap: var(--spacing-4);
}
.masonry-item {
  break-inside: avoid;
  margin-bottom: var(--spacing-4);
}
@media (max-width: 1024px) {
  .masonry { column-count: 2; }
}
@media (max-width: 640px) {
  .masonry { column-count: 1; }
}
""",
            use_cases=["Galleries", "Blogs", "Portfolios"],
            complexity="simple",
            mobile_friendly=True,
            accessibility_notes="Consider tab order for keyboard navigation",
            examples=["pinterest.com", "dribbble.com"]
        ),
        
        # Button Patterns
        "gradient_button": DesignPattern(
            name="Gradient Button",
            category="button",
            description="Button with gradient background and hover animation",
            tags=["button", "gradient", "cta", "animated"],
            css_snippet="""
.btn-gradient {
  background: var(--gradient-primary);
  color: white;
  padding: var(--spacing-3) var(--spacing-6);
  border-radius: var(--radius-md);
  font-weight: 600;
  transition: transform var(--duration-fast),
              box-shadow var(--duration-fast);
}
.btn-gradient:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}
""",
            use_cases=["CTAs", "Sign up buttons", "Primary actions"],
            complexity="simple",
            mobile_friendly=True,
            accessibility_notes="Ensure sufficient color contrast on gradient",
            examples=["stripe.com", "vercel.com"]
        ),
        
        "glow_button": DesignPattern(
            name="Glow Button",
            category="button",
            description="Button with glowing border effect",
            tags=["button", "glow", "neon", "cyberpunk"],
            css_snippet="""
.btn-glow {
  position: relative;
  background: transparent;
  border: 2px solid var(--color-primary);
  color: var(--color-primary);
  padding: var(--spacing-3) var(--spacing-6);
  border-radius: var(--radius-md);
}
.btn-glow::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: inherit;
  background: var(--color-primary);
  opacity: 0;
  filter: blur(8px);
  transition: opacity var(--duration-normal);
  z-index: -1;
}
.btn-glow:hover::before {
  opacity: 0.5;
}
""",
            use_cases=["Gaming", "Cyberpunk themes", "Dark mode sites"],
            complexity="simple",
            mobile_friendly=True,
            accessibility_notes="Provide fallback for reduced-motion",
            examples=["gaming sites", "tech products"]
        ),
    }
    
    # Current design trends
    TRENDS = [
        TrendData(
            trend_name="Glassmorphism",
            popularity_score=85.0,
            growth_rate="stable",
            first_seen="2020",
            niche_affinity=["saas", "portfolio", "tech"],
            description="Frosted glass effect with blur and transparency",
            examples=["apple.com", "microsoft.com"]
        ),
        TrendData(
            trend_name="Dark Mode First",
            popularity_score=92.0,
            growth_rate="rising",
            first_seen="2019",
            niche_affinity=["developer_tools", "gaming", "tech", "fintech"],
            description="Designing for dark mode as primary experience",
            examples=["linear.app", "vercel.com", "github.com"]
        ),
        TrendData(
            trend_name="Micro-interactions",
            popularity_score=88.0,
            growth_rate="rising",
            first_seen="2018",
            niche_affinity=["saas", "ecommerce", "social"],
            description="Subtle animations that provide feedback and delight",
            examples=["linear.app", "notion.so", "slack.com"]
        ),
        TrendData(
            trend_name="3D Elements",
            popularity_score=75.0,
            growth_rate="rising",
            first_seen="2021",
            niche_affinity=["gaming", "ecommerce", "creative"],
            description="Three-dimensional graphics and illustrations",
            examples=["stripe.com", "framer.com"]
        ),
        TrendData(
            trend_name="Bento Grids",
            popularity_score=82.0,
            growth_rate="rising",
            first_seen="2022",
            niche_affinity=["saas", "portfolio", "dashboard"],
            description="Asymmetric grid layouts inspired by Japanese bento boxes",
            examples=["linear.app", "raycast.com"]
        ),
        TrendData(
            trend_name="Gradient Mesh",
            popularity_score=78.0,
            growth_rate="stable",
            first_seen="2020",
            niche_affinity=["saas", "startup", "creative"],
            description="Complex multi-color gradient backgrounds",
            examples=["stripe.com", "linear.app"]
        ),
        TrendData(
            trend_name="Minimalist Typography",
            popularity_score=90.0,
            growth_rate="stable",
            first_seen="2015",
            niche_affinity=["portfolio", "agency", "luxury"],
            description="Clean, large typography with ample whitespace",
            examples=["apple.com", "linear.app"]
        ),
        TrendData(
            trend_name="Scroll-driven Animations",
            popularity_score=80.0,
            growth_rate="rising",
            first_seen="2021",
            niche_affinity=["creative", "portfolio", "storytelling"],
            description="Animations triggered by scroll position",
            examples=["apple.com", "stripe.com"]
        ),
    ]
    
    # Niche-specific design recommendations
    NICHE_RECOMMENDATIONS = {
        "fintech": {
            "patterns": ["split_hero", "floating_nav", "hover_lift_card", "gradient_button"],
            "avoid": ["glow_button", "immersive_hero"],
            "color_tone": "professional, trustworthy",
            "typography": "clean, modern sans-serif",
            "animation_level": "subtle, purposeful"
        },
        "healthcare": {
            "patterns": ["split_hero", "glass_card", "stagger_fade_in"],
            "avoid": ["glow_button", "dark_mode"],
            "color_tone": "calming, clean, accessible",
            "typography": "readable, friendly",
            "animation_level": "gentle, minimal"
        },
        "ecommerce": {
            "patterns": ["hover_lift_card", "masonry_layout", "gradient_button"],
            "avoid": ["sidebar_nav"],
            "color_tone": "vibrant, trustworthy",
            "typography": "readable, product-focused",
            "animation_level": "engaging, conversion-focused"
        },
        "saas": {
            "patterns": ["split_hero", "bento_grid", "floating_nav", "gradient_mesh_hero"],
            "avoid": ["immersive_hero"],
            "color_tone": "modern, professional",
            "typography": "clean, technical",
            "animation_level": "purposeful, smooth"
        },
        "gaming": {
            "patterns": ["immersive_hero", "glow_button", "glass_card"],
            "avoid": ["minimalist"],
            "color_tone": "bold, exciting, dark",
            "typography": "distinctive, themed",
            "animation_level": "dynamic, immersive"
        },
        "developer_tools": {
            "patterns": ["sidebar_nav", "bento_grid", "stagger_fade_in"],
            "avoid": ["immersive_hero", "gradient_mesh_hero"],
            "color_tone": "dark, technical, clean",
            "typography": "monospace-friendly, technical",
            "animation_level": "minimal, functional"
        },
    }
    
    def __init__(self, memory_client: Optional[Any] = None):
        self.memory = memory_client
    
    def get_patterns_for_niche(self, niche: str) -> List[DesignPattern]:
        """Get recommended design patterns for a specific niche"""
        recommendations = self.NICHE_RECOMMENDATIONS.get(niche, {})
        pattern_names = recommendations.get("patterns", ["split_hero", "floating_nav"])
        
        patterns = []
        for name in pattern_names:
            if name in self.DESIGN_PATTERNS:
                patterns.append(self.DESIGN_PATTERNS[name])
        
        return patterns
    
    def get_patterns_by_category(self, category: str) -> List[DesignPattern]:
        """Get all patterns in a specific category"""
        return [
            pattern for pattern in self.DESIGN_PATTERNS.values()
            if pattern.category == category
        ]
    
    def get_current_trends(self) -> List[TrendData]:
        """Get current design trends"""
        return sorted(self.TRENDS, key=lambda t: t.popularity_score, reverse=True)
    
    def get_trends_for_niche(self, niche: str) -> List[TrendData]:
        """Get trends popular in a specific niche"""
        return [
            trend for trend in self.TRENDS
            if niche in trend.niche_affinity
        ]
    
    def search_patterns(self, query: str) -> List[DesignPattern]:
        """Search patterns by name, description, or tags"""
        query_lower = query.lower()
        results = []
        
        for pattern in self.DESIGN_PATTERNS.values():
            if (query_lower in pattern.name.lower() or
                query_lower in pattern.description.lower() or
                any(query_lower in tag for tag in pattern.tags)):
                results.append(pattern)
        
        return results
    
    def get_pattern(self, name: str) -> Optional[DesignPattern]:
        """Get a specific pattern by name"""
        return self.DESIGN_PATTERNS.get(name)
    
    def get_recommendations(self, niche: str) -> Dict[str, Any]:
        """Get complete design recommendations for a niche"""
        base_recommendations = self.NICHE_RECOMMENDATIONS.get(niche, {})
        
        return {
            "patterns": self.get_patterns_for_niche(niche),
            "trends": self.get_trends_for_niche(niche),
            "color_tone": base_recommendations.get("color_tone", "modern, professional"),
            "typography": base_recommendations.get("typography", "clean, modern"),
            "animation_level": base_recommendations.get("animation_level", "purposeful"),
            "avoid": base_recommendations.get("avoid", [])
        }
    
    def generate_css(self, pattern_names: List[str]) -> str:
        """Generate combined CSS for multiple patterns"""
        css_parts = []
        
        for name in pattern_names:
            pattern = self.DESIGN_PATTERNS.get(name)
            if pattern and pattern.css_snippet:
                css_parts.append(f"/* {pattern.name} */")
                css_parts.append(pattern.css_snippet)
                css_parts.append("")
        
        return "\n".join(css_parts)