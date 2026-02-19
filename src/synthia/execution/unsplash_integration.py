"""
Unsplash API Integration
========================

Integrates Unsplash API for professional imagery.
Features:
- Image search by keywords
- Category-based image retrieval
- Image metadata extraction
- Rate limiting and caching
"""

import logging
import requests
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("synthia.execution.unsplash_integration")


class UnsplashAPI:
    """
    Integration with Unsplash API for professional imagery.
    
    Key features:
    - Image search by keywords
    - Category-based image retrieval
    - Image metadata extraction
    - Rate limiting and caching
    """
    
    BASE_URL = "https://api.unsplash.com"
    CLIENT_ID = "YOUR_UNSPLASH_ACCESS_KEY"  # Should be configured
    
    RATE_LIMIT = 50  # Requests per hour
    RATE_RESET_TIME = 3600  # Seconds
    
    def __init__(self, access_key: Optional[str] = None):
        if access_key:
            self.CLIENT_ID = access_key
        
        self.request_count = 0
        self.last_reset_time = time.time()
        self.cache: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("Unsplash API integration initialized")
    
    def _check_rate_limit(self) -> bool:
        """Check if rate limit has been exceeded"""
        current_time = time.time()
        
        # Reset rate limit if reset time has passed
        if current_time - self.last_reset_time >= self.RATE_RESET_TIME:
            self.request_count = 0
            self.last_reset_time = current_time
        
        if self.request_count >= self.RATE_LIMIT:
            logger.warning("Unsplash API rate limit exceeded")
            return False
        
        return True
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make HTTP request to Unsplash API with rate limiting"""
        if not self._check_rate_limit():
            return None
        
        headers = {
            "Accept": "application/json",
            "Authorization": f"Client-ID {self.CLIENT_ID}"
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}{endpoint}",
                headers=headers,
                params=params,
                timeout=10
            )
            
            self.request_count += 1
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                logger.error("Unsplash API access forbidden")
            elif response.status_code == 404:
                logger.warning("Unsplash API resource not found")
            else:
                logger.error(f"Unsplash API error: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Unsplash API request failed: {e}")
        
        return None
    
    def search_images(self, query: str, per_page: int = 10) -> List[str]:
        """Search for images by keyword"""
        cache_key = f"search:{query}:{per_page}"
        
        if cache_key in self.cache:
            logger.debug(f"Cache hit for: {cache_key}")
            return self.cache[cache_key]
        
        logger.debug(f"Searching Unsplash for: {query}")
        
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": "landscape"
        }
        
        data = self._make_request("/search/photos", params)
        
        if data and "results" in data:
            images = []
            for result in data["results"]:
                if "urls" in result and "regular" in result["urls"]:
                    images.append(result["urls"]["regular"])
            
            self.cache[cache_key] = images
            logger.debug(f"Found {len(images)} images for: {query}")
            return images
        
        logger.warning(f"No images found for query: {query}")
        return self._get_fallback_images()
    
    def get_category_images(self, category: str, per_page: int = 10) -> List[str]:
        """Get images from specific category"""
        logger.debug(f"Getting {per_page} images from category: {category}")
        
        # Map category to Unsplash search query
        category_map = {
            "technology": "technology digital coding",
            "business": "business office professional",
            "healthcare": "healthcare medical hospital",
            "education": "education learning school",
            "nature": "nature landscape outdoors",
            "food": "food cooking restaurant",
            "travel": "travel adventure vacation",
            "fashion": "fashion clothing style",
            "art": "art design creative",
            "abstract": "abstract modern art"
        }
        
        query = category_map.get(category.lower(), category)
        return self.search_images(query, per_page)
    
    def get_image_metadata(self, image_url: str) -> Optional[Dict[str, Any]]:
        """Get metadata for specific image URL"""
        logger.debug(f"Getting metadata for image: {image_url}")
        
        # Extract image ID from URL if possible
        # Unsplash image URLs format: https://images.unsplash.com/photo-1234567890abcdef?w=1920&q=80
        import re
        match = re.search(r"photo-([\w-]+)", image_url)
        
        if match:
            image_id = match.group(1)
            data = self._make_request(f"/photos/{image_id}", {})
            
            if data:
                return {
                    "id": image_id,
                    "description": data.get("description", ""),
                    "user": data.get("user", {}).get("name", ""),
                    "username": data.get("user", {}).get("username", ""),
                    "likes": data.get("likes", 0),
                    "views": data.get("views", 0),
                    "downloads": data.get("downloads", 0),
                    "color": data.get("color", ""),
                    "tags": [tag["title"] for tag in data.get("tags", [])]
                }
        
        return None
    
    def download_image(self, image_url: str, save_path: str) -> bool:
        """Download image to local file"""
        logger.debug(f"Downloading image: {image_url}")
        
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            with open(save_path, "wb") as f:
                f.write(response.content)
            
            logger.debug(f"Image saved to: {save_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            return False
    
    def _get_fallback_images(self) -> List[str]:
        """Get fallback images if search fails"""
        fallback_images = [
            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1920&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1920&q=80",
            "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=1920&q=80",
            "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?w=1920&q=80"
        ]
        
        return fallback_images
    
    def clear_cache(self):
        """Clear image cache"""
        self.cache.clear()
        logger.debug("Unsplash API cache cleared")
    
    def set_access_key(self, access_key: str):
        """Set Unsplash API access key"""
        self.CLIENT_ID = access_key
        logger.info("Unsplash API access key updated")
    
    def get_request_count(self) -> int:
        """Get current API request count"""
        return self.request_count
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        remaining = max(0, self.RATE_LIMIT - self.request_count)
        reset_time = max(0, self.RATE_RESET_TIME - (time.time() - self.last_reset_time))
        
        return {
            "remaining": remaining,
            "limit": self.RATE_LIMIT,
            "reset_time_seconds": int(reset_time),
            "reset_time_minutes": int(reset_time / 60)
        }
    
    def get_random_images(self, count: int = 10, categories: Optional[List[str]] = None) -> List[str]:
        """Get random images"""
        if categories:
            # Get random images from specified categories
            images = []
            for category in categories:
                cat_images = self.get_category_images(category, count)
                images.extend(cat_images)
            
            # Randomly select unique images
            import random
            seen = set()
            unique_images = []
            
            for img in images:
                if img not in seen:
                    seen.add(img)
                    unique_images.append(img)
            
            return unique_images[:count]
        else:
            # Get completely random images
            logger.debug(f"Getting {count} random images")
            
            params = {
                "count": count,
                "orientation": "landscape"
            }
            
            data = self._make_request("/photos/random", params)
            
            if data:
                images = []
                for photo in data:
                    if "urls" in photo and "regular" in photo["urls"]:
                        images.append(photo["urls"]["regular"])
                
                return images
        
        return self._get_fallback_images()
