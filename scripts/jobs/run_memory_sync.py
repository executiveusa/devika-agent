"""Run memory sync in dry-run mode for local testing."""
from src.synthia.jobs.memory_sync import MemorySync
import logging

logging.basicConfig(level=logging.INFO)


def main():
    ms = MemorySync(dry_run=True)
    ms.sync()


if __name__ == "__main__":
    main()
