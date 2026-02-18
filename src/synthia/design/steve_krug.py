"""
SYNTHIA Steve Krug Principles
=============================
Design principles based on "Don't Make Me Think" by Steve Krug.
Mobile-first breakpoints, spacing systems, and usability patterns.
"""

import os
import re
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class BreakpointName(Enum):
    """Breakpoint names following mobile-first approach"""
    XS = "xs"  # 0-639px (mobile)
    SM = "sm"  # 640px+ (large mobile)
    MD = "md"  # 768px+ (tablet)
    LG = "lg"  # 1024px+ (laptop)
    XL = "xl"  # 1280px+ (desktop)
    XXL = "2xl"  # 1536px+ (large desktop)


@dataclass
class Breakpoint:
    """A responsive breakpoint"""
    name: str
    min_width: int
    max_width: Optional[int]
    container_max: int
    description: str
    typical_devices: List[str]


@dataclass
class SpacingRule:
    """A spacing rule based on Steve Krug's principles"""
    name: str
    value: int
    use_case: str
    krug_principle: str  # Which principle this supports


@dataclass
class TouchTarget:
    """Touch target specifications for mobile"""
    min_size: int  # 44px minimum per Apple HIG
    recommended_size: int
    spacing_between: int
    description: str


@dataclass
class ReadabilityRule:
    """Readability rules for content"""
    max_line_length: int
    min_line_height: float
    optimal_font_size: int
    description: str


