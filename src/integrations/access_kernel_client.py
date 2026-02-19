"""Minimal Access Kernel client for privileged action authorization."""

from __future__ import annotations

import os
from typing import Any

import requests


class AccessKernelClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("ACCESS_KERNEL_BASE_URL", "http://localhost:8090")).rstrip("/")

    def request_grant(self, *, principal: str, principal_type: str, work_item_id: str, resource: str, action: str, duration_minutes: int = 15) -> dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/v1/grants/request",
            json={
                "principal": principal,
                "principal_type": principal_type,
                "work_item_id": work_item_id,
                "resource": resource,
                "action": action,
                "duration_minutes": duration_minutes,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


def require_github_write_access(*, work_item_id: str, principal: str = "devika-agent") -> None:
    if not work_item_id:
        raise PermissionError("work_item_id is required for GitHub write actions")

    client = AccessKernelClient()
    grant = client.request_grant(
        principal=principal,
        principal_type="agent",
        work_item_id=work_item_id,
        resource="github",
        action="write",
        duration_minutes=15,
    )
    if grant.get("status") not in {"approved", "pending_approval"}:
        raise PermissionError("Access Kernel denied GitHub write action")
