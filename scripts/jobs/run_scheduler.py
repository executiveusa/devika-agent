"""Run production-like scheduler jobs locally."""

import logging
import os
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import Config
from src.synthia.jobs.scheduler import SchedulerManager
from src.synthia.jobs.memory_sync import MemorySync
from src.synthia.agent_registry import AgentRegistry
from src.synthia.webhook import ArchonXWebhook
from src.synthia.investigation.repo_scanner import RepositoryScanner

logging.basicConfig(level=logging.INFO)


def main():
    cfg = Config()
    webhook_url = cfg.get_archon_webhook_url().strip()
    webhook_secret = cfg.get_archon_webhook_secret().strip()
    if webhook_url:
        os.environ.setdefault("ARCHON_X_WEBHOOK_URL", webhook_url)
    if webhook_secret:
        os.environ.setdefault("ARCHON_X_WEBHOOK_SECRET", webhook_secret)

    def heartbeat_job():
        webhook = ArchonXWebhook(enable_batching=False)
        if not webhook.is_configured():
            print("[scheduler] heartbeat skipped: webhook not configured")
            return
        registry = AgentRegistry()
        for agent in registry.list_agents():
            webhook.send_heartbeat(agent.name, "alive", {"execution_count": registry._agents[agent.name].execution_count})

    def repo_scan_job():
        scanner = RepositoryScanner()
        result = scanner.scan(".")
        print(f"[scheduler] repo scan files={result.total_files} broken={len(result.broken_code)}")

    sched = SchedulerManager(db_path=cfg.get_scheduler_db_path())
    memory_sync = MemorySync(dry_run=False)

    sched.add_interval_job(
        heartbeat_job,
        seconds=cfg.get_scheduler_heartbeat_seconds(),
        job_id="heartbeat",
    )
    sched.add_interval_job(
        memory_sync.sync,
        seconds=cfg.get_scheduler_memory_sync_seconds(),
        job_id="memory_sync",
    )
    sched.add_interval_job(
        repo_scan_job,
        seconds=cfg.get_scheduler_repo_scan_seconds(),
        job_id="repo_scan",
    )

    sched.start()
    print(f"[scheduler] started with jobs: {sched.health()['jobs']}")
    try:
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        print("[scheduler] stopping")
    finally:
        sched.shutdown()


if __name__ == "__main__":
    main()
