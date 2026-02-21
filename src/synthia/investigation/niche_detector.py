"""
SYNTHIA Niche Detector
======================
Multi-signal niche detection for context-aware design decisions.

Detects project niche from code, dependencies, colors, and content
to provide tailored design recommendations.
"""

import os
import re
import json
from typing import Optional, Dict, List, Any, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DesignDirection:
    """Design direction for a niche"""
    color_palette: List[str]
    typography: Dict[str, str]
    spacing_scale: str
    border_radius: str
    shadow_style: str
    animation_style: str
    layout_pattern: str
    imagery_style: str
    cta_style: str
    form_style: str


@dataclass
class NicheProfile:
    """Complete niche profile with design recommendations"""
    niche_type: str
    confidence: float
    signals: Dict[str, float]
    keywords: List[str]
    competitors: List[str]
    design_direction: DesignDirection
    user_expectations: List[str]
    conversion_goals: List[str]
    accessibility_priority: str
    mobile_importance: str


class NicheDetector:
    """
    Multi-signal niche detection for context-aware design.
    
    Analyzes:
    - Code content and structure
    - Dependencies and frameworks
    - SVG colors and styles
    - Configuration files
    - Documentation and comments
    
    Usage:
        detector = NicheDetector()
        profile = detector.detect(scan_result)
        print(f"Niche: {profile.niche_type} (confidence: {profile.confidence})")
    """
    
    # Niche profiles with design directions
    NICHES = {
        "fintech": {
            "keywords": ["payment", "banking", "finance", "crypto", "wallet", "transaction", "investment", "trading", "loan", "credit", "debit", "money", "fund", "portfolio", "stock", "forex", "blockchain", "defi", "nft"],
            "dependencies": ["stripe", "paypal", "plaid", "coinbase", "metamask", "web3", "ethers", "alpaca", "polygon", "binance"],
            "colors": ["#0066FF", "#00C853", "#1A1A2E", "#16213E", "#0F3460", "#E94560"],
            "design": {
                "color_palette": ["#0A0E14", "#0066FF", "#00C853", "#FFFFFF", "#1A1A2E"],
                "typography": {"heading": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
                "spacing_scale": "tight",
                "border_radius": "small",
                "shadow_style": "subtle",
                "animation_style": "minimal",
                "layout_pattern": "dashboard",
                "imagery_style": "abstract",
                "cta_style": "solid",
                "form_style": "minimal"
            },
            "competitors": ["Stripe", "Coinbase", "Robinhood", "Revolut"],
            "user_expectations": ["Security", "Speed", "Transparency", "Trust"],
            "conversion_goals": ["Sign up", "Link bank", "First transaction"],
            "accessibility_priority": "high",
            "mobile_importance": "critical"
        },
        
        "healthcare": {
            "keywords": ["health", "medical", "patient", "doctor", "hospital", "clinic", "pharmacy", "prescription", "appointment", "diagnosis", "treatment", "wellness", "fitness", "mental", "therapy", "telehealth", "ehr", "emr"],
            "dependencies": ["epic", "cerner", "healthkit", "fhir", "hl7", "openemr", "fhirclient"],
            "colors": ["#00B4D8", "#90E0EF", "#CAF0F8", "#0077B6", "#023E8A"],
            "design": {
                "color_palette": ["#FFFFFF", "#00B4D8", "#0077B6", "#F8F9FA", "#E9ECEF"],
                "typography": {"heading": "Poppins", "body": "Open Sans", "mono": "Roboto Mono"},
                "spacing_scale": "comfortable",
                "border_radius": "medium",
                "shadow_style": "soft",
                "animation_style": "gentle",
                "layout_pattern": "card-based",
                "imagery_style": "people-first",
                "cta_style": "rounded",
                "form_style": "accessible"
            },
            "competitors": ["Zocdoc", "Teladoc", "MyChart", "Headspace"],
            "user_expectations": ["Privacy", "Ease of use", "Trust", "Accessibility"],
            "conversion_goals": ["Book appointment", "Complete profile", "Enable notifications"],
            "accessibility_priority": "critical",
            "mobile_importance": "high"
        },
        
        "ecommerce": {
            "keywords": ["shop", "store", "cart", "checkout", "product", "order", "shipping", "payment", "inventory", "catalog", "wishlist", "review", "rating", "discount", "coupon", "brand", "merchant"],
            "dependencies": ["shopify", "woocommerce", "magento", "bigcommerce", "stripe", "paypal", "snipcart", "medusa"],
            "colors": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"],
            "design": {
                "color_palette": ["#FFFFFF", "#1A1A1A", "#FF6B6B", "#4ECDC4", "#F5F5F5"],
                "typography": {"heading": "Poppins", "body": "Lato", "mono": "Fira Code"},
                "spacing_scale": "balanced",
                "border_radius": "medium",
                "shadow_style": "elevated",
                "animation_style": "smooth",
                "layout_pattern": "grid",
                "imagery_style": "product-focused",
                "cta_style": "prominent",
                "form_style": "streamlined"
            },
            "competitors": ["Amazon", "Shopify", "Etsy", "ASOS"],
            "user_expectations": ["Fast checkout", "Product images", "Reviews", "Returns policy"],
            "conversion_goals": ["Add to cart", "Complete purchase", "Leave review"],
            "accessibility_priority": "high",
            "mobile_importance": "critical"
        },
        
        "saas": {
            "keywords": ["dashboard", "analytics", "report", "team", "workspace", "project", "task", "workflow", "automation", "integration", "api", "subscription", "plan", "billing", "onboarding", "settings", "admin"],
            "dependencies": ["stripe", "auth0", "clerk", "next-auth", "supabase", "firebase", "planetscale", "upstash"],
            "colors": ["#6366F1", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B", "#3B82F6"],
            "design": {
                "color_palette": ["#0F172A", "#1E293B", "#6366F1", "#10B981", "#FFFFFF"],
                "typography": {"heading": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
                "spacing_scale": "balanced",
                "border_radius": "medium",
                "shadow_style": "modern",
                "animation_style": "purposeful",
                "layout_pattern": "sidebar",
                "imagery_style": "abstract-ui",
                "cta_style": "gradient",
                "form_style": "clean"
            },
            "competitors": ["Notion", "Slack", "Linear", "Vercel"],
            "user_expectations": ["Fast onboarding", "Clear pricing", "Integrations", "Support"],
            "conversion_goals": ["Start trial", "Upgrade plan", "Invite team"],
            "accessibility_priority": "high",
            "mobile_importance": "medium"
        },
        
        "education": {
            "keywords": ["course", "lesson", "learn", "teach", "student", "teacher", "class", "quiz", "exam", "grade", "curriculum", "enrollment", "certificate", "video", "lecture", "tutorial", "academy", "school", "university"],
            "dependencies": ["moodle", "canvas", "blackboard", "teachable", "thinkific", "kajabi", "udemy-api", "coursera"],
            "colors": ["#4F46E5", "#7C3AED", "#EC4899", "#14B8A6", "#F59E0B", "#10B981"],
            "design": {
                "color_palette": ["#FFFFFF", "#4F46E5", "#14B8A6", "#F8FAFC", "#1E293B"],
                "typography": {"heading": "Poppins", "body": "Nunito", "mono": "Source Code Pro"},
                "spacing_scale": "comfortable",
                "border_radius": "large",
                "shadow_style": "soft",
                "animation_style": "playful",
                "layout_pattern": "card-based",
                "imagery_style": "illustrations",
                "cta_style": "rounded",
                "form_style": "friendly"
            },
            "competitors": ["Coursera", "Udemy", "Khan Academy", "Duolingo"],
            "user_expectations": ["Progress tracking", "Certificates", "Mobile access", "Community"],
            "conversion_goals": ["Enroll", "Complete lesson", "Get certificate"],
            "accessibility_priority": "critical",
            "mobile_importance": "high"
        },
        
        "real_estate": {
            "keywords": ["property", "listing", "house", "apartment", "rent", "lease", "buy", "sell", "agent", "broker", "mortgage", "valuation", "neighborhood", "bedroom", "bathroom", "sqft", "zillow", "realtor"],
            "dependencies": ["zillow-api", "realtor-api", "mapbox", "google-maps", "stripe", "docuSign"],
            "colors": ["#2D3436", "#00B894", "#0984E3", "#6C5CE7", "#FDCB6E", "#E17055"],
            "design": {
                "color_palette": ["#FFFFFF", "#2D3436", "#00B894", "#F5F5F5", "#0984E3"],
                "typography": {"heading": "Playfair Display", "body": "Lato", "mono": "Roboto Mono"},
                "spacing_scale": "spacious",
                "border_radius": "medium",
                "shadow_style": "elevated",
                "animation_style": "smooth",
                "layout_pattern": "gallery",
                "imagery_style": "photography",
                "cta_style": "solid",
                "form_style": "detailed"
            },
            "competitors": ["Zillow", "Redfin", "Realtor.com", "Trulia"],
            "user_expectations": ["Photos", "Maps", "Price history", "Contact agent"],
            "conversion_goals": ["Schedule viewing", "Contact agent", "Save listing"],
            "accessibility_priority": "medium",
            "mobile_importance": "high"
        },
        
        "food_delivery": {
            "keywords": ["restaurant", "menu", "order", "delivery", "food", "cuisine", "takeout", "dine-in", "reservation", "chef", "recipe", "ingredient", "meal", "catering", "grocery", "fresh"],
            "dependencies": ["doordash-api", "ubereats-api", "grubhub-api", "stripe", "twilio", "sendgrid"],
            "colors": ["#E74C3C", "#F39C12", "#27AE60", "#3498DB", "#9B59B6", "#1ABC9C"],
            "design": {
                "color_palette": ["#FFFFFF", "#E74C3C", "#27AE60", "#F8F8F8", "#2C3E50"],
                "typography": {"heading": "Poppins", "body": "Open Sans", "mono": "Fira Code"},
                "spacing_scale": "balanced",
                "border_radius": "large",
                "shadow_style": "soft",
                "animation_style": "playful",
                "layout_pattern": "card-based",
                "imagery_style": "food-photography",
                "cta_style": "prominent",
                "form_style": "minimal"
            },
            "competitors": ["DoorDash", "Uber Eats", "Grubhub", "Instacart"],
            "user_expectations": ["Fast delivery", "Order tracking", "Photos", "Reviews"],
            "conversion_goals": ["Place order", "Reorder", "Leave review"],
            "accessibility_priority": "medium",
            "mobile_importance": "critical"
        },
        
        "travel": {
            "keywords": ["flight", "hotel", "booking", "vacation", "trip", "destination", "travel", "airline", "resort", "tour", "adventure", "explore", "itinerary", "passport", "visa", "luggage", "cruise", "car-rental"],
            "dependencies": ["amadeus", "sabre", "booking-api", "expedia-api", "tripadvisor-api", "google-flights", "skyscanner"],
            "colors": ["#0077B6", "#00B4D8", "#90E0EF", "#CAF0F8", "#023E8A", "#48CAE4"],
            "design": {
                "color_palette": ["#FFFFFF", "#0077B6", "#00B4D8", "#F0F9FF", "#023E8A"],
                "typography": {"heading": "Poppins", "body": "Inter", "mono": "Roboto Mono"},
                "spacing_scale": "spacious",
                "border_radius": "large",
                "shadow_style": "soft",
                "animation_style": "smooth",
                "layout_pattern": "search-focused",
                "imagery_style": "destination-photography",
                "cta_style": "gradient",
                "form_style": "search-optimized"
            },
            "competitors": ["Airbnb", "Booking.com", "Expedia", "Kayak"],
            "user_expectations": ["Price comparison", "Reviews", "Photos", "Cancellation policy"],
            "conversion_goals": ["Book", "Save trip", "Share itinerary"],
            "accessibility_priority": "medium",
            "mobile_importance": "high"
        },
        
        "social_media": {
            "keywords": ["post", "feed", "profile", "follow", "like", "share", "comment", "message", "notification", "friend", "group", "community", "timeline", "story", "reel", "live", "chat", "dm"],
            "dependencies": ["firebase", "supabase", "pusher", "socket.io", "redis", "mongodb", "neo4j"],
            "colors": ["#E1306C", "#405DE6", "#5851DB", "#833AB4", "#C13584", "#FD1D1D", "#F77737", "#FCAF45"],
            "design": {
                "color_palette": ["#FFFFFF", "#1A1A1A", "#E1306C", "#405DE6", "#F5F5F5"],
                "typography": {"heading": "Inter", "body": "Inter", "mono": "SF Mono"},
                "spacing_scale": "tight",
                "border_radius": "full",
                "shadow_style": "minimal",
                "animation_style": "dynamic",
                "layout_pattern": "feed",
                "imagery_style": "user-generated",
                "cta_style": "icon-based",
                "form_style": "inline"
            },
            "competitors": ["Instagram", "Twitter", "TikTok", "LinkedIn"],
            "user_expectations": ["Real-time updates", "Easy sharing", "Discovery", "Privacy controls"],
            "conversion_goals": ["Create account", "Follow users", "Post content"],
            "accessibility_priority": "high",
            "mobile_importance": "critical"
        },
        
        "developer_tools": {
            "keywords": ["code", "git", "repository", "commit", "branch", "merge", "pull", "push", "issue", "pr", "pipeline", "deploy", "build", "test", "lint", "debug", "terminal", "ide", "api", "sdk"],
            "dependencies": ["github-api", "gitlab-api", "bitbucket-api", "docker", "kubernetes", "terraform", "ansible", "jenkins"],
            "colors": ["#238636", "#1F6FEB", "#F78166", "#A371F7", "#3FB950", "#58A6FF"],
            "design": {
                "color_palette": ["#0D1117", "#161B22", "#238636", "#1F6FEB", "#C9D1D9"],
                "typography": {"heading": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
                "spacing_scale": "tight",
                "border_radius": "small",
                "shadow_style": "minimal",
                "animation_style": "functional",
                "layout_pattern": "terminal-inspired",
                "imagery_style": "code-screenshots",
                "cta_style": "outlined",
                "form_style": "developer-friendly"
            },
            "competitors": ["GitHub", "GitLab", "Vercel", "Netlify"],
            "user_expectations": ["Documentation", "API access", "CLI tools", "Status page"],
            "conversion_goals": ["Start project", "Connect repo", "Deploy"],
            "accessibility_priority": "medium",
            "mobile_importance": "low"
        },
        
        "ai_ml": {
            "keywords": ["model", "training", "inference", "neural", "machine-learning", "deep-learning", "ai", "ml", "nlp", "computer-vision", "transformer", "embedding", "vector", "dataset", "prediction", "classification", "regression", "clustering"],
            "dependencies": ["tensorflow", "pytorch", "keras", "scikit-learn", "huggingface", "openai", "anthropic", "langchain", "llamaindex", "pinecone", "weaviate"],
            "colors": ["#6366F1", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B", "#3B82F6", "#06B6D4"],
            "design": {
                "color_palette": ["#0F172A", "#1E293B", "#6366F1", "#10B981", "#F8FAFC"],
                "typography": {"heading": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
                "spacing_scale": "balanced",
                "border_radius": "medium",
                "shadow_style": "glow",
                "animation_style": "futuristic",
                "layout_pattern": "playground",
                "imagery_style": "abstract-neural",
                "cta_style": "gradient",
                "form_style": "minimal"
            },
            "competitors": ["OpenAI", "Hugging Face", "Replicate", "Together AI"],
            "user_expectations": ["API documentation", "Playground", "Examples", "Pricing calculator"],
            "conversion_goals": ["Try model", "Get API key", "Integrate"],
            "accessibility_priority": "medium",
            "mobile_importance": "low"
        },
        
        "gaming": {
            "keywords": ["game", "play", "player", "level", "score", "achievement", "multiplayer", "single-player", "arcade", "puzzle", "rpg", "fps", "moba", "battle-royale", "esports", "stream", "twitch", "discord"],
            "dependencies": ["unity", "unreal", "phaser", "three.js", "babylon.js", "socket.io", "playfab", "gamesparks"],
            "colors": ["#9B59B6", "#E74C3C", "#2ECC71", "#3498DB", "#F39C12", "#1ABC9C", "#E91E63"],
            "design": {
                "color_palette": ["#0A0A0A", "#9B59B6", "#E74C3C", "#2ECC71", "#FFFFFF"],
                "typography": {"heading": "Orbitron", "body": "Rajdhani", "mono": "Share Tech Mono"},
                "spacing_scale": "dynamic",
                "border_radius": "sharp",
                "shadow_style": "neon",
                "animation_style": "dynamic",
                "layout_pattern": "immersive",
                "imagery_style": "game-art",
                "cta_style": "animated",
                "form_style": "themed"
            },
            "competitors": ["Steam", "Epic Games", "Roblox", "Discord"],
            "user_expectations": ["Performance", "Social features", "Achievements", "Customization"],
            "conversion_goals": ["Play game", "Invite friends", "Purchase"],
            "accessibility_priority": "medium",
            "mobile_importance": "high"
        },
        
        "legal": {
            "keywords": ["law", "legal", "attorney", "lawyer", "court", "case", "contract", "agreement", "compliance", "regulation", "policy", "terms", "privacy", "gdpr", "hipaa", "document", "signature"],
            "dependencies": ["docuSign", "hellosign", "pandaDoc", "ironclad", "linkSquares", "clio"],
            "colors": ["#1A365D", "#2C5282", "#2B6CB0", "#3182CE", "#4299E1", "#63B3ED"],
            "design": {
                "color_palette": ["#FFFFFF", "#1A365D", "#2C5282", "#F7FAFC", "#2D3748"],
                "typography": {"heading": "Merriweather", "body": "Open Sans", "mono": "Roboto Mono"},
                "spacing_scale": "formal",
                "border_radius": "small",
                "shadow_style": "subtle",
                "animation_style": "minimal",
                "layout_pattern": "document-focused",
                "imagery_style": "professional",
                "cta_style": "solid",
                "form_style": "detailed"
            },
            "competitors": ["LegalZoom", "Rocket Lawyer", "Clio", "Ironclad"],
            "user_expectations": ["Trust", "Security", "Clarity", "Support"],
            "conversion_goals": ["Consultation", "Document creation", "Sign up"],
            "accessibility_priority": "high",
            "mobile_importance": "medium"
        },
        
        "nonprofit": {
            "keywords": ["donate", "charity", "volunteer", "cause", "mission", "impact", "community", "fundraise", "campaign", "awareness", "advocacy", "nonprofit", "foundation", "grant", "sponsor"],
            "dependencies": ["stripe", "paypal", "donorbox", "classy", "benevity", "givebutter"],
            "colors": ["#E53E3E", "#38A169", "#3182CE", "#D69E2E", "#805AD5", "#319795"],
            "design": {
                "color_palette": ["#FFFFFF", "#E53E3E", "#38A169", "#F7FAFC", "#2D3748"],
                "typography": {"heading": "Poppins", "body": "Open Sans", "mono": "Roboto Mono"},
                "spacing_scale": "comfortable",
                "border_radius": "medium",
                "shadow_style": "soft",
                "animation_style": "heartfelt",
                "layout_pattern": "story-focused",
                "imagery_style": "impact-photography",
                "cta_style": "prominent",
                "form_style": "trust-building"
            },
            "competitors": ["GoFundMe", "Donorbox", "GlobalGiving", "Charity: Water"],
            "user_expectations": ["Transparency", "Impact stories", "Easy donation", "Tax receipts"],
            "conversion_goals": ["Donate", "Volunteer", "Share"],
            "accessibility_priority": "high",
            "mobile_importance": "high"
        },
        
        "portfolio_personal": {
            "keywords": ["portfolio", "resume", "cv", "bio", "about", "work", "project", "skill", "experience", "education", "contact", "blog", "personal", "developer", "designer", "creative"],
            "dependencies": ["gatsby", "next", "astro", "sveltekit", "contentful", "sanity", "prismic"],
            "colors": ["#000000", "#FFFFFF", "#6366F1", "#8B5CF6", "#EC4899", "#10B981"],
            "design": {
                "color_palette": ["#0A0A0A", "#FFFFFF", "#6366F1", "#F5F5F5", "#1A1A1A"],
                "typography": {"heading": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
                "spacing_scale": "balanced",
                "border_radius": "medium",
                "shadow_style": "modern",
                "animation_style": "smooth",
                "layout_pattern": "showcase",
                "imagery_style": "project-screenshots",
                "cta_style": "minimal",
                "form_style": "clean"
            },
            "competitors": ["Behance", "Dribbble", "GitHub Pages", "Personal sites"],
            "user_expectations": ["Fast loading", "Project details", "Contact info", "Social links"],
            "conversion_goals": ["Contact", "View project", "Download CV"],
            "accessibility_priority": "medium",
            "mobile_importance": "high"
        }
    }
    
    def __init__(self, memory_client: Optional[Any] = None):
        self.memory = memory_client
    
    def detect(
        self,
        scan_result: Any,
        additional_context: Optional[Dict] = None
    ) -> NicheProfile:
        """
        Detect niche from scan result.
        
        Args:
            scan_result: RepositoryScanner result
            additional_context: Additional context (description, readme, etc.)
            
        Returns:
            NicheProfile with design recommendations
        """
        signals = {}
        keyword_matches = {}
        
        # Analyze code content
        code_signals = self._analyze_code_content(scan_result)
        signals["code"] = code_signals
        keyword_matches["code"] = self._extract_keywords(code_signals)
        
        # Analyze dependencies
        dep_signals = self._analyze_dependencies(scan_result)
        signals["dependencies"] = dep_signals
        keyword_matches["dependencies"] = self._extract_keywords(dep_signals)
        
        # Analyze SVG colors
        color_signals = self._analyze_colors(scan_result)
        signals["colors"] = color_signals
        
        # Analyze frameworks
        framework_signals = self._analyze_frameworks(scan_result)
        signals["frameworks"] = framework_signals
        keyword_matches["frameworks"] = self._extract_keywords(framework_signals)
        
        # Combine signals
        combined_signals = self._combine_signals(signals, keyword_matches)
        
        # Determine niche
        niche_type, confidence = self._determine_niche(combined_signals)
        
        # Get niche profile
        niche_data = self.NICHES.get(niche_type, self.NICHES["saas"])
        
        # Create design direction
        design_direction = DesignDirection(
            color_palette=niche_data["design"]["color_palette"],
            typography=niche_data["design"]["typography"],
            spacing_scale=niche_data["design"]["spacing_scale"],
            border_radius=niche_data["design"]["border_radius"],
            shadow_style=niche_data["design"]["shadow_style"],
            animation_style=niche_data["design"]["animation_style"],
            layout_pattern=niche_data["design"]["layout_pattern"],
            imagery_style=niche_data["design"]["imagery_style"],
            cta_style=niche_data["design"]["cta_style"],
            form_style=niche_data["design"]["form_style"]
        )
        
        # Extract keywords from all sources
        all_keywords = list(set(
            keyword_matches.get("code", []) +
            keyword_matches.get("dependencies", []) +
            keyword_matches.get("frameworks", [])
        ))[:20]
        
        return NicheProfile(
            niche_type=niche_type,
            confidence=confidence,
            signals=signals,
            keywords=all_keywords,
            competitors=niche_data.get("competitors", []),
            design_direction=design_direction,
            user_expectations=niche_data.get("user_expectations", []),
            conversion_goals=niche_data.get("conversion_goals", []),
            accessibility_priority=niche_data.get("accessibility_priority", "medium"),
            mobile_importance=niche_data.get("mobile_importance", "medium")
        )
    
    def _analyze_code_content(self, scan_result: Any) -> Dict[str, float]:
        """Analyze code content for niche signals"""
        signals = {}
        
        # Get source files
        source_files = [
            f for f in scan_result.files
            if f.extension in [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".rb", ".php"]
            and not f.is_generated
        ][:50]  # Sample first 50 files
        
        # Read content and count keyword matches
        for niche_name, niche_data in self.NICHES.items():
            score = 0.0
            keywords = niche_data.get("keywords", [])
            
            for file_info in source_files:
                try:
                    with open(file_info.path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().lower()
                    
                    for keyword in keywords:
                        if keyword.lower() in content:
                            score += 1.0
                except Exception:
                    continue
            
            signals[niche_name] = score
        
        return signals
    
    def _analyze_dependencies(self, scan_result: Any) -> Dict[str, float]:
        """Analyze dependencies for niche signals"""
        signals = {}
        
        # Collect all dependencies
        all_deps = []
        for dep_info in scan_result.dependencies:
            for dep in dep_info.dependencies:
                all_deps.append(dep.get("name", "").lower())
        
        # Match against niche dependencies
        for niche_name, niche_data in self.NICHES.items():
            niche_deps = [d.lower() for d in niche_data.get("dependencies", [])]
            score = sum(1.0 for dep in all_deps if dep in niche_deps)
            signals[niche_name] = score
        
        return signals
    
    def _analyze_colors(self, scan_result: Any) -> Dict[str, float]:
        """Analyze SVG colors for niche signals"""
        signals = {}
        
        # Collect all colors from SVGs
        all_colors = []
        for svg in scan_result.svg_assets:
            all_colors.extend(svg.colors)
        
        # Normalize colors
        normalized_colors = set()
        for color in all_colors:
            # Normalize to uppercase hex
            if color.startswith("#"):
                normalized_colors.add(color.upper()[:7])
        
        # Match against niche colors
        for niche_name, niche_data in self.NICHES.items():
            niche_colors = set(c.upper()[:7] for c in niche_data.get("colors", []) if c.startswith("#"))
            overlap = len(normalized_colors & niche_colors)
            signals[niche_name] = float(overlap)
        
        return signals
    
    def _analyze_frameworks(self, scan_result: Any) -> Dict[str, float]:
        """Analyze frameworks for niche signals"""
        signals = {}
        
        detected_frameworks = set(f.lower() for f in scan_result.frameworks)
        
        # Map frameworks to niches
        framework_niche_map = {
            "django": ["saas", "ecommerce", "education"],
            "flask": ["saas", "developer_tools", "ai_ml"],
            "fastapi": ["ai_ml", "developer_tools", "saas"],
            "react": ["saas", "ecommerce", "social_media", "portfolio_personal"],
            "nextjs": ["saas", "ecommerce", "portfolio_personal", "education"],
            "vue": ["saas", "ecommerce", "education"],
            "angular": ["saas", "healthcare", "enterprise"],
            "express": ["saas", "social_media", "developer_tools"],
            "spring": ["healthcare", "legal", "enterprise"],
            "rails": ["saas", "ecommerce", "education"],
        }
        
        for framework in detected_frameworks:
            related_niches = framework_niche_map.get(framework, [])
            for niche in related_niches:
                signals[niche] = signals.get(niche, 0) + 1.0
        
        return signals
    
    def _extract_keywords(self, signals: Dict[str, float]) -> List[str]:
        """Extract top keywords from signals"""
        # Return niches with non-zero scores
        return [niche for niche, score in signals.items() if score > 0]
    
    def _combine_signals(
        self,
        signals: Dict[str, Dict[str, float]],
        keyword_matches: Dict[str, List[str]]
    ) -> Dict[str, float]:
        """Combine all signals into final scores"""
        combined = {}
        
        # Weight factors
        weights = {
            "code": 1.0,
            "dependencies": 2.0,  # Higher weight for dependencies
            "colors": 0.5,
            "frameworks": 1.5
        }
        
        for signal_type, signal_data in signals.items():
            weight = weights.get(signal_type, 1.0)
            
            for niche, score in signal_data.items():
                combined[niche] = combined.get(niche, 0) + (score * weight)
        
        return combined
    
    def _determine_niche(self, combined_signals: Dict[str, float]) -> Tuple[str, float]:
        """Determine the most likely niche"""
        if not combined_signals:
            return "saas", 0.5  # Default to SaaS
        
        # Find niche with highest score
        sorted_niches = sorted(combined_signals.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_niches:
            return "saas", 0.5
        
        top_niche, top_score = sorted_niches[0]
        
        # Calculate confidence (normalized)
        total_score = sum(combined_signals.values())
        confidence = min(0.95, top_score / max(total_score, 1) + 0.3) if total_score > 0 else 0.5
        
        return top_niche, confidence
    
    def get_design_tokens(self, niche_type: str) -> Dict[str, Any]:
        """Get design tokens for a specific niche"""
        niche_data = self.NICHES.get(niche_type, self.NICHES["saas"])
        return niche_data.get("design", {})
    
    def get_competitors(self, niche_type: str) -> List[str]:
        """Get competitor list for a niche"""
        niche_data = self.NICHES.get(niche_type, self.NICHES["saas"])
        return niche_data.get("competitors", [])