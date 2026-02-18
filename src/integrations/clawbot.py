"""Clawbot integration helper

Provides lightweight utilities to ensure a Clawbot repo is present locally,
load or generate the agent `heart` and `soul` files, and expose a simple API
for other agents to query Clawbot capabilities.

This module intentionally avoids executing remote code automatically; it
provides utilities so maintainers can review before enabling network actions.
"""
import os
import json
import subprocess
from typing import Dict, Any

from ..config import _Cfg


def ensure_claw_repo(dest_dir: str = None) -> Dict[str, Any]:
    cfg = _Cfg()
    repo = cfg.get("CLAW_REPO_URL")
    if not repo:
        return {"status": "no_repo_configured"}

    dest = dest_dir or os.path.join(cfg.get_storage_dir(), "clawrepo")
    os.makedirs(dest, exist_ok=True)

    # If .git exists, assume cloned
    if os.path.isdir(os.path.join(dest, ".git")):
        return {"status": "present", "path": dest}

    # Provide a safe command to clone; do NOT run automatically without consent
    return {"status": "missing", "suggested_clone_cmd": f"git clone {repo} {dest}"}


def load_heart_and_soul(heart_path: str = None, soul_path: str = None) -> Dict[str, Any]:
    cfg = _Cfg()
    heart = heart_path or cfg.get("CLAW_HEART_PATH")
    soul = soul_path or cfg.get("CLAW_SOUL_PATH")

    result = {"heart": None, "soul": None}

    try:
        if heart and os.path.isfile(heart):
            with open(heart, "r", encoding="utf-8") as f:
                result["heart"] = json.load(f)
    except Exception as e:
        result["heart_error"] = str(e)

    try:
        if soul and os.path.isfile(soul):
            with open(soul, "r", encoding="utf-8") as f:
                result["soul"] = json.load(f)
    except Exception as e:
        result["soul_error"] = str(e)

    return result


def generate_default_heart_and_soul(heart_path: str = None, soul_path: str = None) -> Dict[str, str]:
    cfg = _Cfg()
    heart = heart_path or cfg.get("CLAW_HEART_PATH") or "src/synthia/claw/heart.json"
    soul = soul_path or cfg.get("CLAW_SOUL_PATH") or "src/synthia/claw/soul.json"

    os.makedirs(os.path.dirname(heart), exist_ok=True)
    os.makedirs(os.path.dirname(soul), exist_ok=True)

    default_heart = {
        "agent_name": "clawbot",
        "goal": "assist via Whatsapp channel",
        "skills": ["send_message", "receive_message", "handle_webhook"]
    }

    default_soul = {
        "ethos": "assistive, safety-first, follow-ralphy-loop",
        "long_term_goal_path": "e:/ACTIVE PROJECTS-PIPELINE/ACTIVE PROJECTS-PIPELINE/AGENT ZERO/Building a Future-Proof Autonomous.txt"
    }

    with open(heart, "w", encoding="utf-8") as f:
        json.dump(default_heart, f, indent=2)

    with open(soul, "w", encoding="utf-8") as f:
        json.dump(default_soul, f, indent=2)

    return {"heart": heart, "soul": soul}


def suggest_clone_and_setup_messages() -> Dict[str, str]:
    """Return human-actionable steps for maintainers to fully integrate Clawbot."""
    cfg = _Cfg()
    repo = cfg.get("CLAW_REPO_URL") or "<not-configured>"
    return {
        "clone": f"git clone {repo} data/repos/clawbot",
        "review": "Review cloned code and only enable automatic loading after manual review.",
        "generate_heart_soul": "Call integrations.clawbot.generate_default_heart_and_soul() to create default files."
    }
