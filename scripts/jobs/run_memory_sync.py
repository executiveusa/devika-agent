"""Run memory sync job."""

import argparse
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import Config
from src.synthia.jobs.memory_sync import MemorySync

logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    cfg = Config()
    if cfg.get_archon_webhook_url().strip():
        os.environ.setdefault("ARCHON_X_WEBHOOK_URL", cfg.get_archon_webhook_url().strip())
    if cfg.get_archon_webhook_secret().strip():
        os.environ.setdefault("ARCHON_X_WEBHOOK_SECRET", cfg.get_archon_webhook_secret().strip())

    ms = MemorySync(dry_run=args.dry_run)
    result = ms.sync()
    print(f"[memory-sync] {result.to_dict()}")
    return 0 if result.total_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
