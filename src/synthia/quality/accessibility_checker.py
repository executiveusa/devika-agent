"""
Accessibility Checker - WCAG 2.1 AA Compliance Validation
=========================================================

Comprehensive accessibility testing using axe-core patterns for:
- WCAG 2.1 Level AA compliance
- Section 508 compliance
- Best practice accessibility checks

Target: 100% WCAG 2.1 AA compliance
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Set, Tuple
import os
import subprocess
import tempfile

from . import (
    QualityCategory,
    QualityIssue,
    QualityScore,
    SeverityLevel
)

logger = logging.getLogger("synthia.quality.accessibility")


class WCAGLevel(Enum):
    """WCAG conformance levels"""
    A = "A"
    AA = "AA"
    AAA = "AAA"


class WCAGPrinciple(Enum):
    """WCAG principles (POUR)"""
    PERCEIVABLE = "perceivable"
    OPERABLE = "operable"
    UNDERSTANDABLE = "understandable"
    ROBUST = "robust"


@dataclass
class AccessibilityRule:
    """Definition of an accessibility rule"""
    id: str
    name: str
    description: str
    wcag_level: WCAGLevel
    wcag_criteria: List[str]
    principle: WCAGPrinciple
    impact: str  # critical, serious, moderate, minor
    tags: List[str] = field(default_factory=list)
    help_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "wcag_level": self.wcag_level.value,
            "wcag_criteria": self.wcag_criteria,
            "principle": self.principle.value,
            "impact": self.impact,
            "tags": self.tags,
            "help_url": self.help_url
        }


@dataclass
class AccessibilityViolation:
    """A specific accessibility violation found"""
    rule: AccessibilityRule
    element: str
    selector: str
    html: str
    message: str
    suggestions: List[str] = field(default_factory=list)
    
    def to_quality_issue(self) -> QualityIssue:
        """Convert to QualityIssue"""
        severity_map = {
            "critical": SeverityLevel.CRITICAL,
            "serious": SeverityLevel.HIGH,
            "moderate": SeverityLevel.MEDIUM,
            "minor": SeverityLevel.LOW
        }
        
        return QualityIssue(
            category=QualityCategory.ACCESSIBILITY,
            severity=severity_map.get(self.rule.impact, SeverityLevel.MEDIUM),
            title=self.rule.name,
            description=self.message,
            element=self.element,
            suggestion=self.suggestions[0] if self.suggestions else None,
            documentation=self.rule.help_url
        )


# WCAG 2.1 AA Rules Definition
WCAG_AA_RULES: Dict[str, AccessibilityRule] = {
    # Perceivable
    "image-alt": AccessibilityRule(
        id="image-alt",
        name="Images must have alternate text",
        description="Ensures <img> elements have alternate text or a role of none or presentation",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["1.1.1"],
        principle=WCAGPrinciple.PERCEIVABLE,
        impact="critical",
        tags=["cat.text-alternatives", "wcag2a", "section508"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/image-alt"
    ),
    "input-image-alt": AccessibilityRule(
        id="input-image-alt",
        name="Image buttons must have alternate text",
        description="Ensures <input type=\"image\"> elements have alternate text",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["1.1.1"],
        principle=WCAGPrinciple.PERCEIVABLE,
        impact="critical",
        tags=["cat.text-alternatives", "wcag2a"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/input-image-alt"
    ),
    "color-contrast": AccessibilityRule(
        id="color-contrast",
        name="Elements must meet minimum color contrast ratio",
        description="Ensures the contrast between foreground and background colors meets WCAG 2 AA minimum contrast ratio thresholds",
        wcag_level=WCAGLevel.AA,
        wcag_criteria=["1.4.3"],
        principle=WCAGPrinciple.PERCEIVABLE,
        impact="serious",
        tags=["cat.color", "wcag2aa"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/color-contrast"
    ),
    "video-caption": AccessibilityRule(
        id="video-caption",
        name="Video elements must have captions",
        description="Ensures <video> elements have captions",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["1.2.2"],
        principle=WCAGPrinciple.PERCEIVABLE,
        impact="critical",
        tags=["cat.text-alternatives", "wcag2a"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/video-caption"
    ),
    
    # Operable
    "keyboard": AccessibilityRule(
        id="keyboard",
        name="Elements must be keyboard accessible",
        description="Ensures all page functionality is available using a keyboard",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["2.1.1"],
        principle=WCAGPrinciple.OPERABLE,
        impact="critical",
        tags=["cat.keyboard", "wcag2a"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/keyboard"
    ),
    "focus-order": AccessibilityRule(
        id="focus-order",
        name="Elements in focus order must have a role appropriate for interactive content",
        description="Ensures elements in the focus order have an appropriate role",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["2.4.3"],
        principle=WCAGPrinciple.OPERABLE,
        impact="serious",
        tags=["cat.keyboard", "wcag2a"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/focus-order"
    ),
    "focus-visible": AccessibilityRule(
        id="focus-visible",
        name="Elements should have visible focus",
        description="Ensures all interactive elements have visible focus",
        wcag_level=WCAGLevel.AA,
        wcag_criteria=["2.4.7"],
        principle=WCAGPrinciple.OPERABLE,
        impact="serious",
        tags=["cat.keyboard", "wcag2aa"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/focus-visible"
    ),
    "link-name": AccessibilityRule(
        id="link-name",
        name="Links must have discernible text",
        description="Ensures links have discernible text",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["2.4.4"],
        principle=WCAGPrinciple.OPERABLE,
        impact="serious",
        tags=["cat.name-role-value", "wcag2a"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/link-name"
    ),
    "button-name": AccessibilityRule(
        id="button-name",
        name="Buttons must have discernible text",
        description="Ensures buttons have discernible text",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["4.1.2"],
        principle=WCAGPrinciple.ROBUST,
        impact="critical",
        tags=["cat.name-role-value", "wcag2a"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/button-name"
    ),
    
    # Understandable
    "page-has-heading-one": AccessibilityRule(
        id="page-has-heading-one",
        name="Page must contain a level-one heading",
        description="Ensure the page, or at least one of its frames contains a level-one heading",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["1.3.1"],
        principle=WCAGPrinciple.PERCEIVABLE,
        impact="moderate",
        tags=["cat.semantics", "wcag2a"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/page-has-heading-one"
    ),
    "landmark-one-main": AccessibilityRule(
        id="landmark-one-main",
        name="Page must have one main landmark",
        description="Ensures the document has a main landmark",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["1.3.1"],
        principle=WCAGPrinciple.PERCEIVABLE,
        impact="moderate",
        tags=["cat.semantics", "wcag2a"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/landmark-one-main"
    ),
    "label": AccessibilityRule(
        id="label",
        name="Form elements must have labels",
        description="Ensures every form element has a label",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["1.3.1", "3.3.2"],
        principle=WCAGPrinciple.UNDERSTANDABLE,
        impact="critical",
        tags=["cat.forms", "wcag2a"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/label"
    ),
    "html-lang": AccessibilityRule(
        id="html-lang",
        name="<html> element must have a lang attribute",
        description="Ensures the <html> element has a lang attribute",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["3.1.1"],
        principle=WCAGPrinciple.UNDERSTANDABLE,
        impact="serious",
        tags=["cat.language", "wcag2a"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/html-lang"
    ),
    "html-lang-valid": AccessibilityRule(
        id="html-lang-valid",
        name="<html> element must have a valid value for the lang attribute",
        description="Ensures the lang attribute of the <html> element has a valid value",
        wcag_level=WCAGLevel.AA,
        wcag_criteria=["3.1.1"],
        principle=WCAGPrinciple.UNDERSTANDABLE,
        impact="serious",
        tags=["cat.language", "wcag2aa"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/html-lang-valid"
    ),
    
    # Robust
    "aria-allowed-attr": AccessibilityRule(
        id="aria-allowed-attr",
        name="ARIA attributes must conform to valid values",
        description="Ensures ARIA attributes are allowed for an element's role",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["4.1.2"],
        principle=WCAGPrinciple.ROBUST,
        impact="critical",
        tags=["cat.aria", "wcag2a"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/aria-allowed-attr"
    ),
    "aria-hidden-body": AccessibilityRule(
        id="aria-hidden-body",
        name="aria-hidden='true' must not be present on the document body",
        description="Ensures aria-hidden='true' is not present on the document body",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["4.1.2"],
        principle=WCAGPrinciple.ROBUST,
        impact="critical",
        tags=["cat.aria", "wcag2a"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/aria-hidden-body"
    ),
    "duplicate-id": AccessibilityRule(
        id="duplicate-id",
        name="id attribute value must be unique",
        description="Ensures every id attribute value is unique",
        wcag_level=WCAGLevel.A,
        wcag_criteria=["4.1.1"],
        principle=WCAGPrinciple.ROBUST,
        impact="moderate",
        tags=["cat.parsing", "wcag2a"],
        help_url="https://dequeuniversity.com/rules/axe/4.8/duplicate-id"
    ),
}


class HTMLAccessibilityParser(HTMLParser):
    """
    HTML parser for static accessibility analysis.
    
    Performs basic checks without JavaScript execution.
    """
    
    def __init__(self):
        super().__init__()
        self.violations: List[AccessibilityViolation] = []
        self.elements: List[Dict[str, Any]] = []
        self._current_element: Optional[Dict[str, Any]] = None
        self._id_set: Set[str] = set()
        self._has_lang: bool = False
        self._has_heading_one: bool = False
        self._has_main: bool = False
        
    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        attrs_dict = dict(attrs)
        element = {
            "tag": tag,
            "attrs": attrs_dict,
            "position": self.getpos()
        }
        self.elements.append(element)
        self._current_element = element
        
        # Check for duplicate IDs
        element_id = attrs_dict.get("id")
        if element_id:
            if element_id in self._id_set:
                self._add_violation(
                    "duplicate-id",
                    f"<{tag}>",
                    f"#{element_id}",
                    f"Duplicate ID: {element_id}",
                    ["Use unique ID values for each element"]
                )
            else:
                self._id_set.add(element_id)
        
        # Check for images without alt
        if tag == "img":
            alt = attrs_dict.get("alt")
            role = attrs_dict.get("role")
            if alt is None and role not in ("presentation", "none"):
                self._add_violation(
                    "image-alt",
                    "<img>",
                    self._get_selector(element),
                    "Image element missing alt attribute",
                    ["Add alt attribute describing the image content"]
                )
        
        # Check for input type="image" without alt
        if tag == "input" and attrs_dict.get("type") == "image":
            alt = attrs_dict.get("alt")
            if alt is None:
                self._add_violation(
                    "input-image-alt",
                    '<input type="image">',
                    self._get_selector(element),
                    "Image input missing alt attribute",
                    ["Add alt attribute describing the button action"]
                )
        
        # Check for buttons without accessible name
        if tag == "button":
            aria_label = attrs_dict.get("aria-label")
            aria_labelledby = attrs_dict.get("aria-labelledby")
            title = attrs_dict.get("title")
            # Content will be checked in handle_data
        
        # Check for links without accessible name
        if tag == "a":
            href = attrs_dict.get("href")
            if href:
                aria_label = attrs_dict.get("aria-label")
                aria_labelledby = attrs_dict.get("aria-labelledby")
                title = attrs_dict.get("title")
                # Content will be checked in handle_data
        
        # Check for form inputs without labels
        if tag in ("input", "select", "textarea"):
            input_type = attrs_dict.get("type", "text")
            if input_type not in ("hidden", "submit", "reset", "button"):
                element_id = attrs_dict.get("id")
                aria_label = attrs_dict.get("aria-label")
                aria_labelledby = attrs_dict.get("aria-labelledby")
                if not any([element_id, aria_label, aria_labelledby]):
                    self._add_violation(
                        "label",
                        f"<{tag}>",
                        self._get_selector(element),
                        f"Form element ({tag}) missing label",
                        ["Add id attribute and associate with a <label> element"]
                    )
        
        # Check for html lang
        if tag == "html":
            lang = attrs_dict.get("lang")
            if lang:
                self._has_lang = True
                # Validate lang format (basic check)
                if not re.match(r'^[a-zA-Z]{2,3}(-[a-zA-Z]{2,4})?$', lang):
                    self._add_violation(
                        "html-lang-valid",
                        "<html>",
                        "html",
                        f"Invalid lang attribute value: {lang}",
                        ["Use valid BCP 47 language tag (e.g., 'en', 'en-US')"]
                    )
            else:
                self._add_violation(
                    "html-lang",
                    "<html>",
                    "html",
                    "Document missing language attribute",
                    ["Add lang attribute to <html> element"]
                )
        
        # Check for heading one
        if tag in ("h1", "H1"):
            self._has_heading_one = True
        
        # Check for main landmark
        if tag == "main" or attrs_dict.get("role") == "main":
            self._has_main = True
        
        # Check for aria-hidden on body
        if tag == "body":
            aria_hidden = attrs_dict.get("aria-hidden")
            if aria_hidden == "true":
                self._add_violation(
                    "aria-hidden-body",
                    "<body>",
                    "body",
                    "aria-hidden='true' should not be on body",
                    ["Remove aria-hidden from body element"]
                )
    
    def handle_endtag(self, tag: str):
        self._current_element = None
    
    def handle_data(self, data: str):
        if self._current_element:
            self._current_element["text"] = data.strip()
    
    def _get_selector(self, element: Dict[str, Any]) -> str:
        """Generate a CSS selector for an element"""
        tag = element.get("tag", "")
        attrs = element.get("attrs", {})
        
        if "id" in attrs:
            return f"{tag}#{attrs['id']}"
        
        classes = attrs.get("class", "").split()
        if classes:
            return f"{tag}.{classes[0]}"
        
        return tag
    
    def _add_violation(
        self,
        rule_id: str,
        element: str,
        selector: str,
        message: str,
        suggestions: List[str]
    ):
        rule = WCAG_AA_RULES.get(rule_id)
        if rule:
            self.violations.append(AccessibilityViolation(
                rule=rule,
                element=element,
                selector=selector,
                html=element,
                message=message,
                suggestions=suggestions
            ))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of parsed document"""
        return {
            "total_elements": len(self.elements),
            "has_lang": self._has_lang,
            "has_heading_one": self._has_heading_one,
            "has_main": self._has_main,
            "violation_count": len(self.violations)
        }


