"""Simple workspace search utility exposed to agents.

Provides a thin wrapper around recursive file search for use by agents
that need to grep the workspace (e.g., 'grep mcperver' or similar tools).
"""
import os
from typing import List


def search_workspace(root: str, query: str, max_results: int = 100) -> List[str]:
    matches = []
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f):
                        if query in line:
                            matches.append(f"{path}:{i+1}:{line.strip()}")
                            if len(matches) >= max_results:
                                return matches
            except Exception:
                continue
    return matches
