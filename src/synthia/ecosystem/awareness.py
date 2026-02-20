import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import urllib.request


@dataclass
class PulseResult:
    saved: bool
    sent_webhook: bool
    sent_agent_mail: bool


class EcosystemAwareness:
    """Persistent cross-repo awareness bridge for SYNTHIA.

    Writes local beads events and optionally sends heartbeat signals
    to Archon X webhook and Agent Mail MCP endpoints.
    """

    def __init__(
        self,
        manifest_path: str = "ecosystem/ecosystem-manifest.json",
        beads_path: str = "data/beads/ecosystem-awareness.jsonl",
        webhook_url: str = "",
        agent_mail_http_url: str = "",
        agent_mail_token: str = "",
    ):
        self.manifest_path = manifest_path
        self.beads_path = beads_path
        self.webhook_url = webhook_url
        self.agent_mail_http_url = agent_mail_http_url
        self.agent_mail_token = agent_mail_token
        self._last_error = ""

    def load_manifest(self) -> Dict[str, Any]:
        path = Path(self.manifest_path)
        if not path.exists():
            return {"repos": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def _append_bead(self, payload: Dict[str, Any]) -> bool:
        bead_file = Path(self.beads_path)
        bead_file.parent.mkdir(parents=True, exist_ok=True)
        with bead_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
        return True

    def _post_json(self, url: str, payload: Dict[str, Any], headers: Dict[str, str] | None = None) -> bool:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", **(headers or {})},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=8):
                return True
        except Exception as exc:
            self._last_error = str(exc)
            return False

    def pulse(self, source: str, context: Dict[str, Any] | None = None) -> PulseResult:
        manifest = self.load_manifest()
        payload = {
            "event": "ecosystem.pulse",
            "source": source,
            "ts": int(time.time()),
            "context": context or {},
            "repos": [r.get("name") for r in manifest.get("repos", [])],
        }

        saved = self._append_bead(payload)

        sent_webhook = False
        if self.webhook_url:
            sent_webhook = self._post_json(self.webhook_url, payload)

        sent_agent_mail = False
        if self.agent_mail_http_url:
            mail_payload = {
                "type": "message",
                "message": {
                    "sender": source,
                    "recipient": "broadcast",
                    "message_type": "broadcast",
                    "subject": "ecosystem.pulse",
                    "payload": payload,
                },
            }
            headers = {}
            if self.agent_mail_token:
                headers["Authorization"] = f"Bearer {self.agent_mail_token}"
            sent_agent_mail = self._post_json(self.agent_mail_http_url, mail_payload, headers=headers)

        if not sent_webhook and self.webhook_url:
            payload.setdefault("errors", []).append({"channel": "webhook", "error": self._last_error})
        if not sent_agent_mail and self.agent_mail_http_url:
            payload.setdefault("errors", []).append({"channel": "agent_mail", "error": self._last_error})
            self._append_bead(payload)

        return PulseResult(saved=saved, sent_webhook=sent_webhook, sent_agent_mail=sent_agent_mail)