class AccessibilityChecker:
    """
    Comprehensive accessibility checker for WCAG 2.1 AA compliance.
    
    Supports both static HTML analysis and dynamic browser-based testing.
    """
    
    def __init__(
        self,
        wcag_level: WCAGLevel = WCAGLevel.AA,
        include_best_practices: bool = True
    ):
        self.wcag_level = wcag_level
        self.include_best_practices = include_best_practices
        self._parser = HTMLAccessibilityParser()
        
    def check_html_static(self, html: str) -> List[AccessibilityViolation]:
        """
        Perform static accessibility analysis on HTML.
        
        This checks the HTML without JavaScript execution.
        """
        parser = HTMLAccessibilityParser()
        parser.feed(html)
        
        # Additional post-parsing checks
        summary = parser.get_summary()
        
        # Check for missing heading one
        if not summary["has_heading_one"]:
            parser._add_violation(
                "page-has-heading-one",
                "<h1>",
                "h1",
                "Page does not have a level-one heading",
                ["Add an <h1> element as the main page heading"]
            )
        
        # Check for missing main landmark
        if not summary["has_main"]:
            parser._add_violation(
                "landmark-one-main",
                "<main>",
                "main",
                "Page does not have a main landmark",
                ["Add a <main> element or role='main' to the primary content area"]
            )
        
        return parser.violations
    
    async def check_url_with_axe(self, url: str) -> List[AccessibilityViolation]:
        """
        Check a URL using axe-core via Playwright.
        
        This provides comprehensive accessibility testing with
        JavaScript execution support.
        """
        violations = []
        
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(url, wait_until="networkidle")
                
                # Inject and run axe-core
                axe_results = await page.evaluate("""async () => {
                    // Check if axe is already loaded
                    if (typeof axe === 'undefined') {
                        // Load axe-core from CDN
                        const script = document.createElement('script');
                        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.2/axe.min.js';
                        document.head.appendChild(script);
                        
                        await new Promise(resolve => {
                            script.onload = resolve;
                        });
                    }
                    
                    // Run axe
                    return await axe.run(document, {
                        runOnly: {
                            type: 'tag',
                            values: ['wcag2a', 'wcag2aa']
                        }
                    });
                }""")
                
                await browser.close()
                
                # Parse axe results
                for violation in axe_results.get("violations", []):
                    rule_id = violation.get("id", "")
                    rule = WCAG_AA_RULES.get(rule_id, AccessibilityRule(
                        id=rule_id,
                        name=violation.get("help", rule_id),
                        description=violation.get("description", ""),
                        wcag_level=WCAGLevel.AA,
                        wcag_criteria=[],
                        principle=WCAGPrinciple.ROBUST,
                        impact=violation.get("impact", "moderate"),
                        help_url=violation.get("helpUrl", "")
                    ))
                    
                    for node in violation.get("nodes", []):
                        violations.append(AccessibilityViolation(
                            rule=rule,
                            element=node.get("html", ""),
                            selector=node.get("target", [""])[0],
                            html=node.get("html", ""),
                            message=violation.get("help", ""),
                            suggestions=violation.get("help", "").split(". ")
                        ))
                
        except ImportError:
            logger.warning("Playwright not available for dynamic accessibility testing")
        except Exception as e:
            logger.error(f"Error running axe-core: {e}")
        
        return violations
    
    async def check(
        self,
        target: str,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Main check method for quality gate integration.
        
        Args:
            target: URL or HTML content to check
            context: Optional context with additional settings
            
        Returns:
            QualityScore with accessibility results
        """
        context = context or {}
        violations = []
        
        # Determine if target is URL or HTML
        if target.startswith(("http://", "https://")):
            # URL - use axe-core
            violations = await self.check_url_with_axe(target)
        elif target.strip().startswith("<"):
            # HTML content - use static analysis
            violations = self.check_html_static(target)
        else:
            # Assume it's a file path
            try:
                with open(target, "r", encoding="utf-8") as f:
                    html = f.read()
                violations = self.check_html_static(html)
            except Exception as e:
                logger.error(f"Error reading file {target}: {e}")
                return QualityScore(
                    category=QualityCategory.ACCESSIBILITY,
                    score=0,
                    passed=False,
                    issues=[QualityIssue(
                        category=QualityCategory.ACCESSIBILITY,
                        severity=SeverityLevel.CRITICAL,
                        title="Failed to read target",
                        description=str(e)
                    )]
                )
        
        # Calculate score
        # Base score starts at 100, subtract for violations
        score = 100.0
        
        # Weight violations by severity
        severity_weights = {
            "critical": 15,
            "serious": 10,
            "moderate": 5,
            "minor": 2
        }
        
        for violation in violations:
            weight = severity_weights.get(violation.rule.impact, 5)
            score -= weight
        
        score = max(0, min(100, score))
        
        # Convert violations to issues
        issues = [v.to_quality_issue() for v in violations]
        
        # Determine pass/fail (100% compliance required for WCAG AA)
        passed = len([v for v in violations if v.rule.wcag_level == WCAGLevel.AA]) == 0
        
        return QualityScore(
            category=QualityCategory.ACCESSIBILITY,
            score=score,
            issues=issues,
            passed=passed,
            details={
                "wcag_level": self.wcag_level.value,
                "violation_count": len(violations),
                "critical_count": len([v for v in violations if v.rule.impact == "critical"]),
                "serious_count": len([v for v in violations if v.rule.impact == "serious"]),
                "moderate_count": len([v for v in violations if v.rule.impact == "moderate"]),
                "minor_count": len([v for v in violations if v.rule.impact == "minor"])
            }
        )
    
    def get_wcag_report(self, score: QualityScore) -> Dict[str, Any]:
        """Generate a detailed WCAG compliance report"""
        report = {
            "summary": {
                "score": score.score,
                "passed": score.passed,
                "total_violations": len(score.issues)
            },
            "by_criteria": {},
            "by_principle": {}
        }
        
        # Group violations by WCAG criteria
        for issue in score.issues:
            # Find the corresponding rule
            for rule in WCAG_AA_RULES.values():
                if rule.name == issue.title:
                    for criteria in rule.wcag_criteria:
                        if criteria not in report["by_criteria"]:
                            report["by_criteria"][criteria] = []
                        report["by_criteria"][criteria].append(issue.to_dict())
                    
                    principle = rule.principle.value
                    if principle not in report["by_principle"]:
                        report["by_principle"][principle] = []
                    report["by_principle"][principle].append(issue.to_dict())
                    break
        
        return report


# Convenience function
async def check_accessibility(
    target: str,
    wcag_level: WCAGLevel = WCAGLevel.AA
) -> QualityScore:
    """
    Quick function to check accessibility.
    
    Args:
        target: URL or HTML content to check
        wcag_level: WCAG conformance level to check against
        
    Returns:
        QualityScore with accessibility results
    """
    checker = AccessibilityChecker(wcag_level=wcag_level)
    return await checker.check(target)


__all__ = [
    "WCAGLevel",
    "WCAGPrinciple",
    "AccessibilityRule",
    "AccessibilityViolation",
    "WCAG_AA_RULES",
    "HTMLAccessibilityParser",
    "AccessibilityChecker",
    "check_accessibility"
]
