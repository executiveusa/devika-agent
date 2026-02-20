import json
from typing import Dict
import os
import requests

class BrennerAdapter:
    """Minimal Brenner adapter. Currently runs in simulate mode by default.

    Real implementations should replace `send_query` to call the real Brenner service
    or shell out to the `third_party/brenner_bot` CLI when available.
    """

    def __init__(self, simulate: bool = True):
        # read configuration if present
        cfg_sim = os.environ.get("BRENNER_SIMULATE")
        if cfg_sim is not None:
            self.simulate = cfg_sim.lower() not in ("0", "false", "no")
        else:
            self.simulate = simulate

    def send_query(self, query: str, stream: bool = False) -> Dict:
        """Send a query to Brenner. Returns a dict reply.

        For now this returns a simulated reply. If `simulate` is False, implement
        the real call (HTTP, CLI, or IPC) here.
        """
        if self.simulate:
            # simple simulated reply structure
            return {
                "source": "brenner_sim",
                "query": query,
                "reply": f"[Simulated Brenner deep-reasoning reply on] {query}",
                "stream": stream
            }

        endpoint = os.environ.get("BRENNER_HTTP_URL", "").strip()
        token = os.environ.get("BRENNER_HTTP_TOKEN", "").strip()
        if not endpoint:
            return {
                "source": "brenner",
                "query": query,
                "error": "BRENNER_HTTP_URL not configured",
                "stream": stream,
            }

        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            resp = requests.post(
                endpoint,
                json={"query": query, "stream": stream},
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "source": "brenner_http",
                "query": query,
                "reply": data.get("reply", data),
                "stream": stream,
            }
        except Exception as exc:
            return {
                "source": "brenner_http",
                "query": query,
                "error": str(exc),
                "stream": stream,
            }