class BreakpointSystem:
    """
    Mobile-first breakpoint system based on Steve Krug's principles.
    
    Key Principles Applied:
    - "Don't make me think" - Clear, obvious layouts at every size
    - Mobile-first - Start with mobile, enhance for larger screens
    - Consistent spacing - Predictable patterns reduce cognitive load
    - Touch-friendly - Adequate touch targets on mobile
    
    Usage:
        breakpoints = BreakpointSystem()
        css = breakpoints.generate_media_queries()
        print(breakpoints.get_breakpoint_for_width(800))
    """
    
    # Mobile-first breakpoints (min-width approach)
    BREAKPOINTS = {
        "xs": Breakpoint(
            name="xs",
            min_width=0,
            max_width=639,
            container_max=640,
            description="Mobile phones (portrait and landscape)",
            typical_devices=["iPhone SE", "iPhone 14", "Android phones"]
        ),
        "sm": Breakpoint(
            name="sm",
            min_width=640,
            max_width=767,
            container_max=640,
            description="Large phones, small tablets",
            typical_devices=["iPhone 14 Plus", "Samsung Galaxy Note"]
        ),
        "md": Breakpoint(
            name="md",
            min_width=768,
            max_width=1023,
            container_max=768,
            description="Tablets (portrait)",
            typical_devices=["iPad Mini", "iPad", "Android tablets"]
        ),
        "lg": Breakpoint(
            name="lg",
            min_width=1024,
            max_width=1279,
            container_max=1024,
            description="Tablets (landscape), laptops",
            typical_devices=["iPad Pro", "MacBook Air", "Laptops"]
        ),
        "xl": Breakpoint(
            name="xl",
            min_width=1280,
            max_width=1535,
            container_max=1280,
            description="Desktops",
            typical_devices=["Desktop monitors", "Large laptops"]
        ),
        "2xl": Breakpoint(
            name="2xl",
            min_width=1536,
            max_width=None,
            container_max=1536,
            description="Large desktops, TVs",
            typical_devices=["Large monitors", "4K displays"]
        ),
    }
    
    # Steve Krug-inspired spacing rules
    SPACING_RULES = [
        SpacingRule(
            name="touch-minimum",
            value=44,
            use_case="Minimum touch target size",
            krug_principle="Don't make users struggle to tap - adequate touch targets prevent frustration"
        ),
        SpacingRule(
            name="tap-spacing",
            value=8,
            use_case="Minimum spacing between interactive elements",
            krug_principle="Clear separation prevents accidental taps and reduces errors"
        ),
        SpacingRule(
            name="content-padding",
            value=16,
            use_case="Minimum padding around content on mobile",
            krug_principle="Content shouldn't touch edges - breathing room improves readability"
        ),
        SpacingRule(
            name="section-gap",
            value=32,
            use_case="Spacing between major sections",
            krug_principle="Clear visual hierarchy - users should see where one section ends and another begins"
        ),
        SpacingRule(
            name="heading-gap",
            value=24,
            use_case="Spacing below headings",
            krug_principle="Headings should clearly introduce their content - adequate spacing shows relationship"
        ),
        SpacingRule(
            name="form-gap",
            value=16,
            use_case="Spacing between form fields",
            krug_principle="Forms should be scannable - clear separation between fields reduces errors"
        ),
        SpacingRule(
            name="card-padding",
            value=24,
            use_case="Internal padding for cards",
            krug_principle="Cards should feel like distinct units - padding creates visual containment"
        ),
        SpacingRule(
            name="nav-item-spacing",
            value=12,
            use_case="Spacing between navigation items",
            krug_principle="Navigation should be scannable - adequate spacing prevents mis-clicks"
        ),
    ]
    
    # Touch target specifications
    TOUCH_TARGETS = {
        "minimum": TouchTarget(
            min_size=44,
            recommended_size=48,
            spacing_between=8,
            description="Minimum touch target per Apple HIG and WCAG 2.1"
        ),
        "comfortable": TouchTarget(
            min_size=48,
            recommended_size=56,
            spacing_between=12,
            description="Comfortable touch target for most users"
        ),
        "large": TouchTarget(
            min_size=56,
            recommended_size=64,
            spacing_between=16,
            description="Large touch target for accessibility or primary actions"
        ),
    }
    
    # Readability rules
    READABILITY_RULES = {
        "optimal": ReadabilityRule(
            max_line_length=75,
            min_line_height=1.5,
            optimal_font_size=16,
            description="Optimal readability for body text"
        ),
        "comfortable": ReadabilityRule(
            max_line_length=80,
            min_line_height=1.6,
            optimal_font_size=18,
            description="Comfortable reading for long-form content"
        ),
        "compact": ReadabilityRule(
            max_line_length=65,
            min_line_height=1.4,
            optimal_font_size=14,
            description="Compact text for UI elements and labels"
        ),
    }
    
    def __init__(self):
        pass
    
    def generate_media_queries(self) -> str:
        """Generate CSS media queries for all breakpoints"""
        lines = []
        
        # Base (mobile-first, no media query)
        lines.append("/* Base styles (mobile-first) */")
        lines.append("/* 0px - 639px: Mobile phones */")
        lines.append("")
        
        # sm: 640px+
        lines.append("/* 640px+: Large phones, small tablets */")
        lines.append("@media (min-width: 640px) {")
        lines.append("  /* sm styles */")
        lines.append("}")
        lines.append("")
        
        # md: 768px+
        lines.append("/* 768px+: Tablets (portrait) */")
        lines.append("@media (min-width: 768px) {")
        lines.append("  /* md styles */")
        lines.append("}")
        lines.append("")
        
        # lg: 1024px+
        lines.append("/* 1024px+: Tablets (landscape), laptops */")
        lines.append("@media (min-width: 1024px) {")
        lines.append("  /* lg styles */")
        lines.append("}")
        lines.append("")
        
        # xl: 1280px+
        lines.append("/* 1280px+: Desktops */")
        lines.append("@media (min-width: 1280px) {")
        lines.append("  /* xl styles */")
        lines.append("}")
        lines.append("")
        
        # 2xl: 1536px+
        lines.append("/* 1536px+: Large desktops */")
        lines.append("@media (min-width: 1536px) {")
        lines.append("  /* 2xl styles */")
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_container_classes(self) -> str:
        """Generate responsive container classes"""
        return """
/* Container - Mobile First */
.container {
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  padding-left: 1rem;  /* 16px - content padding rule */
  padding-right: 1rem;
}

/* sm: 640px+ */
@media (min-width: 640px) {
  .container {
    max-width: 640px;
  }
}

/* md: 768px+ */
@media (min-width: 768px) {
  .container {
    max-width: 768px;
    padding-left: 1.5rem;  /* 24px */
    padding-right: 1.5rem;
  }
}

/* lg: 1024px+ */
@media (min-width: 1024px) {
  .container {
    max-width: 1024px;
  }
}

/* xl: 1280px+ */
@media (min-width: 1280px) {
  .container {
    max-width: 1280px;
    padding-left: 2rem;  /* 32px */
    padding-right: 2rem;
  }
}

/* 2xl: 1536px+ */
@media (min-width: 1536px) {
  .container {
    max-width: 1536px;
  }
}
""".strip()
    
    def generate_spacing_utilities(self) -> str:
        """Generate spacing utility classes based on Krug's principles"""
        return """
/* Spacing Utilities - Steve Krug Principles */
/* "Don't make me think" - Consistent, predictable spacing */

/* Gap between sections */
.section-gap {
  margin-top: 2rem;    /* 32px - section-gap rule */
  margin-bottom: 2rem;
}

@media (min-width: 768px) {
  .section-gap {
    margin-top: 3rem;  /* 48px */
    margin-bottom: 3rem;
  }
}

@media (min-width: 1024px) {
  .section-gap {
    margin-top: 4rem;  /* 64px */
    margin-bottom: 4rem;
  }
}

/* Content padding - prevents edge-hugging */
.content-padding {
  padding: 1rem;  /* 16px - content-padding rule */
}

@media (min-width: 768px) {
  .content-padding {
    padding: 1.5rem;  /* 24px */
  }
}

@media (min-width: 1024px) {
  .content-padding {
    padding: 2rem;  /* 32px */
  }
}

/* Form spacing - scannable forms */
.form-gap {
  gap: 1rem;  /* 16px - form-gap rule */
}

/* Card padding - visual containment */
.card-padding {
  padding: 1.5rem;  /* 24px - card-padding rule */
}

@media (min-width: 768px) {
  .card-padding {
    padding: 2rem;  /* 32px */
  }
}

/* Navigation spacing - prevents mis-clicks */
.nav-gap {
  gap: 0.75rem;  /* 12px - nav-item-spacing rule */
}

@media (min-width: 1024px) {
  .nav-gap {
    gap: 1rem;  /* 16px */
  }
}
""".strip()
    
    def generate_touch_target_classes(self) -> str:
        """Generate touch target classes for mobile"""
        return """
/* Touch Targets - Steve Krug Principles */
/* "Don't make users struggle to tap" */

/* Minimum touch target (44px per Apple HIG) */
.touch-target {
  min-width: 44px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* Comfortable touch target */
.touch-comfortable {
  min-width: 48px;
  min-height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* Large touch target (accessibility) */
.touch-large {
  min-width: 56px;
  min-height: 56px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* Touch target spacing */
.touch-group {
  display: flex;
  gap: 0.5rem;  /* 8px minimum between touch targets */
}

@media (min-width: 768px) {
  .touch-group {
    gap: 0.75rem;  /* 12px on larger screens */
  }
}

/* Button touch targets */
.btn-touch {
  min-height: 44px;
  padding: 0.75rem 1.5rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

@media (min-width: 768px) {
  .btn-touch {
    min-height: 48px;
    padding: 1rem 2rem;
  }
}

/* Icon button touch targets */
.icon-btn-touch {
  width: 44px;
  height: 44px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

@media (min-width: 768px) {
  .icon-btn-touch {
    width: 48px;
    height: 48px;
  }
}
""".strip()
    
    def generate_readability_classes(self) -> str:
        """Generate readability classes based on Krug's principles"""
        return """
/* Readability - Steve Krug Principles */
/* "Content should be easy to scan and read" */

/* Optimal line length (75 characters max) */
.readable {
  max-width: 75ch;
  line-height: 1.5;
}

/* Comfortable reading for long-form */
.readable-comfortable {
  max-width: 80ch;
  line-height: 1.6;
  font-size: 1.125rem;  /* 18px */
}

/* Compact text for UI */
.readable-compact {
  max-width: 65ch;
  line-height: 1.4;
  font-size: 0.875rem;  /* 14px */
}

/* Body text sizing */
.body-text {
  font-size: 1rem;     /* 16px - optimal for readability */
  line-height: 1.5;
  max-width: 75ch;
}

@media (min-width: 768px) {
  .body-text {
    font-size: 1.0625rem;  /* 17px */
    line-height: 1.6;
  }
}

@media (min-width: 1024px) {
  .body-text {
    font-size: 1.125rem;  /* 18px */
  }
}

/* Heading spacing - clear hierarchy */
.heading-spacing {
  margin-bottom: 1.5rem;  /* 24px - heading-gap rule */
}

.heading-spacing + * {
  margin-top: 0;  /* Remove top margin from following element */
}

/* Paragraph spacing */
.prose p + p {
  margin-top: 1rem;  /* 16px */
}

/* List spacing */
.prose li {
  margin-bottom: 0.5rem;  /* 8px */
}

.prose ul, .prose ol {
  margin-bottom: 1rem;  /* 16px */
}
""".strip()
    
    def get_breakpoint_for_width(self, width: int) -> Breakpoint:
        """Get the appropriate breakpoint for a given width"""
        if width < 640:
            return self.BREAKPOINTS["xs"]
        elif width < 768:
            return self.BREAKPOINTS["sm"]
        elif width < 1024:
            return self.BREAKPOINTS["md"]
        elif width < 1280:
            return self.BREAKPOINTS["lg"]
        elif width < 1536:
            return self.BREAKPOINTS["xl"]
        else:
            return self.BREAKPOINTS["2xl"]
    
    def generate_responsive_grid(self) -> str:
        """Generate responsive grid system"""
        return """
/* Responsive Grid - Mobile First */
/* "Don't make me think" - Predictable grid behavior */

.grid {
  display: grid;
  gap: 1rem;  /* 16px default gap */
}

/* Auto-fit grid (responsive without breakpoints) */
.grid-auto {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

/* Fixed column grids */
.grid-cols-1 { grid-template-columns: repeat(1, 1fr); }
.grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
.grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
.grid-cols-4 { grid-template-columns: repeat(4, 1fr); }

/* Mobile: 1 column, Tablet: 2, Desktop: 3+ */
.grid-responsive {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 768px) {
  .grid-responsive {
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }
}

@media (min-width: 1024px) {
  .grid-responsive {
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
  }
}

@media (min-width: 1280px) {
  .grid-responsive {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* Bento-style grid */
.grid-bento {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 768px) {
  .grid-bento {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .bento-span-2 {
    grid-column: span 2;
  }
}

@media (min-width: 1024px) {
  .grid-bento {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .bento-span-2 {
    grid-column: span 2;
  }
  
  .bento-span-3 {
    grid-column: span 3;
  }
  
  .bento-span-4 {
    grid-column: span 4;
  }
}
""".strip()
    
    def generate_all_css(self) -> str:
        """Generate complete CSS with all responsive utilities"""
        parts = [
            "/* ========================================",
            " * SYNTHIA Responsive Design System",
            " * Based on Steve Krug's 'Don't Make Me Think'",
            " * ======================================== */",
            "",
            "/* Breakpoints */",
            self.generate_media_queries(),
            "",
            "/* Container */",
            self.generate_container_classes(),
            "",
            "/* Spacing */",
            self.generate_spacing_utilities(),
            "",
            "/* Touch Targets */",
            self.generate_touch_target_classes(),
            "",
            "/* Readability */",
            self.generate_readability_classes(),
            "",
            "/* Grid */",
            self.generate_responsive_grid(),
        ]
        
        return "\n".join(parts)


