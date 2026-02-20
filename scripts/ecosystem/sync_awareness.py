import json
from src.config import Config
from src.synthia.ecosystem import EcosystemAwareness


def main() -> None:
    cfg = Config()
    awareness = EcosystemAwareness(
        manifest_path=cfg.config.get("FEATURES", {}).get("ECOSYSTEM_MANIFEST_PATH", "ecosystem/ecosystem-manifest.json"),
        beads_path=cfg.config.get("FEATURES", {}).get("ECOSYSTEM_BEADS_PATH", "data/beads/ecosystem-awareness.jsonl"),
        webhook_url=cfg.config.get("FEATURES", {}).get("ARCHON_X_WEBHOOK_URL", ""),
        agent_mail_http_url=cfg.config.get("FEATURES", {}).get("AGENT_MAIL_MCP_HTTP", ""),
        agent_mail_token=cfg.config.get("FEATURES", {}).get("AGENT_MAIL_MCP_TOKEN", ""),
    )
    result = awareness.pulse("synthia-core", {"mode": "manual_sync"})
    print(json.dumps({
        "saved": result.saved,
        "sent_webhook": result.sent_webhook,
        "sent_agent_mail": result.sent_agent_mail,
    }))


if __name__ == "__main__":
    main()
