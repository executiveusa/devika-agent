"""Minimal Meta-Skill (ms) client stub.

This module provides a small wrapper to query a local `ms` installation or
to return empty results when `ms` is not present. It is intentionally simple
so it can be expanded later to call an MCP HTTP endpoint or CLI.
"""
from typing import List, Dict
import shutil
import subprocess
from src.logger import Logger

logger = Logger()


class MSClient:
    def __init__(self, ms_path: str = "ms"):
        self.ms_path = ms_path

    def available(self) -> bool:
        return shutil.which(self.ms_path) is not None

    def search_skills(self, query: str) -> List[Dict]:
        """Return a list of matching skills. Stub returns empty list when `ms` missing."""
        if not self.available():
            logger.debug("ms client not available; returning empty skill list")
            return []
        try:
            # Example: `ms search "query" --json` if ms supported
            out = subprocess.check_output([self.ms_path, "search", query, "--json"], text=True)
            # In a full implementation parse JSON and return
            return []
        except Exception as e:
            logger.error(str(e))
            return []

    def fetch_skill(self, skill_id: str) -> Dict:
        if not self.available():
            return {}
        try:
            out = subprocess.check_output([self.ms_path, "get", skill_id, "--json"], text=True)
            return {}
        except Exception:
            return {}


ms_client = MSClient()
