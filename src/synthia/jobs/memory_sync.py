from typing import Dict
import logging

from src.synthia.memory import MemoryLayer, MemoryManager

logger = logging.getLogger(__name__)


class MemorySync:
    """Skeleton memory sync: pushes PROJECT layer entries to TEAM/GLOBAL endpoints.

    This is a dry-run-first implementation; real network/backends must be provided
    and enabled in config.toml.
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.memory = MemoryManager(enable_embeddings=False)

    def sync(self) -> Dict[str, int]:
        logger.info("MemorySync: starting (dry_run=%s)", self.dry_run)
        project_data = self.memory.export_layer(MemoryLayer.PROJECT)
        entries = project_data.get("entries", [])
        scanned = len(entries)
        synced = 0

        if not self.dry_run:
            for e in entries:
                key = f"team:{e['key']}"
                self.memory.store(
                    key=key,
                    value=e.get("value", ""),
                    layer=MemoryLayer.TEAM,
                    project_name=e.get("project_name"),
                )
                synced += 1

        result = {"scanned": scanned, "synced": synced}
        logger.info("MemorySync: completed: %s", result)
        return result
