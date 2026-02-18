"""
SYNTHIA Archon X Webhook Integration
====================================
Syncs all agent knowledge to the central Archon X brain.

Archon X is the central spaceship in the Yappyverse that serves as
the brain of the entire agent ecosystem. All agents sync their
knowledge, memories, and learnings to Archon X.

Features:
- Real-time knowledge sync
- Agent heartbeat monitoring
- Task completion reporting
- Memory layer synchronization
- Error reporting and alerting
"""

import os
import json
import hashlib
import time
import threading
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor


class SyncStatus(Enum):
    """Status of a sync operation"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


class EventType(Enum):
    """Types of events to sync"""
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    MEMORY_STORE = "memory_store"
    MEMORY_SEARCH = "memory_search"
    HEARTBEAT = "heartbeat"
    KNOWLEDGE_SYNC = "knowledge_sync"
    ERROR_REPORT = "error_report"


@dataclass
class WebhookPayload:
    """Payload sent to Archon X"""
    event_type: str
    agent_name: str
    timestamp: str
    data: Dict[str, Any]
    checksum: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        return json.dumps({
            "event_type": self.event_type,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp,
            "data": self.data,
            "checksum": self.checksum,
            "metadata": self.metadata
        })
    
    def generate_checksum(self, secret: str) -> str:
        """Generate checksum for payload verification"""
        content = f"{self.event_type}:{self.agent_name}:{self.timestamp}:{secret}"
        self.checksum = hashlib.sha256(content.encode()).hexdigest()[:32]
        return self.checksum


class ArchonXWebhook:
    """
    Webhook integration with Archon X.
    
    Archon X (git@github.com:executiveusa/archonx-os.git) is the central brain
    of the Yappyverse agent ecosystem. All agents sync their knowledge here.
    
    Usage:
        webhook = ArchonXWebhook(
            url="https://archonx.yappyverse.io/webhook",
            secret="your-webhook-secret"
        )
        
        # Sync task completion
        webhook.sync_task_completion(
            task_id="abc123",
            project_name="my-project",
            result={"status": "success"}
        )
        
        # Sync knowledge
        webhook.sync_knowledge(
            agent_name="coder",
            task_id="abc123",
            result={"patterns_learned": [...]}
        )
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        secret: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        batch_size: int = 10,
        enable_batching: bool = True
    ):
        self.url = url or os.getenv("ARCHON_X_WEBHOOK_URL", "")
        self.secret = secret or os.getenv("ARCHON_X_WEBHOOK_SECRET", "")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.batch_size = batch_size
        self.enable_batching = enable_batching
        
        # Batching queue
        self._queue: List[WebhookPayload] = []
        self._queue_lock = threading.Lock()
        
        # Background executor
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        # Status tracking
        self._sync_history: List[Dict] = []
        self._failed_syncs: List[Dict] = []
        
        # Callbacks
        self._success_callbacks: List[Callable] = []
        self._failure_callbacks: List[Callable] = []
    
    def is_configured(self) -> bool:
        """Check if webhook is properly configured"""
        return bool(self.url)
    
    def register_success_callback(self, callback: Callable):
        """Register callback for successful syncs"""
        self._success_callbacks.append(callback)
    
    def register_failure_callback(self, callback: Callable):
        """Register callback for failed syncs"""
        self._failure_callbacks.append(callback)
    
    def _emit_success(self, payload: WebhookPayload):
        """Emit success to callbacks"""
        for callback in self._success_callbacks:
            try:
                callback(payload)
            except Exception as e:
                print(f"Success callback error: {e}")
    
    def _emit_failure(self, payload: WebhookPayload, error: str):
        """Emit failure to callbacks"""
        for callback in self._failure_callbacks:
            try:
                callback(payload, error)
            except Exception as e:
                print(f"Failure callback error: {e}")
    
    def _send_request(
        self,
        payload: WebhookPayload
    ) -> Dict:
        """Send HTTP request to Archon X"""
        if not self.is_configured():
            return {"status": "skipped", "reason": "Webhook not configured"}
        
        # Generate checksum
        if self.secret:
            payload.generate_checksum(self.secret)
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SYNTHIA-Webhook/4.2",
            "X-Agent-Name": payload.agent_name,
            "X-Event-Type": payload.event_type
        }
        
        data = payload.to_json().encode("utf-8")
        req = urllib.request.Request(
            self.url,
            data=data,
            headers=headers,
            method="POST"
        )
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    response_data = response.read().decode("utf-8")
                    return {
                        "status": "success",
                        "status_code": response.status,
                        "response": response_data
                    }
            except urllib.error.HTTPError as e:
                last_error = f"HTTP {e.code}: {e.reason}"
                if e.code >= 500 and attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
            except urllib.error.URLError as e:
                last_error = f"URL Error: {e.reason}"
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                last_error = str(e)
        
        return {"status": "failed", "error": last_error}
    
    def send(
        self,
        event_type: EventType,
        agent_name: str,
        data: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Send a webhook event to Archon X.
        
        Args:
            event_type: Type of event
            agent_name: Name of the agent sending
            data: Event data
            metadata: Optional metadata
            
        Returns:
            Result dictionary with status
        """
        payload = WebhookPayload(
            event_type=event_type.value,
            agent_name=agent_name,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            metadata=metadata or {}
        )
        
        if self.enable_batching:
            with self._queue_lock:
                self._queue.append(payload)
                if len(self._queue) >= self.batch_size:
                    return self._flush_queue()
            return {"status": "queued"}
        
        result = self._send_request(payload)
        
        # Track result
        self._sync_history.append({
            "timestamp": payload.timestamp,
            "event_type": event_type.value,
            "status": result["status"]
        })
        
        if result["status"] == "success":
            self._emit_success(payload)
        else:
            self._emit_failure(payload, result.get("error", "Unknown error"))
            self._failed_syncs.append({
                "payload": payload.to_json(),
                "error": result.get("error"),
                "timestamp": payload.timestamp
            })
        
        return result
    
    def _flush_queue(self) -> Dict:
        """Flush queued payloads"""
        with self._queue_lock:
            payloads = self._queue.copy()
            self._queue.clear()
        
        if not payloads:
            return {"status": "empty"}
        
        # Send batch
        batch_data = {
            "batch": True,
            "events": [json.loads(p.to_json()) for p in payloads]
        }
        
        batch_payload = WebhookPayload(
            event_type=EventType.KNOWLEDGE_SYNC.value,
            agent_name="synthia-core",
            timestamp=datetime.utcnow().isoformat(),
            data=batch_data
        )
        
        return self._send_request(batch_payload)
    
    def sync_task_completion(
        self,
        task_id: str,
        project_name: str,
        result: Dict[str, Any]
    ) -> Dict:
        """Sync task completion to Archon X"""
        return self.send(
            event_type=EventType.TASK_COMPLETE,
            agent_name="orchestrator",
            data={
                "task_id": task_id,
                "project_name": project_name,
                "result": result
            },
            metadata={
                "sync_type": "task_completion"
            }
        )
    
    def sync_knowledge(
        self,
        agent_name: str,
        task_id: str,
        result: Dict[str, Any]
    ) -> Dict:
        """Sync agent knowledge to Archon X"""
        return self.send(
            event_type=EventType.KNOWLEDGE_SYNC,
            agent_name=agent_name,
            data={
                "task_id": task_id,
                "knowledge": result
            },
            metadata={
                "sync_type": "knowledge"
            }
        )
    
    def send_heartbeat(
        self,
        agent_name: str,
        status: str,
        metrics: Optional[Dict] = None
    ) -> Dict:
        """Send agent heartbeat to Archon X"""
        return self.send(
            event_type=EventType.HEARTBEAT,
            agent_name=agent_name,
            data={
                "status": status,
                "metrics": metrics or {}
            },
            metadata={
                "sync_type": "heartbeat"
            }
        )
    
    def report_error(
        self,
        agent_name: str,
        error: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Report error to Archon X"""
        return self.send(
            event_type=EventType.ERROR_REPORT,
            agent_name=agent_name,
            data={
                "error": error,
                "context": context or {}
            },
            metadata={
                "sync_type": "error_report"
            }
        )
    
    def sync_memory_layer(
        self,
        layer: str,
        entries: List[Dict]
    ) -> Dict:
        """Sync entire memory layer to Archon X"""
        return self.send(
            event_type=EventType.MEMORY_STORE,
            agent_name="memory-manager",
            data={
                "layer": layer,
                "entries": entries,
                "count": len(entries)
            },
            metadata={
                "sync_type": "memory_layer"
            }
        )
    
    def get_sync_status(self) -> Dict:
        """Get sync status and statistics"""
        return {
            "configured": self.is_configured(),
            "url": self.url[:50] + "..." if self.url else None,
            "queue_size": len(self._queue),
            "total_syncs": len(self._sync_history),
            "failed_syncs": len(self._failed_syncs),
            "recent_syncs": self._sync_history[-10:]
        }
    
    def retry_failed(self) -> int:
        """Retry all failed syncs"""
        retried = 0
        failed_copy = self._failed_syncs.copy()
        self._failed_syncs.clear()
        
        for failed in failed_copy:
            try:
                payload_data = json.loads(failed["payload"])
                payload = WebhookPayload(
                    event_type=payload_data["event_type"],
                    agent_name=payload_data["agent_name"],
                    timestamp=payload_data["timestamp"],
                    data=payload_data["data"],
                    metadata=payload_data.get("metadata", {})
                )
                result = self._send_request(payload)
                if result["status"] == "success":
                    retried += 1
                else:
                    self._failed_syncs.append(failed)
            except Exception:
                self._failed_syncs.append(failed)
        
        return retried
    
    def flush(self) -> Dict:
        """Force flush all queued payloads"""
        return self._flush_queue()
    
    def shutdown(self):
        """Graceful shutdown - flush queue and stop executor"""
        self._flush_queue()
        self._executor.shutdown(wait=True)