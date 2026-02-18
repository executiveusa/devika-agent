"""
SYNTHIA Theme Generator
======================
Dynamic theme generation based on niche, style, and preferences.
Generates CSS, Tailwind config, and design tokens.
"""

import os
import json
import re
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import colorsys
import hashlib


@dataclass
class ThemeConfig:
    """Configuration for theme generation"""
    style: str
    niche: Optional[str]
    primary_color: Optional[str]
    secondary_color: Optional[str]
    accent_color: Optional[str]
    background_preference: str  # light, dark, auto
    font_preference: Optional[str]
    spacing_preference: str  # tight, balanced, comfortable, spacious
    border_radius_preference: str  # sharp, subtle, rounded, pill
    animation_preference: str  # minimal, smooth, dynamic, futuristic
    accessibility_mode: bool
    reduced_motion: bool
    high_contrast: bool


@dataclass
class GeneratedTheme:
    """A generated theme with all outputs"""
    name: str
    css_variables: str
    tailwind_config: Dict
    css_file: str
    scss_file: str
    design_tokens_json: Dict
    component_styles: Dict[str, str]
    dark_mode_variant: str
    light_mode_variant: str
    generated_at: datetime


class ThemeGenerator:
    """
    Dynamic theme generator for SYNTHIA.
    
    Features:
    - Niche-aware color selection
    - Typography pairing logic
    - Animation profile generation
    - Component style mapping
    - Dark/Light mode variants
    - Accessibility adjustments
    
    Usage:
        generator = ThemeGenerator()
        theme = generator.generate(ThemeConfig(
            style="dark_mode",
            niche="fintech",
            background_preference="dark"
        ))
        print(theme.css_variables)
    """
    
    # Color harmony rules
    HARMONY_RULES = {
        "complementary": lambda h: [(h + 180) % 360],
        "analogous": lambda h: [(h + 30) % 360, (h - 30) % 360],
        "triadic": lambda h: [(h + 120) % 360, (h + 240) % 360],
        "split_complementary": lambda h: [(h + 150) % 360, (h + 210) % 360],
        "tetradic": lambda h: [(h + 90) % 360, (h + 180) % 360, (h + 270) % 360],
    }
    
    # Semantic color mappings
    SEMANTIC_COLORS = {
        "error": {"hue": 0, "saturation": 70, "lightness": 50},
        "success": {"hue": 140, "saturation": 70, "lightness": 40},
        "warning": {"hue": 45, "saturation": 90, "lightness": 50},
        "info": {"hue": 210, "saturation": 80, "lightness": 50},
    }
    
    def __init__(self, memory_client: Optional[Any] = None):
        self.memory = memory_client
    
    def generate(
        self,
        config: ThemeConfig,
        design_system: Optional[Any] = None
    ) -> GeneratedTheme:
        """
        Generate a complete theme from configuration.
        
        Args:
            config: Theme configuration
            design_system: Optional design system reference
            
        Returns:
            GeneratedTheme with all theme outputs
        """
        # Generate base colors
        colors = self._generate_colors(config)
        
        # Generate typography
        typography = self._generate_typography(config)
        
        # Generate spacing
        spacing = self._generate_spacing(config)
        
        # Generate border radius
        border_radius = self._generate_border_radius(config)
        
        # Generate shadows
        shadows = self._generate_shadows(config, colors)
        
        # Generate animations
        animations = self._generate_animations(config)
        
        # Generate theme name
        theme_name = self._generate_theme_name(config, colors)
        
        # Build CSS variables
        css_variables = self._build_css_variables(
            colors, typography, spacing, border_radius, shadows, animations
        )
        
        # Build Tailwind config
        tailwind_config = self._build_tailwind_config(
            colors, typography, spacing, border_radius
        )
        
        # Build full CSS file
        css_file = self._build_css_file(
            css_variables, colors, typography, spacing, border_radius, shadows, animations
        )
        
        # Build SCSS file
        scss_file = self._build_scss_file(
            colors, typography, spacing, border_radius, shadows, animations
        )
        
        # Build design tokens JSON
        design_tokens_json = self._build_design_tokens_json(
            colors, typography, spacing, border_radius, shadows, animations
        )
        
        # Generate component styles
        component_styles = self._generate_component_styles(
            colors, typography, spacing, border_radius, shadows, animations
        )
        
        # Generate dark/light variants
        dark_variant = self._generate_dark_variant(css_variables, colors)
        light_variant = self._generate_light_variant(css_variables, colors)
        
        return GeneratedTheme(
            name=theme_name,
            css_variables=css_variables,
            tailwind_config=tailwind_config,
            css_file=css_file,
            scss_file=scss_file,
            design_tokens_json=design_tokens_json,
            component_styles=component_styles,
            dark_mode_variant=dark_variant,
            light_mode_variant=light_variant,
            generated_at=datetime.now()
        )
    
    def _generate_colors(self, config: ThemeConfig) -> Dict[str, str]:
        """Generate color palette from configuration"""
        colors = {}
        
        # Get primary color
        if config.primary_color:
            primary = config.primary_color
        else:
            primary = self._get_niche_primary_color(config.niche, config.style)
        
        # Convert to HSL for manipulation
        h, s, l = self._hex_to_hsl(primary)
        
        # Generate color harmony
        harmony_type = self._get_harmony_type(config.niche)
        harmony_hues = self.HARMONY_RULES[harmony_type](h)
        
        # Primary
        colors["primary"] = primary
        colors["primary-hover"] = self._hsl_to_hex(h, s, min(l + 10, 90))
        colors["primary-active"] = self._hsl_to_hex(h, s, max(l - 10, 10))
        colors["primary-light"] = self._hsl_to_hex(h, s * 0.3, 95)
        
        # Secondary (from harmony)
        if config.secondary_color:
            colors["secondary"] = config.secondary_color
        else:
            sec_h = harmony_hues[0] if harmony_hues else (h + 30) % 360
            colors["secondary"] = self._hsl_to_hex(sec_h, s, l)
        
        # Accent
        if config.accent_color:
            colors["accent"] = config.accent_color
        else:
            acc_h = harmony_hues[1] if len(harmony_hues) > 1 else (h + 180) % 360
            colors["accent"] = self._hsl_to_hex(acc_h, s * 1.1, l)
        
        # Background and surface
        if config.background_preference == "dark":
            colors["background"] = "#0A0E14"
            colors["surface"] = "#111827"
            colors["surface-hover"] = "#1F2937"
            colors["text-primary"] = "#F8FAFC"
            colors["text-secondary"] = "#94A3B8"
            colors["border"] = "#1E293B"
        elif config.background_preference == "light":
            colors["background"] = "#FFFFFF"
            colors["surface"] = "#F8FAFC"
            colors["surface-hover"] = "#F1F5F9"
            colors["text-primary"] = "#0F172A"
            colors["text-secondary"] = "#64748B"
            colors["border"] = "#E2E8F0"
        else:  # auto
            # Default to dark for tech/gaming, light for others
            if config.niche in ["developer_tools", "gaming", "tech"]:
                colors["background"] = "#0A0E14"
                colors["surface"] = "#111827"
                colors["text-primary"] = "#F8FAFC"
                colors["text-secondary"] = "#94A3B8"
                colors["border"] = "#1E293B"
            else:
                colors["background"] = "#FFFFFF"
                colors["surface"] = "#F8FAFC"
                colors["text-primary"] = "#0F172A"
                colors["text-secondary"] = "#64748B"
                colors["border"] = "#E2E8F0"
        
        # Semantic colors
        for name, hsl in self.SEMANTIC_COLORS.items():
            colors[name] = self._hsl_to_hex(hsl["hue"], hsl["saturation"], hsl["lightness"])
        
        # Gradients
        colors["gradient-primary"] = f"linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%)"
        colors["gradient-secondary"] = f"linear-gradient(135deg, {colors['accent']} 0%, {colors['primary']} 100%)"
        
        # Accessibility adjustments
        if config.high_contrast:
            colors = self._apply_high_contrast(colors)
        
        return colors
    
    def _get_niche_primary_color(self, niche: Optional[str], style: str) -> str:
        """Get default primary color for niche"""
        niche_colors = {
            "fintech": "#0066FF",
            "healthcare": "#00B4D8",
            "ecommerce": "#FF6B6B",
            "saas": "#6366F1",
            "education": "#4F46E5",
            "gaming": "#9B59B6",
            "developer_tools": "#22D3EE",
            "real_estate": "#2D3436",
            "food_delivery": "#E74C3C",
            "travel": "#0077B6",
            "social_media": "#E1306C",
            "ai_ml": "#6366F1",
            "legal": "#1A365D",
            "nonprofit": "#E53E3E",
            "portfolio_personal": "#000000",
        }
        
        if niche and niche in niche_colors:
            return niche_colors[niche]
        
        # Style-based defaults
        style_colors = {
            "dark_mode": "#6366F1",
            "cyberpunk": "#00F5FF",
            "minimalist": "#000000",
            "luxury": "#E11D48",
            "tech": "#6366F1",
            "futuristic": "#00D4FF",
        }
        
        return style_colors.get(style, "#6366F1")
    
    def _get_harmony_type(self, niche: Optional[str]) -> str:
        """Get color harmony type for niche"""
        harmony_map = {
            "fintech": "complementary",
            "healthcare": "analogous",
            "ecommerce": "split_complementary",
            "saas": "triadic",
            "gaming": "complementary",
            "education": "analogous",
        }
        return harmony_map.get(niche, "complementary")
    
    def _generate_typography(self, config: ThemeConfig) -> Dict[str, Any]:
        """Generate typography configuration"""
        if config.font_preference:
            # Parse font preference
            fonts = config.font_preference.split(",")
            return {
                "heading": fonts[0].strip() if fonts else "Inter",
                "body": fonts[1].strip() if len(fonts) > 1 else "Inter",
                "mono": fonts[2].strip() if len(fonts) > 2 else "JetBrains Mono",
                "heading_weights": [600, 700, 800],
                "body_weights": [400, 500, 600],
            }
        
        # Niche-based typography
        niche_typography = {
            "fintech": {"heading": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
            "healthcare": {"heading": "Poppins", "body": "Open Sans", "mono": "Roboto Mono"},
            "ecommerce": {"heading": "Poppins", "body": "Lato", "mono": "Fira Code"},
            "saas": {"heading": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
            "gaming": {"heading": "Orbitron", "body": "Rajdhani", "mono": "Share Tech Mono"},
            "developer_tools": {"heading": "JetBrains Mono", "body": "Inter", "mono": "JetBrains Mono"},
            "education": {"heading": "Poppins", "body": "Nunito", "mono": "Source Code Pro"},
            "luxury": {"heading": "Playfair Display", "body": "Lato", "mono": "Roboto Mono"},
        }
        
        if config.niche and config.niche in niche_typography:
            base = niche_typography[config.niche]
            return {
                "heading": base["heading"],
                "body": base["body"],
                "mono": base["mono"],
                "heading_weights": [600, 700, 800],
                "body_weights": [400, 500, 600],
            }
        
        # Default
        return {
            "heading": "Inter",
            "body": "Inter",
            "mono": "JetBrains Mono",
            "heading_weights": [600, 700, 800],
            "body_weights": [400, 500, 600],
        }
    
    def _generate_spacing(self, config: ThemeConfig) -> Dict[str, Any]:
        """Generate spacing scale"""
        spacing_scales = {
            "tight": {"base": 4, "scale": [2, 4, 6, 8, 12, 16, 24, 32, 48, 64]},
            "balanced": {"base": 4, "scale": [4, 8, 12, 16, 24, 32, 48, 64, 96, 128]},
            "comfortable": {"base": 8, "scale": [8, 16, 24, 32, 48, 64, 80, 96, 128, 160]},
            "spacious": {"base": 8, "scale": [16, 24, 32, 48, 64, 80, 96, 128, 160, 192]},
        }
        
        return spacing_scales.get(config.spacing_preference, spacing_scales["balanced"])
    
    def _generate_border_radius(self, config: ThemeConfig) -> Dict[str, str]:
        """Generate border radius values"""
        radius_scales = {
            "sharp": {"sm": "0", "md": "2px", "lg": "4px", "xl": "6px", "full": "9999px"},
            "subtle": {"sm": "4px", "md": "8px", "lg": "12px", "xl": "16px", "full": "9999px"},
            "rounded": {"sm": "8px", "md": "12px", "lg": "16px", "xl": "24px", "full": "9999px"},
            "pill": {"sm": "12px", "md": "16px", "lg": "24px", "xl": "32px", "full": "9999px"},
        }
        
        return radius_scales.get(config.border_radius_preference, radius_scales["subtle"])
    
    def _generate_shadows(self, config: ThemeConfig, colors: Dict) -> Dict[str, str]:
        """Generate shadow styles"""
        is_dark = colors.get("background", "#FFFFFF").lower() in ["#0a0e14", "#000000", "#0d0d0d"]
        
        if is_dark:
            # Dark mode shadows (subtle, with glow potential)
            return {
                "sm": "0 1px 2px rgba(0, 0, 0, 0.3)",
                "md": "0 4px 8px rgba(0, 0, 0, 0.4)",
                "lg": "0 8px 16px rgba(0, 0, 0, 0.5)",
                "xl": "0 16px 32px rgba(0, 0, 0, 0.6)",
                "glow": f"0 0 20px {colors.get('primary', '#6366F1')}40",
            }
        else:
            # Light mode shadows
            return {
                "sm": "0 1px 2px rgba(0, 0, 0, 0.05)",
                "md": "0 4px 8px rgba(0, 0, 0, 0.1)",
                "lg": "0 8px 16px rgba(0, 0, 0, 0.1)",
                "xl": "0 16px 32px rgba(0, 0, 0, 0.15)",
                "glow": f"0 0 20px {colors.get('primary', '#6366F1')}30",
            }
    
    def _generate_animations(self, config: ThemeConfig) -> Dict[str, str]:
        """Generate animation configuration"""
        animation_profiles = {
            "minimal": {
                "duration-fast": "100ms",
                "duration-normal": "200ms",
                "duration-slow": "300ms",
                "easing": "ease",
            },
            "smooth": {
                "duration-fast": "150ms",
                "duration-normal": "300ms",
                "duration-slow": "500ms",
                "easing": "cubic-bezier(0.4, 0, 0.2, 1)",
            },
            "dynamic": {
                "duration-fast": "200ms",
                "duration-normal": "400ms",
                "duration-slow": "600ms",
                "easing": "cubic-bezier(0.34, 1.56, 0.64, 1)",
            },
            "futuristic": {
                "duration-fast": "100ms",
                "duration-normal": "250ms",
                "duration-slow": "400ms",
                "easing": "cubic-bezier(0.22, 1, 0.36, 1)",
            },
        }
        
        animations = animation_profiles.get(
            config.animation_preference,
            animation_profiles["smooth"]
        )
        
        # Apply reduced motion if needed
        if config.reduced_motion:
            animations["duration-fast"] = "0ms"
            animations["duration-normal"] = "0ms"
            animations["duration-slow"] = "0ms"
        
        return animations
    
    def _generate_theme_name(self, config: ThemeConfig, colors: Dict) -> str:
        """Generate a unique theme name"""
        base = f"{config.style}_{config.niche or 'default'}"
        color_hash = hashlib.md5(colors.get("primary", "").encode()).hexdigest()[:6]
        return f"{base}_{color_hash}"
    
    def _build_css_variables(
        self,
        colors: Dict,
        typography: Dict,
        spacing: Dict,
        border_radius: Dict,
        shadows: Dict,
        animations: Dict
    ) -> str:
        """Build CSS custom properties"""
        lines = [":root {"]
        
        # Colors
        lines.append("  /* Colors */")
        for name, value in colors.items():
            if value.startswith("linear-gradient"):
                lines.append(f"  --gradient-{name.replace('gradient-', '')}: {value};")
            else:
                lines.append(f"  --color-{name.replace('_', '-')}: {value};")
        
        # Typography
        lines.append("\n  /* Typography */")
        lines.append(f"  --font-heading: '{typography['heading']}', sans-serif;")
        lines.append(f"  --font-body: '{typography['body']}', sans-serif;")
        lines.append(f"  --font-mono: '{typography['mono']}', monospace;")
        
        # Spacing
        lines.append("\n  /* Spacing */")
        for i, value in enumerate(spacing["scale"]):
            lines.append(f"  --spacing-{i + 1}: {value}px;")
        
        # Border radius
        lines.append("\n  /* Border Radius */")
        for name, value in border_radius.items():
            lines.append(f"  --radius-{name}: {value};")
        
        # Shadows
        lines.append("\n  /* Shadows */")
        for name, value in shadows.items():
            lines.append(f"  --shadow-{name}: {value};")
        
        # Animations
        lines.append("\n  /* Animations */")
        for name, value in animations.items():
            lines.append(f"  --{name}: {value};")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _build_tailwind_config(
        self,
        colors: Dict,
        typography: Dict,
        spacing: Dict,
        border_radius: Dict
    ) -> Dict:
        """Build Tailwind configuration"""
        return {
            "theme": {
                "extend": {
                    "colors": {
                        "primary": {
                            "DEFAULT": colors.get("primary"),
                            "hover": colors.get("primary-hover"),
                            "active": colors.get("primary-active"),
                            "light": colors.get("primary-light"),
                        },
                        "secondary": colors.get("secondary"),
                        "accent": colors.get("accent"),
                        "background": colors.get("background"),
                        "surface": {
                            "DEFAULT": colors.get("surface"),
                            "hover": colors.get("surface-hover"),
                        },
                        "text": {
                            "primary": colors.get("text-primary"),
                            "secondary": colors.get("text-secondary"),
                        },
                        "border": colors.get("border"),
                        "error": colors.get("error"),
                        "success": colors.get("success"),
                        "warning": colors.get("warning"),
                        "info": colors.get("info"),
                    },
                    "fontFamily": {
                        "heading": [typography["heading"]],
                        "body": [typography["body"]],
                        "mono": [typography["mono"]],
                    },
                    "spacing": {
                        str(i + 1): f"{v}px" for i, v in enumerate(spacing["scale"])
                    },
                    "borderRadius": {
                        "sm": border_radius["sm"],
                        "md": border_radius["md"],
                        "lg": border_radius["lg"],
                        "xl": border_radius["xl"],
                        "full": border_radius["full"],
                    },
                }
            }
        }
    
    def _build_css_file(
        self,
        css_variables: str,
        colors: Dict,
        typography: Dict,
        spacing: Dict,
        border_radius: Dict,
        shadows: Dict,
        animations: Dict
    ) -> str:
        """Build complete CSS file"""
        return f"""/* Generated Theme - SYNTHIA */
/* Generated at: {datetime.now().isoformat()} */

{css_variables}

/* Base Styles */
*,
*::before,
*::after {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

html {{
  font-family: var(--font-body);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}}

body {{
  background-color: var(--color-background);
  color: var(--color-text-primary);
}}

/* Typography */
h1, h2, h3, h4, h5, h6 {{
  font-family: var(--font-heading);
  font-weight: 700;
  line-height: 1.2;
}}

/* Focus Styles */
:focus-visible {{
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}}

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {{
  *,
  *::before,
  *::after {{
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }}
}}
"""
    
    def _build_scss_file(
        self,
        colors: Dict,
        typography: Dict,
        spacing: Dict,
        border_radius: Dict,
        shadows: Dict,
        animations: Dict
    ) -> str:
        """Build SCSS file with variables"""
        lines = ["// Generated Theme - SYNTHIA"]
        lines.append(f"// Generated at: {datetime.now().isoformat()}")
        lines.append("")
        
        # Colors
        lines.append("// Colors")
        for name, value in colors.items():
            if not value.startswith("linear-gradient"):
                lines.append(f"${name.replace('-', '_')}: {value};")
        
        # Typography
        lines.append("\n// Typography")
        lines.append(f"$font-heading: '{typography['heading']}', sans-serif;")
        lines.append(f"$font-body: '{typography['body']}', sans-serif;")
        lines.append(f"$font-mono: '{typography['mono']}', monospace;")
        
        # Spacing
        lines.append("\n// Spacing")
        for i, value in enumerate(spacing["scale"]):
            lines.append(f"$spacing-{i + 1}: {value}px;")
        
        # Border radius
        lines.append("\n// Border Radius")
        for name, value in border_radius.items():
            lines.append(f"$radius-{name}: {value};")
        
        # Shadows
        lines.append("\n// Shadows")
        for name, value in shadows.items():
            lines.append(f"$shadow-{name}: {value};")
        
        return "\n".join(lines)
    
    def _build_design_tokens_json(
        self,
        colors: Dict,
        typography: Dict,
        spacing: Dict,
        border_radius: Dict,
        shadows: Dict,
        animations: Dict
    ) -> Dict:
        """Build design tokens JSON for design tools"""
        return {
            "colors": {k: v for k, v in colors.items() if not v.startswith("linear-gradient")},
            "gradients": {k: v for k, v in colors.items() if v.startswith("linear-gradient")},
            "typography": typography,
            "spacing": spacing,
            "borderRadius": border_radius,
            "shadows": shadows,
            "animations": animations,
        }
    
    def _generate_component_styles(
        self,
        colors: Dict,
        typography: Dict,
        spacing: Dict,
        border_radius: Dict,
        shadows: Dict,
        animations: Dict
    ) -> Dict[str, str]:
        """Generate pre-built component styles"""
        return {
            "button-primary": f"""
.btn-primary {{
  background: var(--color-primary);
  color: white;
  padding: var(--spacing-3) var(--spacing-6);
  border-radius: var(--radius-md);
  font-weight: 600;
  transition: all var(--duration-normal) var(--easing);
}}
.btn-primary:hover {{
  background: var(--color-primary-hover);
  transform: translateY(-1px);
}}
""",
            "button-secondary": f"""
.btn-secondary {{
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  padding: var(--spacing-3) var(--spacing-6);
  border-radius: var(--radius-md);
  font-weight: 600;
  transition: all var(--duration-normal) var(--easing);
}}
.btn-secondary:hover {{
  background: var(--color-primary);
  color: white;
}}
""",
            "card": f"""
.card {{
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
  transition: all var(--duration-normal) var(--easing);
}}
.card:hover {{
  box-shadow: var(--shadow-lg);
}}
""",
            "input": f"""
.input {{
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-3) var(--spacing-4);
  color: var(--color-text-primary);
  transition: all var(--duration-fast) var(--easing);
}}
.input:focus {{
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}}
""",
        }
    
    def _generate_dark_variant(self, base_css: str, colors: Dict) -> str:
        """Generate dark mode variant"""
        dark_colors = {
            "background": "#0A0E14",
            "surface": "#111827",
            "surface-hover": "#1F2937",
            "text-primary": "#F8FAFC",
            "text-secondary": "#94A3B8",
            "border": "#1E293B",
        }
        
        lines = ["[data-theme='dark'] {"]
        for name, value in dark_colors.items():
            lines.append(f"  --color-{name.replace('_', '-')}: {value};")
        lines.append("}")
        
        return "\n".join(lines)
    
    def _generate_light_variant(self, base_css: str, colors: Dict) -> str:
        """Generate light mode variant"""
        light_colors = {
            "background": "#FFFFFF",
            "surface": "#F8FAFC",
            "surface-hover": "#F1F5F9",
            "text-primary": "#0F172A",
            "text-secondary": "#64748B",
            "border": "#E2E8F0",
        }
        
        lines = ["[data-theme='light'] {"]
        for name, value in light_colors.items():
            lines.append(f"  --color-{name.replace('_', '-')}: {value};")
        lines.append("}")
        
        return "\n".join(lines)
    
    def _apply_high_contrast(self, colors: Dict) -> Dict:
        """Apply high contrast adjustments for accessibility"""
        # Increase contrast ratios
        if colors.get("text-secondary"):
            # Make secondary text more visible
            h, s, l = self._hex_to_hsl(colors["text-secondary"])
            colors["text-secondary"] = self._hsl_to_hex(h, s, l + 20 if l < 50 else l - 20)
        
        if colors.get("border"):
            # Make borders more visible
            h, s, l = self._hex_to_hsl(colors["border"])
            colors["border"] = self._hsl_to_hex(h, s, l + 30 if l < 50 else l - 30)
        
        return colors
    
    def _hex_to_hsl(self, hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color to HSL"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return h * 360, s * 100, l * 100
    
    def _hsl_to_hex(self, h: float, s: float, l: float) -> str:
        """Convert HSL to hex color"""
        h = h / 360
        s = s / 100
        l = l / 100
        
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"