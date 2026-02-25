"""Send heartbeat to Archon X for all registered agents."""

from datetime import datetime
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import Config
from src.synthia.agent_registry import AgentRegistry
from src.synthia.webhook import ArchonXWebhook


def main() -> int:
    cfg = Config()
    if cfg.get_archon_webhook_url().strip():
        os.environ.setdefault("ARCHON_X_WEBHOOK_URL", cfg.get_archon_webhook_url().strip())
    if cfg.get_archon_webhook_secret().strip():
        os.environ.setdefault("ARCHON_X_WEBHOOK_SECRET", cfg.get_archon_webhook_secret().strip())

    registry = AgentRegistry()
    webhook = ArchonXWebhook(enable_batching=False)

    if not webhook.is_configured():
        print("[heartbeat] skipped: ARCHON_X_WEBHOOK not configured")
        return 0

    sent = 0
    for agent in registry.list_agents():
        metrics = {
            "execution_count": registry._agents[agent.name].execution_count,
            "error_count": registry._agents[agent.name].error_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
        result = webhook.send_heartbeat(agent.name, "alive", metrics)
        if result.get("status") in ("success", "queued"):
            sent += 1

    print(f"[heartbeat] sent={sent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
