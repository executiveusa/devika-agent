from typing import Dict, Any
import requests


class BrightDataMCPClient:
    """Small HTTP client for a BrightData MCP endpoint.

    This client is intentionally minimal and safe-by-default. It only performs
    explicit POST calls with caller-provided payloads.
    """

    def __init__(self, endpoint: str = "", api_key: str = "", timeout: int = 30):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def configured(self) -> bool:
        return bool(self.endpoint and self.api_key)

    def call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.configured():
            return {
                "ok": False,
                "error": "BrightData MCP not configured"
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "method": method,
            "params": params,
        }

        response = requests.post(
            self.endpoint,
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()


brightdata_mcp_client = BrightDataMCPClient()
