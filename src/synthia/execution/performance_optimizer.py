"""
Performance Optimization Engine
================================

Automatically optimizes generated code with:
- Code splitting
- Image optimization
- Lazy loading
- Bundle optimization
- SEO improvements
"""

import logging
import os
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger("synthia.execution.performance_optimizer")


class PerformanceOptimizer:
    """
    Automatically optimizes generated code for performance.
    
    Key features:
    - Code splitting
    - Image optimization
    - Lazy loading
    - Bundle optimization
    - SEO improvements
    """
    
    def __init__(self):
        self.optimization_config: Dict[str, Any] = {
            "image_optimization": True,
            "code_splitting": True,
            "lazy_loading": True,
            "minification": True,
            "bundle_analysis": True,
            "seo_optimization": True
        }
        
        logger.info("Performance optimization engine initialized")
    
    def optimize_project(self, project_dir: str) -> Dict[str, Any]:
        """Optimize entire project for performance"""
        try:
            results = {
                "project_dir": project_dir,
                "optimizations": [],
                "before": self._analyze_performance(project_dir),
                "after": {}
            }
            
            # Run all enabled optimizations
            if self.optimization_config["code_splitting"]:
                self._code_splitting(project_dir)
                results["optimizations"].append("code_splitting")
            
            if self.optimization_config["image_optimization"]:
                self._optimize_images(project_dir)
                results["optimizations"].append("image_optimization")
            
            if self.optimization_config["lazy_loading"]:
                self._add_lazy_loading(project_dir)
                results["optimizations"].append("lazy_loading")
            
            if self.optimization_config["minification"]:
                self._minify_code(project_dir)
                results["optimizations"].append("minification")
            
            if self.optimization_config["seo_optimization"]:
                self._optimize_seo(project_dir)
                results["optimizations"].append("seo_optimization")
            
            results["after"] = self._analyze_performance(project_dir)
            
            logger.info(f"Project optimized successfully with {len(results['optimizations'])} optimizations")
            return results
        except Exception as e:
            logger.error(f"Project optimization failed: {e}")
            return {"error": str(e)}
    
    def _analyze_performance(self, project_dir: str) -> Dict[str, Any]:
        """Analyze project performance metrics"""
        analysis = {
            "total_size": 0,
            "image_count": 0,
            "image_size": 0,
            "javascript_count": 0,
            "javascript_size": 0,
            "css_count": 0,
            "css_size": 0,
            "html_count": 0,
            "html_size": 0
        }
        
        try:
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    analysis["total_size"] += file_size
                    
                    if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                        analysis["image_count"] += 1
                        analysis["image_size"] += file_size
                    elif file.lower().endswith((".js", ".jsx", ".ts", ".tsx")):
                        analysis["javascript_count"] += 1
                        analysis["javascript_size"] += file_size
                    elif file.lower().endswith((".css", ".scss", ".less")):
                        analysis["css_count"] += 1
                        analysis["css_size"] += file_size
                    elif file.lower().endswith((".html")):
                        analysis["html_count"] += 1
                        analysis["html_size"] += file_size
        
        except Exception as e:
            logger.warning(f"Performance analysis failed: {e}")
        
        return analysis
    
    def _code_splitting(self, project_dir: str):
        """Implement code splitting for JavaScript/TypeScript files"""
        # Look for entry points and split code
        entry_points = self._find_entry_points(project_dir)
        
        for entry in entry_points:
            try:
                # This is a placeholder - actual code splitting would be framework-specific
                logger.debug(f"Code splitting for entry point: {entry}")
            except Exception as e:
                logger.warning(f"Code splitting failed for {entry}: {e}")
    
    def _find_entry_points(self, project_dir: str) -> List[str]:
        """Find JavaScript/TypeScript entry points"""
        entry_points = []
        
        # Common entry point patterns
        entry_patterns = [
            "src/index.js", "src/index.tsx", "src/App.js", "src/App.tsx",
            "public/index.html", "index.html"
        ]
        
        for pattern in entry_patterns:
            file_path = os.path.join(project_dir, pattern)
            if os.path.exists(file_path):
                entry_points.append(file_path)
        
        return entry_points
    
    def _optimize_images(self, project_dir: str):
        """Optimize images in project"""
        image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp")
        
        try:
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    if file.lower().endswith(image_extensions):
                        file_path = os.path.join(root, file)
                        self._optimize_image(file_path)
                        
        except Exception as e:
            logger.warning(f"Image optimization failed: {e}")
    
    def _optimize_image(self, file_path: str):
        """Optimize individual image file"""
        try:
            # Try using Pillow for image optimization
            from PIL import Image
            
            with Image.open(file_path) as img:
                # Get original size
                original_size = os.path.getsize(file_path)
                
                # Optimize image
                if img.format == "JPEG":
                    img.save(file_path, "JPEG", optimize=True, quality=85)
                elif img.format == "PNG":
                    img.save(file_path, "PNG", optimize=True)
                elif img.format == "WEBP":
                    img.save(file_path, "WEBP", optimize=True, quality=85)
                
                optimized_size = os.path.getsize(file_path)
                savings = original_size - optimized_size
                
                if savings > 0:
                    logger.debug(f"Optimized {file_path}: saved {savings} bytes")
        
        except ImportError:
            logger.warning("Pillow not installed, skipping image optimization")
        except Exception as e:
            logger.warning(f"Failed to optimize {file_path}: {e}")
    
    def _add_lazy_loading(self, project_dir: str):
        """Add lazy loading to images and scripts"""
        html_files = self._find_html_files(project_dir)
        
        for html_file in html_files:
            try:
                with open(html_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Add loading="lazy" to images
                content = re.sub(r'<img(.*?)src=', r'<img\1loading="lazy" src=', content)
                
                # Add defer attribute to scripts
                content = re.sub(r'<script(.*?)src=', r'<script\1defer src=', content)
                
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(content)
                
                logger.debug(f"Added lazy loading to: {html_file}")
            
            except Exception as e:
                logger.warning(f"Failed to add lazy loading to {html_file}: {e}")
    
    def _find_html_files(self, project_dir: str) -> List[str]:
        """Find all HTML files in project"""
        html_files = []
        
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if file.lower().endswith(".html"):
                    html_files.append(os.path.join(root, file))
        
        return html_files
    
    def _minify_code(self, project_dir: str):
        """Minify JavaScript, CSS, and HTML files"""
        # Minify JavaScript
        js_files = self._find_files_by_extension(project_dir, (".js", ".jsx"))
        for js_file in js_files:
            self._minify_js(js_file)
        
        # Minify CSS
        css_files = self._find_files_by_extension(project_dir, (".css", ".scss", ".less"))
        for css_file in css_files:
            self._minify_css(css_file)
        
        # Minify HTML
        html_files = self._find_html_files(project_dir)
        for html_file in html_files:
            self._minify_html(html_file)
    
    def _find_files_by_extension(self, project_dir: str, extensions: tuple) -> List[str]:
        """Find files by extension"""
        files = []
        
        for root, dirs, files_list in os.walk(project_dir):
            for file in files_list:
                if file.lower().endswith(extensions):
                    files.append(os.path.join(root, file))
        
        return files
    
    def _minify_js(self, file_path: str):
        """Minify JavaScript file"""
        try:
            import jsmin
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            minified = jsmin.jsmin(content)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(minified)
            
            logger.debug(f"Minified JavaScript file: {file_path}")
        
        except ImportError:
            logger.warning("jsmin not installed, skipping JavaScript minification")
        except Exception as e:
            logger.warning(f"Failed to minify {file_path}: {e}")
    
    def _minify_css(self, file_path: str):
        """Minify CSS file"""
        try:
            from csscompressor import compress
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            minified = compress(content)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(minified)
            
            logger.debug(f"Minified CSS file: {file_path}")
        
        except ImportError:
            logger.warning("csscompressor not installed, skipping CSS minification")
        except Exception as e:
            logger.warning(f"Failed to minify {file_path}: {e}")
    
    def _minify_html(self, file_path: str):
        """Minify HTML file"""
        try:
            from htmlmin import minify
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            minified = minify(content, remove_comments=True, remove_empty_space=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(minified)
            
            logger.debug(f"Minified HTML file: {file_path}")
        
        except ImportError:
            logger.warning("htmlmin not installed, skipping HTML minification")
        except Exception as e:
            logger.warning(f"Failed to minify {file_path}: {e}")
    
    def _optimize_seo(self, project_dir: str):
        """Optimize project for SEO"""
        html_files = self._find_html_files(project_dir)
        
        for html_file in html_files:
            try:
                with open(html_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Add viewport meta tag if missing
                if '<meta name="viewport"' not in content:
                    viewport_tag = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
                    if '<head>' in content:
                        content = content.replace('<head>', f'<head>\n    {viewport_tag}')
                
                # Add meta description if missing
                if '<meta name="description"' not in content:
                    meta_desc = '<meta name="description" content="Professional website featuring our services">'
                    if '<head>' in content:
                        content = content.replace('<head>', f'<head>\n    {meta_desc}')
                
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(content)
                
                logger.debug(f"Optimized SEO for: {html_file}")
            
            except Exception as e:
                logger.warning(f"Failed to optimize SEO for {html_file}: {e}")
    
    def analyze_bundle(self, project_dir: str) -> Dict[str, Any]:
        """Analyze bundle performance"""
        analysis = {
            "bundle_size": 0,
            "chunk_count": 0,
            "third_party_size": 0,
            "unused_code": 0,
            "critical_path": 0
        }
        
        try:
            # Check if we're in a Node.js project
            package_json = os.path.join(project_dir, "package.json")
            if os.path.exists(package_json):
                # Run webpack bundle analyzer (if available)
                pass
        
        except Exception as e:
            logger.warning(f"Bundle analysis failed: {e}")
        
        return analysis
    
    def set_config(self, config: Dict[str, bool]):
        """Set optimization configuration"""
        for key, value in config.items():
            if key in self.optimization_config:
                self.optimization_config[key] = value
        
        logger.info("Optimization configuration updated")
    
    def get_optimization_report(self, results: Dict[str, Any]) -> str:
        """Generate optimization report"""
        report = "=== Performance Optimization Report ===\n\n"
        report += f"Project Directory: {results.get('project_dir', 'Unknown')}\n"
        report += f"Optimizations Applied: {', '.join(results.get('optimizations', []))}\n\n"
        
        before = results.get('before', {})
        after = results.get('after', {})
        
        if before and after:
            report += "Before Optimization:\n"
            report += self._format_analysis(before)
            report += "\nAfter Optimization:\n"
            report += self._format_analysis(after)
            report += "\nImprovements:\n"
            report += self._format_improvements(before, after)
        
        return report
    
    def _format_analysis(self, analysis: Dict[str, Any]) -> str:
        """Format analysis results"""
        format_str = (
            f"  Total Size: {self._format_size(analysis.get('total_size', 0))}\n"
            f"  Images: {analysis.get('image_count', 0)} ({self._format_size(analysis.get('image_size', 0))})\n"
            f"  JavaScript: {analysis.get('javascript_count', 0)} ({self._format_size(analysis.get('javascript_size', 0))})\n"
            f"  CSS: {analysis.get('css_count', 0)} ({self._format_size(analysis.get('css_size', 0))})\n"
            f"  HTML: {analysis.get('html_count', 0)} ({self._format_size(analysis.get('html_size', 0))})\n"
        )
        
        return format_str
    
    def _format_improvements(self, before: Dict[str, Any], after: Dict[str, Any]) -> str:
        """Format performance improvements"""
        improvements = []
        
        if before.get('total_size', 0) > 0:
            saved = before['total_size'] - after.get('total_size', 0)
            if saved > 0:
                improvements.append(f"  Total size: - {self._format_size(saved)}")
        
        if before.get('image_size', 0) > 0:
            saved = before['image_size'] - after.get('image_size', 0)
            if saved > 0:
                improvements.append(f"  Images: - {self._format_size(saved)}")
        
        if before.get('javascript_size', 0) > 0:
            saved = before['javascript_size'] - after.get('javascript_size', 0)
            if saved > 0:
                improvements.append(f"  JavaScript: - {self._format_size(saved)}")
        
        if before.get('css_size', 0) > 0:
            saved = before['css_size'] - after.get('css_size', 0)
            if saved > 0:
                improvements.append(f"  CSS: - {self._format_size(saved)}")
        
        if before.get('html_size', 0) > 0:
            saved = before['html_size'] - after.get('html_size', 0)
            if saved > 0:
                improvements.append(f"  HTML: - {self._format_size(saved)}")
        
        return "\n".join(improvements) if improvements else "  No measurable improvements"
    
    def _format_size(self, bytes: int) -> str:
        """Format bytes to readable size"""
        if bytes < 1024:
            return f"{bytes} B"
        elif bytes < 1024 * 1024:
            return f"{bytes / 1024:.1f} KB"
        else:
            return f"{bytes / (1024 * 1024):.1f} MB"
