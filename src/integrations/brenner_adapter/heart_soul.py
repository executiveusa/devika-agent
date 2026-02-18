import json
import os
from typing import Dict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "..", "data", "brenner")

def _ensure_data_dir(path: str):
    os.makedirs(path, exist_ok=True)

def generate_heart_soul(base_dir: str = None) -> Dict[str, str]:
    """Generate heart.json and soul.json under `data/brenner/`.

    Returns paths written.
    """
    # Resolve base data directory
    if base_dir is None:
        # place under repository data/brenner
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        base_dir = os.path.join(repo_root, "data", "brenner")

    _ensure_data_dir(base_dir)

    heart = {
        "name": "Brenner Bot",
        "version": "0.1",
        "repo": "https://github.com/Dicklesworthstone/brenner_bot",
        "capabilities": ["deep-reasoning", "artifact-compiler", "delta-protocol"],
        "author": "Brenner Authors",
    }

    soul = {
        "persona": "Brenner - research conductor",
        "goals": [
            "provide stepwise deep reasoning",
            "compile multi-agent artifacts",
            "explain chain-of-thought in structured deltas"
        ],
        "safety_policy": {
            "external_code_execution": "disabled_by_default",
            "allowed_actions": ["explain", "suggest", "compile_artifact"]
        },
        "visual_avatar": None
    }

    heart_path = os.path.join(base_dir, "heart.json")
    soul_path = os.path.join(base_dir, "soul.json")

    with open(heart_path, "w", encoding="utf-8") as f:
        json.dump(heart, f, indent=2)

    with open(soul_path, "w", encoding="utf-8") as f:
        json.dump(soul, f, indent=2)

    return {"heart": heart_path, "soul": soul_path}
