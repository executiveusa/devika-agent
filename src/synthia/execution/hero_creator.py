"""
Hero Section Creator with Niche-Specific Patterns
=================================================

Generates hero sections with 25+ niche-specific patterns.
Supports:
- Industry-specific hero designs
- Responsive layouts
- SEO-optimized content
- Image integration
"""

import logging
import random
from typing import Any, Dict, List, Optional
from jinja2 import Environment, FileSystemLoader

from ..investigation.niche_detector import NicheDetector
from ..design.theme_generator import ThemeGenerator
from ..execution.unsplash_integration import UnsplashAPI

logger = logging.getLogger("synthia.execution.hero_creator")


class HeroCreator:
    """
    Generates hero sections with niche-specific patterns.
    
    Key features:
    - 25+ niche-specific hero patterns
    - Responsive design templates
    - SEO-optimized content
    - Image integration with Unsplash
    """
    
    # Niche-specific hero patterns
    HERO_PATTERNS = {
        "technology": [
            {
                "id": "tech-modern",
                "name": "Modern Tech Hero",
                "description": "Clean, modern hero with gradient background",
                "template": "templates/hero/tech-modern.html"
            },
            {
                "id": "tech-gaming",
                "name": "Gaming Hero",
                "description": "Dynamic hero with neon accents",
                "template": "templates/hero/tech-gaming.html"
            },
            {
                "id": "tech-startup",
                "name": "Startup Hero",
                "description": "Bold, energetic hero for startups",
                "template": "templates/hero/tech-startup.html"
            }
        ],
        "ecommerce": [
            {
                "id": "ecommerce-product",
                "name": "Product Focus",
                "description": "Product-centric hero with CTA",
                "template": "templates/hero/ecommerce-product.html"
            },
            {
                "id": "ecommerce-sales",
                "name": "Sales Hero",
                "description": "Promotional hero with discount highlights",
                "template": "templates/hero/ecommerce-sales.html"
            },
            {
                "id": "ecommerce-minimal",
                "name": "Minimal Ecommerce",
                "description": "Clean, minimalist product showcase",
                "template": "templates/hero/ecommerce-minimal.html"
            }
        ],
        "healthcare": [
            {
                "id": "healthcare-professional",
                "name": "Professional Healthcare",
                "description": "Trustworthy, clean healthcare hero",
                "template": "templates/hero/healthcare-professional.html"
            },
            {
                "id": "healthcare-Wellness",
                "name": "Wellness Hero",
                "description": "Relaxing, wellness-focused hero",
                "template": "templates/hero/healthcare-wellness.html"
            },
            {
                "id": "healthcare-medical",
                "name": "Medical Practice",
                "description": "Medical practice hero with trust indicators",
                "template": "templates/hero/healthcare-medical.html"
            }
        ],
        "finance": [
            {
                "id": "finance-professional",
                "name": "Professional Finance",
                "description": "Clean, professional financial services hero",
                "template": "templates/hero/finance-professional.html"
            },
            {
                "id": "finance-modern",
                "name": "Modern Finance",
                "description": "Modern financial tech hero",
                "template": "templates/hero/finance-modern.html"
            },
            {
                "id": "finance-investment",
                "name": "Investment Hero",
                "description": "Investment-focused hero with charts",
                "template": "templates/hero/finance-investment.html"
            }
        ],
        "education": [
            {
                "id": "education-university",
                "name": "University Hero",
                "description": "Academic institution hero",
                "template": "templates/hero/education-university.html"
            },
            {
                "id": "education-online",
                "name": "Online Learning",
                "description": "E-learning platform hero",
                "template": "templates/hero/education-online.html"
            },
            {
                "id": "education-corporate",
                "name": "Corporate Training",
                "description": "Professional training hero",
                "template": "templates/hero/education-corporate.html"
            }
        ],
        "real_estate": [
            {
                "id": "realestate-luxury",
                "name": "Luxury Real Estate",
                "description": "High-end property showcase",
                "template": "templates/hero/realestate-luxury.html"
            },
            {
                "id": "realestate-modern",
                "name": "Modern Properties",
                "description": "Contemporary property showcase",
                "template": "templates/hero/realestate-modern.html"
            },
            {
                "id": "realestate-rental",
                "name": "Rental Properties",
                "description": "Rental property search hero",
                "template": "templates/hero/realestate-rental.html"
            }
        ],
        "creative": [
            {
                "id": "creative-agency",
                "name": "Agency Hero",
                "description": "Creative agency showcase",
                "template": "templates/hero/creative-agency.html"
            },
            {
                "id": "creative-portfolio",
                "name": "Portfolio Hero",
                "description": "Artist/designer portfolio",
                "template": "templates/hero/creative-portfolio.html"
            },
            {
                "id": "creative-studio",
                "name": "Studio Hero",
                "description": "Design studio showcase",
                "template": "templates/hero/creative-studio.html"
            }
        ],
        "restaurant": [
            {
                "id": "restaurant-food",
                "name": "Food Showcase",
                "description": "Delicious food showcase",
                "template": "templates/hero/restaurant-food.html"
            },
            {
                "id": "restaurant-ambience",
                "name": "Ambience Hero",
                "description": "Restaurant atmosphere showcase",
                "template": "templates/hero/restaurant-ambience.html"
            },
            {
                "id": "restaurant-menu",
                "name": "Menu Focus",
                "description": "Menu-centric hero",
                "template": "templates/hero/restaurant-menu.html"
            }
        ]
    }
    
    def __init__(self, niche_detector: Optional[NicheDetector] = None):
        self.niche_detector = niche_detector or NicheDetector()
        self.theme_generator = ThemeGenerator()
        self.unsplash_api = UnsplashAPI()
        self.jinja_env = Environment(
            loader=FileSystemLoader("src/synthia/knowledge/hero_patterns"),
            autoescape=True
        )
        
        logger.info("Hero creator initialized")
    
    def detect_niche(self, business_description: str) -> str:
        """Detect business niche from description"""
        try:
            niche = self.niche_detector.detect_niche(business_description)
            logger.debug(f"Detected niche: {niche}")
            return niche
        except Exception as e:
            logger.warning(f"Niche detection failed: {e}")
            return "technology"
    
    def select_hero_pattern(self, niche: str) -> Dict[str, str]:
        """Select hero pattern based on niche"""
        if niche in self.HERO_PATTERNS:
            patterns = self.HERO_PATTERNS[niche]
            selected = random.choice(patterns)
            logger.debug(f"Selected hero pattern: {selected['name']} for niche: {niche}")
            return selected
        
        # Fallback to technology niche
        patterns = self.HERO_PATTERNS["technology"]
        selected = random.choice(patterns)
        logger.debug(f"Fallback to hero pattern: {selected['name']}")
        return selected
    
    def generate_hero_content(self, business: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hero content based on business details"""
        niche = business.get("niche", "technology")
        
        content = {
            "headline": self._generate_headline(business),
            "subtitle": self._generate_subtitle(business),
            "cta_text": self._generate_cta(niche),
            "secondary_cta": self._generate_secondary_cta(niche),
            "features": self._generate_features(business),
            "image": self._generate_image(business)
        }
        
        logger.debug("Generated hero content")
        return content
    
    def _generate_headline(self, business: Dict[str, Any]) -> str:
        """Generate SEO-optimized headline"""
        name = business.get("name", "Your Business")
        niche = business.get("niche", "business")
        value_prop = business.get("value_proposition", "innovative solutions")
        
        return f"{name} - {value_prop} for {niche}"
    
    def _generate_subtitle(self, business: Dict[str, Any]) -> str:
        """Generate compelling subtitle"""
        description = business.get("description", "Transforming the way you work")
        return description
    
    def _generate_cta(self, niche: str) -> str:
        """Generate call-to-action text based on niche"""
        cta_map = {
            "technology": "Get Started",
            "ecommerce": "Shop Now",
            "healthcare": "Book Appointment",
            "finance": "Learn More",
            "education": "Explore Courses",
            "real_estate": "View Properties",
            "creative": "See Portfolio",
            "restaurant": "Reserve Table"
        }
        
        return cta_map.get(niche, "Get Started")
    
    def _generate_secondary_cta(self, niche: str) -> str:
        """Generate secondary call-to-action text"""
        cta_map = {
            "technology": "Watch Demo",
            "ecommerce": "View Collections",
            "healthcare": "Meet Our Team",
            "finance": "Calculate Savings",
            "education": "Free Resources",
            "real_estate": "Request Tour",
            "creative": "Our Process",
            "restaurant": "View Menu"
        }
        
        return cta_map.get(niche, "Learn More")
    
    def _generate_features(self, business: Dict[str, Any]) -> List[str]:
        """Generate key features for hero"""
        default_features = [
            "Industry-leading solutions",
            "Trusted by thousands",
            "24/7 support",
            "Easy to use"
        ]
        
        return business.get("key_features", default_features)
    
    def _generate_image(self, business: Dict[str, Any]) -> str:
        """Generate hero image URL from Unsplash"""
        niche = business.get("niche", "technology")
        query = business.get("image_query", niche)
        
        try:
            images = self.unsplash_api.search_images(query, 1)
            if images:
                return images[0]
        except Exception as e:
            logger.warning(f"Image search failed: {e}")
        
        # Fallback image
        return "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1920&q=80"
    
    def render_hero(self, pattern: Dict[str, str], content: Dict[str, Any]) -> str:
        """Render hero template with content"""
        try:
            template = self.jinja_env.get_template(pattern["template"])
            return template.render(content)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return self._render_fallback_hero(content)
    
    def _render_fallback_hero(self, content: Dict[str, Any]) -> str:
        """Fallback hero template if pattern fails"""
        return f"""
<section class="hero">
    <div class="hero-content">
        <h1>{content['headline']}</h1>
        <p>{content['subtitle']}</p>
        <div class="hero-cta">
            <button class="btn-primary">{content['cta_text']}</button>
            <button class="btn-secondary">{content['secondary_cta']}</button>
        </div>
    </div>
    <div class="hero-image">
        <img src="{content['image']}" alt="Hero image">
    </div>
</section>
"""
    
    def generate_hero_section(self, business: Dict[str, Any]) -> str:
        """Generate complete hero section"""
        try:
            # Detect niche
            niche = self.detect_niche(business.get("description", ""))
            
            # Select hero pattern
            pattern = self.select_hero_pattern(niche)
            
            # Generate content
            content = self.generate_hero_content(business)
            
            # Render hero
            hero_html = self.render_hero(pattern, content)
            
            logger.info("Hero section generated successfully")
            return hero_html
        except Exception as e:
            logger.error(f"Hero generation failed: {e}")
            # Return minimal fallback hero
            return self._render_fallback_hero({
                "headline": business.get("name", "Your Business"),
                "subtitle": business.get("description", "Welcome to our website"),
                "cta_text": "Get Started",
                "secondary_cta": "Learn More",
                "features": ["Professional services", "Trusted partner"],
                "image": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1920&q=80"
            })
    
    def generate_hero_styles(self, theme: Dict[str, Any]) -> str:
        """Generate hero section styles"""
        try:
            styles = f"""
.hero {{
    background: {theme.get('primary_color', '#6366f1')};
    color: {theme.get('text_color', '#ffffff')};
    padding: 80px 20px;
    text-align: center;
    position: relative;
}}

.hero-content {{
    max-width: 1200px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
}}

.hero h1 {{
    font-size: 3rem;
    margin-bottom: 20px;
    font-weight: bold;
}}

.hero p {{
    font-size: 1.5rem;
    margin-bottom: 30px;
    opacity: 0.9;
}}

.hero-cta {{
    display: flex;
    gap: 15px;
    justify-content: center;
    flex-wrap: wrap;
}}

.btn-primary {{
    background: {theme.get('secondary_color', '#10b981')};
    color: white;
    padding: 15px 30px;
    border: none;
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
}}

.btn-primary:hover {{
    background: {self._darken_color(theme.get('secondary_color', '#10b981'), 10)};
    transform: translateY(-2px);
}}

.btn-secondary {{
    background: transparent;
    color: {theme.get('text_color', '#ffffff')};
    padding: 15px 30px;
    border: 2px solid {theme.get('text_color', '#ffffff')};
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
}}

.btn-secondary:hover {{
    background: {theme.get('text_color', '#ffffff')};
    color: {theme.get('primary_color', '#6366f1')};
}}

.hero-image {{
    margin-top: 40px;
    max-width: 100%;
    height: auto;
}}

@media (max-width: 768px) {{
    .hero h1 {{
        font-size: 2rem;
    }}
    
    .hero p {{
        font-size: 1.2rem;
    }}
}}
"""
            return styles
        except Exception as e:
            logger.error(f"Style generation failed: {e}")
            return ""
    
    def _darken_color(self, color: str, percent: int) -> str:
        """Darken a color by percentage"""
        import colorsys
        
        # Convert hex to RGB
        color = color.lstrip('#')
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        # Convert RGB to HLS
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        
        # Darken
        l = max(0, l - (percent/100))
        
        # Convert back to RGB
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
