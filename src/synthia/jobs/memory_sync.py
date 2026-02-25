"""Memory synchronization to external targets.

This module provides memory synchronization from local storage to external
targets like Archon X webhook. It supports dry-run mode and provides
detailed status reporting.

Environment Variables:
    ARCHON_X_WEBHOOK_URL: URL for the Archon X webhook endpoint
    ARCHON_X_WEBHOOK_SECRET: Secret for webhook authentication
    MEMORY_SYNC_DRY_RUN: Set to "true" for dry-run mode (no actual sync)
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import time

from src.synthia.memory import MemoryLayer, MemoryManager
from src.synthia.webhook import ArchonXWebhook

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Status of a sync operation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"
    DRY_RUN = "dry_run"
    NOT_CONFIGURED = "not_configured"


class SyncTargetStatus(Enum):
    """Status of individual sync targets."""
    CONFIGURED = "configured"
    NOT_CONFIGURED = "not_configured"
    ERROR = "error"


@dataclass
class LayerSyncResult:
    """Result of syncing a single memory layer."""
    layer: str
    entries_count: int
    status: str
    error: Optional[str] = None
    elapsed_seconds: Optional[float] = None


@dataclass
class SyncResult:
    """Result of a complete sync operation."""
    status: SyncStatus
    total_scanned: int = 0
    total_synced: int = 0
    total_failed: int = 0
    layers: List[LayerSyncResult] = field(default_factory=list)
    elapsed_seconds: Optional[float] = None
    message: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status.value,
            "total_scanned": self.total_scanned,
            "total_synced": self.total_synced,
            "total_failed": self.total_failed,
            "layers": [
                {
                    "layer": l.layer,
                    "entries_count": l.entries_count,
                    "status": l.status,
                    "error": l.error,
                    "elapsed_seconds": l.elapsed_seconds,
                }
                for l in self.layers
            ],
            "elapsed_seconds": self.elapsed_seconds,
            "message": self.message,
        }


@dataclass
class TargetHealthCheck:
    """Health check result for sync targets."""
    target: str
    status: SyncTargetStatus
    message: str
    configured: bool = False


class MemorySync:
    """Sync memory layers to external targets.
    
    This class synchronizes memory data from local storage to external
    targets like Archon X webhook. It supports:
    - Multiple memory layers (PROJECT, TEAM, GLOBAL)
    - Dry-run mode for testing
    - Detailed status reporting
    - Health checks for targets
    
    Example:
        sync = MemorySync()
        
        # Check if targets are configured
        health = sync.health_check()
        
        # Perform sync
        result = sync.sync()
        if result.status == SyncStatus.SUCCESS:
            print(f"Synced {result.total_synced} entries")
    """
    
    def __init__(
        self,
        dry_run: bool = False,
        webhook: Optional[ArchonXWebhook] = None,
        memory: Optional[MemoryManager] = None,
    ):
        """Initialize the memory sync.
        
        Args:
            dry_run: If True, don't actually sync, just report what would be synced.
            webhook: Optional webhook instance. If not provided, creates default.
            memory: Optional memory manager. If not provided, creates default.
        """
        self.dry_run = dry_run
        self.memory = memory or MemoryManager(enable_embeddings=False)
        self.webhook = webhook or ArchonXWebhook()
        
        # Log initialization state
        self._log_initialization_state()
    
    def _log_initialization_state(self) -> None:
        """Log the initialization state for debugging."""
        webhook_configured = self.webhook.is_configured()
        if self.dry_run:
            logger.info("MemorySync initialized in DRY_RUN mode (no actual sync)")
        elif webhook_configured:
            logger.info("MemorySync initialized with webhook target configured")
        else:
            logger.warning(
                "MemorySync initialized but webhook target NOT configured. "
                "Set ARCHON_X_WEBHOOK_URL environment variable to enable sync."
            )
    
    def health_check(self) -> List[TargetHealthCheck]:
        """Check health of all sync targets.
        
        Returns:
            List of health check results for each target.
        """
        results = []
        
        # Check webhook target
        if self.webhook.is_configured():
            results.append(TargetHealthCheck(
                target="archon_x_webhook",
                status=SyncTargetStatus.CONFIGURED,
                message="Webhook is configured and ready",
                configured=True,
            ))
        else:
            results.append(TargetHealthCheck(
                target="archon_x_webhook",
                status=SyncTargetStatus.NOT_CONFIGURED,
                message="ARCHON_X_WEBHOOK_URL not set - sync will be skipped",
                configured=False,
            ))
        
        return results
    
    def is_configured(self) -> bool:
        """Check if any sync target is configured.
        
        Returns:
            True if at least one target is configured.
        """
        return self.webhook.is_configured()
    
    def sync(self, strict: bool = False) -> SyncResult:
        """Sync all memory layers to external targets.
        
        Args:
            strict: If True, raise exception when targets not configured.
            
        Returns:
            SyncResult with detailed status information.
            
        Raises:
            RuntimeError: If strict=True and no targets are configured.
        """
        start_time = time.time()
        
        logger.info(f"MemorySync: starting (dry_run={self.dry_run})")
        
        # Check configuration
        if not self.is_configured():
            if strict:
                raise RuntimeError(
                    "No sync targets configured. Set ARCHON_X_WEBHOOK_URL to enable sync."
                )
            logger.warning("MemorySync: no targets configured, returning skipped status")
            return SyncResult(
                status=SyncStatus.NOT_CONFIGURED,
                message="No sync targets configured. Set ARCHON_X_WEBHOOK_URL environment variable.",
            )
        
        # Dry run mode
        if self.dry_run:
            return self._dry_run_sync(start_time)
        
        # Actual sync
        return self._actual_sync(start_time)
    
    def _dry_run_sync(self, start_time: float) -> SyncResult:
        """Perform a dry-run sync (no actual data transfer).
        
        Args:
            start_time: Start time for elapsed calculation.
            
        Returns:
            SyncResult with dry-run status.
        """
        total_scanned = 0
        layer_results: List[LayerSyncResult] = []
        
        for layer in [MemoryLayer.PROJECT, MemoryLayer.TEAM, MemoryLayer.GLOBAL]:
            layer_start = time.time()
            layer_data = self.memory.export_layer(layer)
            entries: List[Dict] = layer_data.get("entries", [])
            count = len(entries)
            total_scanned += count
            
            layer_results.append(LayerSyncResult(
                layer=layer.value,
                entries_count=count,
                status="dry_run",
                elapsed_seconds=time.time() - layer_start,
            ))
        
        elapsed = time.time() - start_time
        logger.info(f"MemorySync: dry-run completed, scanned {total_scanned} entries")
        
        return SyncResult(
            status=SyncStatus.DRY_RUN,
            total_scanned=total_scanned,
            total_synced=0,
            total_failed=0,
            layers=layer_results,
            elapsed_seconds=elapsed,
            message=f"Dry-run completed. Would sync {total_scanned} entries.",
        )
    
    def _actual_sync(self, start_time: float) -> SyncResult:
        """Perform actual sync to external targets.
        
        Args:
            start_time: Start time for elapsed calculation.
            
        Returns:
            SyncResult with actual sync status.
        """
        total_scanned = 0
        total_synced = 0
        total_failed = 0
        layer_results: List[LayerSyncResult] = []
        
        for layer in [MemoryLayer.PROJECT, MemoryLayer.TEAM, MemoryLayer.GLOBAL]:
            layer_start = time.time()
            layer_data = self.memory.export_layer(layer)
            entries: List[Dict] = layer_data.get("entries", [])
            count = len(entries)
            total_scanned += count
            
            if count == 0:
                layer_results.append(LayerSyncResult(
                    layer=layer.value,
                    entries_count=0,
                    status="skipped",
                    elapsed_seconds=time.time() - layer_start,
                    error="No entries to sync",
                ))
                continue
            
            # Sync to webhook
            sync_result = self.webhook.sync_memory_layer(layer.value, entries)
            layer_elapsed = time.time() - layer_start
            
            if sync_result.get("status") in ("success", "queued"):
                total_synced += count
                layer_results.append(LayerSyncResult(
                    layer=layer.value,
                    entries_count=count,
                    status="success",
                    elapsed_seconds=layer_elapsed,
                ))
                logger.info(f"MemorySync: synced {count} entries from {layer.value}")
            else:
                total_failed += count
                error_msg = sync_result.get("error", sync_result.get("reason", "Unknown error"))
                layer_results.append(LayerSyncResult(
                    layer=layer.value,
                    entries_count=count,
                    status="failed",
                    error=error_msg,
                    elapsed_seconds=layer_elapsed,
                ))
                logger.warning(
                    f"MemorySync: layer {layer.value} failed: {error_msg}"
                )
        
        elapsed = time.time() - start_time
        
        # Determine overall status
        if total_failed == 0 and total_synced > 0:
            status = SyncStatus.SUCCESS
            message = f"Successfully synced {total_synced} entries"
        elif total_synced > 0 and total_failed > 0:
            status = SyncStatus.PARTIAL
            message = f"Partial sync: {total_synced} succeeded, {total_failed} failed"
        elif total_scanned == 0:
            status = SyncStatus.SKIPPED
            message = "No entries to sync"
        else:
            status = SyncStatus.FAILED
            message = f"Sync failed: {total_failed} entries could not be synced"
        
        result = SyncResult(
            status=status,
            total_scanned=total_scanned,
            total_synced=total_synced,
            total_failed=total_failed,
            layers=layer_results,
            elapsed_seconds=elapsed,
            message=message,
        )
        
        logger.info(f"MemorySync: completed with status {status.value}: {message}")
        return result
    
    def sync_layer(self, layer: MemoryLayer, strict: bool = False) -> LayerSyncResult:
        """Sync a single memory layer.
        
        Args:
            layer: The memory layer to sync.
            strict: If True, raise exception on failure.
            
        Returns:
            LayerSyncResult with status.
        """
        start_time = time.time()
        
        if not self.is_configured():
            if strict:
                raise RuntimeError("No sync targets configured")
            return LayerSyncResult(
                layer=layer.value,
                entries_count=0,
                status="skipped",
                error="No targets configured",
            )
        
        if self.dry_run:
            layer_data = self.memory.export_layer(layer)
            entries: List[Dict] = layer_data.get("entries", [])
            return LayerSyncResult(
                layer=layer.value,
                entries_count=len(entries),
                status="dry_run",
                elapsed_seconds=time.time() - start_time,
            )
        
        layer_data = self.memory.export_layer(layer)
        entries: List[Dict] = layer_data.get("entries", [])
        count = len(entries)
        
        if count == 0:
            return LayerSyncResult(
                layer=layer.value,
                entries_count=0,
                status="skipped",
                error="No entries to sync",
                elapsed_seconds=time.time() - start_time,
            )
        
        sync_result = self.webhook.sync_memory_layer(layer.value, entries)
        elapsed = time.time() - start_time
        
        if sync_result.get("status") in ("success", "queued"):
            return LayerSyncResult(
                layer=layer.value,
                entries_count=count,
                status="success",
                elapsed_seconds=elapsed,
            )
        else:
            error_msg = sync_result.get("error", sync_result.get("reason", "Unknown error"))
            if strict:
                raise RuntimeError(f"Sync failed for {layer.value}: {error_msg}")
            return LayerSyncResult(
                layer=layer.value,
                entries_count=count,
                status="failed",
                error=error_msg,
                elapsed_seconds=elapsed,
            )
