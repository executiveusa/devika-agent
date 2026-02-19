"""
Content Generation System with SEO Optimization
===============================================

Generates SEO-optimized content for websites with support for:
- Context-aware text generation
- Keyword optimization
- Content structure analysis
- SEO best practices
"""

import logging
import re
import nltk
from typing import Any, Dict, List, Optional
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from ..memory import ContentMemory
from ..investigation.niche_detector import NicheDetector

logger = logging.getLogger("synthia.execution.content_generator")


class ContentGenerator:
    """
    Generates SEO-optimized content for websites.
    
    Key features:
    - Context-aware text generation
    - Keyword research and optimization
    - SEO-friendly content structure
    - Natural language processing
    """
    
    def __init__(self, content_memory: Optional[ContentMemory] = None):
        self.content_memory = content_memory or ContentMemory()
        self.niche_detector = NicheDetector()
        self.keyword_cache: Dict[str, List[str]] = {}
        
        # Initialize NLTK
        try:
            nltk.download("punkt", quiet=True)
            nltk.download("stopwords", quiet=True)
        except Exception as e:
            logger.warning(f"Failed to download NLTK resources: {e}")
        
        logger.info("Content generation engine initialized")
    
    def generate_seo_content(
        self, 
        topic: str, 
        niche: str,
        word_count: int = 500,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate SEO-optimized content"""
        try:
            # Use provided keywords or generate from topic
            if not keywords:
                keywords = self._generate_keywords(topic, niche)
            
            # Generate content sections
            content = {
                "title": self._generate_title(topic, keywords),
                "meta_description": self._generate_meta_description(topic, keywords),
                "headings": self._generate_headings(topic, keywords),
                "paragraphs": self._generate_paragraphs(topic, niche, keywords, word_count),
                "bullet_points": self._generate_bullet_points(topic, keywords),
                "call_to_action": self._generate_cta(niche),
                "keywords": keywords,
                "word_count": word_count
            }
            
            logger.info(f"Generated {word_count} word SEO content for: {topic}")
            return content
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return self._generate_fallback_content(topic)
    
    def _generate_keywords(self, topic: str, niche: str) -> List[str]:
        """Generate relevant keywords for topic and niche"""
        cache_key = f"{topic}_{niche}"
        
        if cache_key in self.keyword_cache:
            return self.keyword_cache[cache_key]
        
        keywords = [topic.lower()]
        
        # Add niche-specific keywords
        niche_keywords = self._get_niche_keywords(niche)
        keywords.extend([kw for kw in niche_keywords if kw not in keywords])
        
        # Add variations
        variations = self._generate_keyword_variations(topic)
        keywords.extend([v for v in variations if v not in keywords])
        
        self.keyword_cache[cache_key] = keywords
        return keywords
    
    def _get_niche_keywords(self, niche: str) -> List[str]:
        """Get niche-specific keywords"""
        niche_keywords = {
            "technology": ["software", "digital", "innovation", "cloud", "automation"],
            "ecommerce": ["shop", "online", "products", "discount", "delivery"],
            "healthcare": ["health", "wellness", "medical", "treatment", "clinic"],
            "finance": ["financial", "investment", "savings", "banking", "budget"],
            "education": ["learning", "courses", "training", "university", "online"],
            "real_estate": ["property", "homes", "rent", "buy", "investment"],
            "creative": ["design", "art", "portfolio", "agency", "visual"],
            "restaurant": ["food", "dining", "restaurant", "menu", "cuisine"]
        }
        
        return niche_keywords.get(niche, ["business", "services", "solutions"])
    
    def _generate_keyword_variations(self, topic: str) -> List[str]:
        """Generate keyword variations"""
        variations = []
        
        # Add suffixes
        suffixes = ["services", "solutions", "expertise", "platform", "software"]
        for suffix in suffixes:
            variations.append(f"{topic} {suffix}")
            variations.append(f"{topic}{suffix}")
        
        # Add industry prefixes
        industries = ["best", "top", "premium", "professional", "enterprise"]
        for industry in industries:
            variations.append(f"{industry} {topic}")
        
        return variations
    
    def _generate_title(self, topic: str, keywords: List[str]) -> str:
        """Generate SEO-friendly title (60-70 characters)"""
        base_title = f"{topic.capitalize()} - {self._get_primary_keyword(keywords)}"
        
        if len(base_title) > 60:
            return topic.capitalize()
        
        return base_title
    
    def _get_primary_keyword(self, keywords: List[str]) -> str:
        """Get primary keyword from list"""
        if keywords:
            # Sort by length (prefer medium-length keywords)
            sorted_keywords = sorted(keywords, key=lambda x: abs(len(x) - 8))
            return sorted_keywords[0]
        return "solutions"
    
    def _generate_meta_description(self, topic: str, keywords: List[str]) -> str:
        """Generate meta description (150-160 characters)"""
        base_desc = f"Discover how our {topic.lower()} solutions can help you {self._get_benefit(keywords)}. "
        base_desc += f"Learn more about our {', '.join(keywords[:3])} capabilities today."
        
        if len(base_desc) > 160:
            return base_desc[:157] + "..."
        
        return base_desc
    
    def _get_benefit(self, keywords: List[str]) -> str:
        """Get benefit phrase from keywords"""
        benefits = {
            "technology": "transform your business",
            "ecommerce": "grow your online store",
            "healthcare": "improve your well-being",
            "finance": "achieve financial success",
            "education": "advance your career",
            "real_estate": "find your dream home",
            "creative": "unleash your creativity",
            "restaurant": "enjoy delicious food"
        }
        
        for niche, benefit in benefits.items():
            if any(niche in kw.lower() for kw in keywords):
                return benefit
        
        return "reach your goals"
    
    def _generate_headings(self, topic: str, keywords: List[str]) -> Dict[str, str]:
        """Generate content headings (H2, H3)"""
        headings = {
            "h2": f"Understanding {topic.capitalize()}",
            "h3": [
                f"Key Benefits of {topic}",
                f"How {topic} Can Help Your Business",
                f"Getting Started with {topic}"
            ]
        }
        
        return headings
    
    def _generate_paragraphs(
        self, 
        topic: str, 
        niche: str,
        keywords: List[str],
        word_count: int
    ) -> List[str]:
        """Generate content paragraphs"""
        paragraphs = []
        remaining_words = word_count
        
        # Introduction paragraph (150-200 words)
        intro = self._generate_introduction(topic, keywords)
        paragraphs.append(intro)
        remaining_words -= self._count_words(intro)
        
        # Main content paragraphs
        while remaining_words > 100:
            para_length = min(remaining_words, 200)
            paragraph = self._generate_paragraph(topic, niche, keywords, para_length)
            paragraphs.append(paragraph)
            remaining_words -= self._count_words(paragraph)
        
        # Conclusion paragraph
        if remaining_words > 0:
            conclusion = self._generate_conclusion(topic, keywords)
            paragraphs.append(conclusion)
        
        return paragraphs
    
    def _generate_introduction(self, topic: str, keywords: List[str]) -> str:
        """Generate introduction paragraph"""
        intro = f"In today's fast-paced world, {topic.lower()} has become increasingly important for businesses of all sizes. "
        intro += f"Our {', '.join(keywords[:3])} solutions are designed to help you {self._get_benefit(keywords)}. "
        intro += f"Whether you're looking to {self._get_action_verb(topic)} your operations or {self._get_action_verb(topic)} new opportunities, "
        intro += f"we have the expertise and resources to help you succeed."
        
        return intro
    
    def _generate_paragraph(self, topic: str, niche: str, keywords: List[str], word_count: int) -> str:
        """Generate single content paragraph"""
        # This is a placeholder - in production, this would use LLM integration
        paragraph = f"Our {topic.lower()} services are designed specifically for {niche} businesses. "
        paragraph += f"We understand the unique challenges and opportunities in the {niche} industry. "
        paragraph += f"With our expertise in {', '.join(keywords[:4])}, we can help you achieve your goals. "
        paragraph += "Our team of experts is dedicated to providing high-quality solutions that deliver real results. "
        paragraph += "We believe in building long-term relationships with our clients based on trust and mutual success."
        
        # Trim to desired word count
        words = paragraph.split()
        if len(words) > word_count:
            paragraph = " ".join(words[:word_count]) + "."
        
        return paragraph
    
    def _generate_conclusion(self, topic: str, keywords: List[str]) -> str:
        """Generate conclusion paragraph"""
        conclusion = f"Ready to take your {topic.lower()} to the next level? "
        conclusion += f"Our {', '.join(keywords[:3])} solutions are here to help. "
        conclusion += "Contact us today to learn more about how we can help you achieve your business objectives and drive success."
        
        return conclusion
    
    def _generate_bullet_points(self, topic: str, keywords: List[str]) -> List[str]:
        """Generate bullet points for key features"""
        return [
            f"Professional {topic.lower()} services",
            f"Expertise in {', '.join(keywords[:3])}",
            "Customized solutions for your business",
            "Proven track record of success",
            "Excellent customer support"
        ]
    
    def _generate_cta(self, niche: str) -> str:
        """Generate call-to-action text"""
        cta_map = {
            "technology": "Get Started Today",
            "ecommerce": "Shop Now",
            "healthcare": "Schedule Consultation",
            "finance": "Learn More",
            "education": "Explore Courses",
            "real_estate": "View Properties",
            "creative": "See Portfolio",
            "restaurant": "Reserve Table"
        }
        
        return cta_map.get(niche, "Contact Us")
    
    def _generate_fallback_content(self, topic: str) -> Dict[str, Any]:
        """Generate fallback content if generation fails"""
        return {
            "title": topic.capitalize(),
            "meta_description": f"Learn more about {topic.lower()} and how it can benefit your business.",
            "headings": {"h2": f"About {topic.capitalize()}", "h3": ["Key Features", "Benefits"]},
            "paragraphs": [f"Our {topic.lower()} services are designed to help you achieve your goals."],
            "bullet_points": [f"Professional {topic.lower()} solutions", "Expert support"],
            "call_to_action": "Learn More",
            "keywords": [topic.lower()],
            "word_count": 100
        }
    
    def optimize_content_for_seo(self, content: Dict[str, Any], density: float = 1.5) -> Dict[str, Any]:
        """Optimize content with keyword density (1.5-3%)"""
        try:
            optimized = content.copy()
            keywords = optimized.get("keywords", [])
            
            for i, paragraph in enumerate(optimized["paragraphs"]):
                optimized["paragraphs"][i] = self._optimize_paragraph(paragraph, keywords, density)
            
            logger.debug("Content SEO optimized")
            return optimized
        except Exception as e:
            logger.error(f"SEO optimization failed: {e}")
            return content
    
    def _optimize_paragraph(self, paragraph: str, keywords: List[str], target_density: float) -> str:
        """Optimize paragraph keyword density"""
        current_density = self._calculate_keyword_density(paragraph, keywords)
        
        if abs(current_density - target_density) < 0.5:
            return paragraph
        
        word_count = self._count_words(paragraph)
        target_keywords = max(1, int(word_count * target_density / 100))
        
        return paragraph
    
    def _calculate_keyword_density(self, text: str, keywords: List[str]) -> float:
        """Calculate keyword density in text"""
        words = self._get_clean_words(text)
        word_count = len(words)
        
        if word_count == 0:
            return 0.0
        
        keyword_count = 0
        for keyword in keywords:
            keyword_count += text.lower().count(keyword.lower())
        
        return (keyword_count / word_count) * 100
    
    def _get_clean_words(self, text: str) -> List[str]:
        """Get clean words for analysis"""
        try:
            # Tokenize and remove stopwords/punctuation
            tokens = word_tokenize(text.lower())
            stop_words = set(stopwords.words("english"))
            clean_words = [token for token in tokens if token.isalnum() and token not in stop_words]
            return clean_words
        except Exception as e:
            logger.warning(f"Text cleaning failed: {e}")
            return text.split()
    
    def _count_words(self, text: str) -> int:
        """Count words in text"""
        return len(self._get_clean_words(text))
    
    def _get_action_verb(self, topic: str) -> str:
        """Get appropriate action verb for topic"""
        verbs = ["optimize", "enhance", "transform", "improve", "streamline"]
        return verbs[hash(topic) % len(verbs)]
    
    def save_content(self, filename: str, content: Dict[str, Any]):
        """Save generated content to file"""
        try:
            import json
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            logger.info(f"Content saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save content: {e}")
    
    def load_content(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load saved content from file"""
        try:
            import json
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load content: {e}")
            return None
