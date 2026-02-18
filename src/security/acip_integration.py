"""ACIP integration - lightweight prompt-injection checks and sanitizer.

This module provides a compact, safe-check wrapper that can be used as
an initial gate before sending prompts to expensive LLM calls. It implements
a quick heuristic checker and allows plugging a fuller ACIP prompt if
available in `beads/` or `resources/`.
"""
from typing import Dict, Optional
import re
from src.socket_instance import emit_agent


class ACIP:
    def __init__(self):
        # Load optional full ACIP text if present (not required)
        self.heuristic_patterns = [
            r"\brm\s+-rf\b",
            r"\bsudo\b",
            r"\bshutdown\b",
            r"\bformat\b",
            r"IGNORE\s+PREVIOUS\s+INSTRUCTIONS",
            r"\bopen\s+SSH\b",
        ]

    def check_prompt(self, prompt: str) -> Dict[str, Optional[str]]:
        """
        Run lightweight checks on `prompt`.

        Returns a dict:
          {
            "allowed": bool,
            "verdict": str,  # short description
            "sanitized": Optional[str]
          }
        """
        lowered = prompt.lower()

        # Basic forbidden tokens
        for pat in self.heuristic_patterns:
            if re.search(pat, prompt, re.IGNORECASE):
                emit_agent("info", {"type": "warning", "message": "ACIP blocked dangerous token in prompt"})
                return {"allowed": False, "verdict": "blocked: destructive token detected", "sanitized": None}

        # Look for 'ignore previous' style jailbreaks
        if "ignore previous" in lowered or "disregard previous" in lowered:
            return {"allowed": False, "verdict": "blocked: attempted instruction override", "sanitized": None}

        # Minimal sanitization: remove control sequences that look like shell commands
        sanitized = re.sub(r"[`$]\\w+", "", prompt)

        return {"allowed": True, "verdict": "ok", "sanitized": sanitized}


acip = ACIP()