class SteveKrugPrinciples:
    """
    Steve Krug's "Don't Make Me Think" principles applied to design.
    
    Core Principles:
    1. Don't make users think - Self-evident design
    2. Users scan, they don't read - Design for scanning
    3. Users satisfice - Good enough is good enough
    4. Users muddle through - Design for error recovery
    
    Usage:
        principles = SteveKrugPrinciples()
        checklist = principles.get_design_checklist()
        issues = principles.evaluate_design(design_data)
    """
    
    PRINCIPLES = {
        "self_evident": {
            "name": "Self-Evident Design",
            "description": "Design should be immediately understandable without thought",
            "rules": [
                "Navigation should be obvious and predictable",
                "Buttons should look like buttons",
                "Links should be clearly distinguishable",
                "Forms should have clear labels",
                "Error messages should explain what went wrong and how to fix it",
            ]
        },
        "scan_not_read": {
            "name": "Design for Scanning",
            "description": "Users scan content rather than reading thoroughly",
            "rules": [
                "Use clear visual hierarchy",
                "Break content into clearly defined areas",
                "Make important elements prominent",
                "Use headings and subheadings effectively",
                "Limit the amount of text on each page",
            ]
        },
        "satisficing": {
            "name": "Satisficing Behavior",
            "description": "Users choose the first reasonable option, not the best",
            "rules": [
                "Make primary actions obvious",
                "Reduce the number of choices",
                "Provide sensible defaults",
                "Make the most common actions easiest to find",
                "Avoid overwhelming users with options",
            ]
        },
        "muddle_through": {
            "name": "Muddling Through",
            "description": "Users don't understand how things work, they just use them",
            "rules": [
                "Design for error recovery, not just prevention",
                "Provide clear feedback for actions",
                "Make it easy to go back and try again",
                "Don't require users to understand the system",
                "Test with real users who don't read instructions",
            ]
        },
        "mobile_first": {
            "name": "Mobile-First Thinking",
            "description": "Start with mobile constraints, enhance for larger screens",
            "rules": [
                "Touch targets must be at least 44x44px",
                "Content should be readable without zooming",
                "Navigation should be thumb-friendly",
                "Forms should be easy to fill on mobile",
                "Avoid hover-dependent interactions",
            ]
        },
    }
    
    def __init__(self):
        self.breakpoints = BreakpointSystem()
    
    def get_design_checklist(self) -> List[Dict[str, Any]]:
        """Get a design checklist based on Krug's principles"""
        checklist = []
        
        for principle_id, principle in self.PRINCIPLES.items():
            for rule in principle["rules"]:
                checklist.append({
                    "principle": principle["name"],
                    "rule": rule,
                    "id": f"{principle_id}_{hash(rule) % 10000:04d}"
                })
        
        return checklist
    
    def evaluate_design(self, design_data: Dict) -> Dict[str, Any]:
        """Evaluate a design against Krug's principles"""
        issues = []
        passed = []
        
        # Check touch targets
        if design_data.get("touch_targets"):
            for target in design_data["touch_targets"]:
                if target.get("width", 0) < 44 or target.get("height", 0) < 44:
                    issues.append({
                        "principle": "Mobile-First Thinking",
                        "issue": f"Touch target too small: {target.get('width')}x{target.get('height')}",
                        "recommendation": "Increase to minimum 44x44px"
                    })
                else:
                    passed.append({
                        "principle": "Mobile-First Thinking",
                        "rule": f"Touch target adequate: {target.get('width')}x{target.get('height')}"
                    })
        
        # Check line length
        if design_data.get("line_length"):
            if design_data["line_length"] > 80:
                issues.append({
                    "principle": "Design for Scanning",
                    "issue": f"Line length too long: {design_data['line_length']}ch",
                    "recommendation": "Limit to 75-80 characters for readability"
                })
        
        # Check navigation items
        if design_data.get("nav_items"):
            if len(design_data["nav_items"]) > 7:
                issues.append({
                    "principle": "Satisficing Behavior",
                    "issue": f"Too many navigation items: {len(design_data['nav_items'])}",
                    "recommendation": "Limit to 5-7 items to reduce cognitive load"
                })
        
        return {
            "issues": issues,
            "passed": passed,
            "score": len(passed) / max(len(passed) + len(issues), 1) * 100
        }
    
    def get_principle(self, principle_id: str) -> Optional[Dict]:
        """Get a specific principle by ID"""
        return self.PRINCIPLES.get(principle_id)
    
    def get_all_principles(self) -> Dict[str, Dict]:
        """Get all principles"""
        return self.PRINCIPLES
    
    def generate_usability_report(self, evaluation: Dict) -> str:
        """Generate a usability report from evaluation results"""
        lines = [
            "# Usability Report - Steve Krug Principles",
            "",
            "## Summary",
            f"- **Score:** {evaluation['score']:.1f}%",
            f"- **Issues Found:** {len(evaluation['issues'])}",
            f"- **Rules Passed:** {len(evaluation['passed'])}",
            "",
        ]
        
        if evaluation["issues"]:
            lines.append("## Issues to Address")
            for i, issue in enumerate(evaluation["issues"], 1):
                lines.append(f"### {i}. {issue['issue']}")
                lines.append(f"- **Principle:** {issue['principle']}")
                lines.append(f"- **Recommendation:** {issue['recommendation']}")
                lines.append("")
        
        if evaluation["passed"]:
            lines.append("## Rules Passed")
            for item in evaluation["passed"]:
                lines.append(f"- [{item['principle']}] {item['rule']}")
        
        return "\n".join(lines)