"""Scheduler manager for SYNTHIA background jobs.

This module provides a scheduler for running background jobs like
heartbeats, memory sync, repository scans, and other periodic tasks.

Environment Variables:
    SYNTHIA_SCHEDULER_DB_PATH: Path to scheduler database (default: data/scheduler/jobs.sqlite)
    SYNTHIA_HEARTBEAT_INTERVAL: Heartbeat interval in seconds (default: 300)
    SYNTHIA_MEMORY_SYNC_INTERVAL: Memory sync interval in seconds (default: 3600)
    SYNTHIA_REPO_SCAN_INTERVAL: Repo scan interval in seconds (default: 86400)
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobEvent
from typing import Callable, Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import atexit
import logging
import os
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Status of a scheduled job."""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class JobResult:
    """Result of a job execution."""
    job_id: str
    status: JobStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Any = None
    
    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "result": self.result,
        }


@dataclass
class JobInfo:
    """Information about a scheduled job."""
    id: str
    name: str
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    next_run: Optional[datetime] = None
    last_result: Optional[JobResult] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "interval_seconds": self.interval_seconds,
            "cron_expression": self.cron_expression,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_result": self.last_result.to_dict() if self.last_result else None,
        }


class SchedulerManager:
    """Scheduler manager using APScheduler for background jobs.
    
    This manager provides:
    - Interval-based job scheduling
    - Cron-based job scheduling
    - Job result tracking
    - Error handling and logging
    - Pre-configured SYNTHIA job handlers
    
    Example:
        scheduler = SchedulerManager()
        scheduler.register_default_jobs()
        scheduler.start()
        
        # Check health
        health = scheduler.health()
        print(f"Running: {health['running']}, Jobs: {len(health['jobs'])}")
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the scheduler manager.
        
        Args:
            db_path: Path to SQLite database for job persistence.
        """
        self.db_path = db_path or os.environ.get(
            "SYNTHIA_SCHEDULER_DB_PATH",
            "data/scheduler/jobs.sqlite"
        )
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self._sched = BackgroundScheduler(
            jobstores={"default": SQLAlchemyJobStore(url=f"sqlite:///{self.db_path}")}
        )
        self._results: Dict[str, JobResult] = {}
        self._handlers: Dict[str, Callable] = {}
        
        # Register event listeners
        self._sched.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self._sched.add_listener(self._on_job_error, EVENT_JOB_ERROR)
    
    def _on_job_executed(self, event: JobEvent) -> None:
        """Handle job execution success."""
        job_id = event.job_id
        self._results[job_id] = JobResult(
            job_id=job_id,
            status=JobStatus.SUCCESS,
            completed_at=datetime.utcnow(),
            result=event.retval,
        )
        logger.debug(f"Job {job_id} executed successfully")
    
    def _on_job_error(self, event: JobEvent) -> None:
        """Handle job execution error."""
        job_id = event.job_id
        error_msg = str(event.exception) if event.exception else "Unknown error"
        self._results[job_id] = JobResult(
            job_id=job_id,
            status=JobStatus.FAILED,
            completed_at=datetime.utcnow(),
            error=error_msg,
        )
        logger.error(f"Job {job_id} failed: {error_msg}")
    
    def register_handler(self, job_id: str, handler: Callable) -> None:
        """Register a job handler function.
        
        Args:
            job_id: Unique identifier for the job.
            handler: Callable to execute when job runs.
        """
        self._handlers[job_id] = handler
        logger.debug(f"Registered handler for job: {job_id}")
    
    def add_interval_job(
        self,
        func: Callable[..., Any],
        seconds: int = 60,
        job_id: str = "",
        name: str = "",
        **kwargs
    ) -> str:
        """Add an interval-based job.
        
        Args:
            func: Function to execute.
            seconds: Interval in seconds.
            job_id: Unique job identifier.
            name: Human-readable job name.
            **kwargs: Additional arguments to pass to func.
            
        Returns:
            The job ID.
        """
        job_id = job_id or f"interval_{seconds}_{func.__name__}"
        name = name or func.__name__
        
        self._sched.add_job(
            func,
            IntervalTrigger(seconds=seconds),
            kwargs=kwargs,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
            id=job_id,
            name=name,
            replace_existing=True,
        )
        
        self.register_handler(job_id, func)
        logger.info(f"Added interval job: {job_id} (every {seconds}s)")
        return job_id
    
    def add_cron_job(
        self,
        func: Callable[..., Any],
        cron_expression: str,
        job_id: str = "",
        name: str = "",
        **kwargs
    ) -> str:
        """Add a cron-based job.
        
        Args:
            func: Function to execute.
            cron_expression: Cron expression (e.g., "0 2 * * *" for 2 AM daily).
            job_id: Unique job identifier.
            name: Human-readable job name.
            **kwargs: Additional arguments to pass to func.
            
        Returns:
            The job ID.
        """
        job_id = job_id or f"cron_{cron_expression.replace(' ', '_')}_{func.__name__}"
        name = name or func.__name__
        
        # Parse cron expression
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expression}")
        
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )
        
        self._sched.add_job(
            func,
            trigger,
            kwargs=kwargs,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
            id=job_id,
            name=name,
            replace_existing=True,
        )
        
        self.register_handler(job_id, func)
        logger.info(f"Added cron job: {job_id} ({cron_expression})")
        return job_id
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job.
        
        Args:
            job_id: The job ID to remove.
            
        Returns:
            True if job was removed, False if not found.
        """
        try:
            self._sched.remove_job(job_id)
            if job_id in self._handlers:
                del self._handlers[job_id]
            if job_id in self._results:
                del self._results[job_id]
            logger.info(f"Removed job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove job {job_id}: {e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job.
        
        Args:
            job_id: The job ID to pause.
            
        Returns:
            True if job was paused, False if not found.
        """
        try:
            self._sched.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to pause job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job.
        
        Args:
            job_id: The job ID to resume.
            
        Returns:
            True if job was resumed, False if not found.
        """
        try:
            self._sched.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to resume job {job_id}: {e}")
            return False
    
    def run_job_now(self, job_id: str) -> bool:
        """Trigger a job to run immediately.
        
        Args:
            job_id: The job ID to run.
            
        Returns:
            True if job was triggered, False if not found.
        """
        try:
            self._sched.modify_job(job_id, next_run_time=datetime.utcnow())
            logger.info(f"Triggered immediate run for job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to trigger job {job_id}: {e}")
            return False
    
    def start(self) -> None:
        """Start the scheduler."""
        if not self._sched.running:
            self._sched.start()
            atexit.register(self.shutdown)
            logger.info("Scheduler started")
    
    def shutdown(self, wait: bool = False) -> None:
        """Shutdown the scheduler.
        
        Args:
            wait: If True, wait for running jobs to complete.
        """
        try:
            self._sched.shutdown(wait=wait)
            logger.info("Scheduler shutdown complete")
        except Exception as exc:
            logger.warning(f"Scheduler shutdown warning: {exc}")
    
    def health(self) -> Dict:
        """Get scheduler health status.
        
        Returns:
            Dictionary with scheduler status and job information.
        """
        jobs = []
        for job in self._sched.get_jobs():
            job_info = JobInfo(
                id=job.id,
                name=job.name or job.id,
                next_run=job.next_run_time,
                last_result=self._results.get(job.id),
            )
            jobs.append(job_info.to_dict())
        
        return {
            "running": self._sched.running,
            "job_count": len(jobs),
            "jobs": jobs,
        }
    
    def get_job_info(self, job_id: str) -> Optional[JobInfo]:
        """Get information about a specific job.
        
        Args:
            job_id: The job ID.
            
        Returns:
            JobInfo if found, None otherwise.
        """
        job = self._sched.get_job(job_id)
        if not job:
            return None
        
        return JobInfo(
            id=job.id,
            name=job.name or job.id,
            next_run=job.next_run_time,
            last_result=self._results.get(job.id),
        )
    
    def register_default_jobs(self) -> None:
        """Register default SYNTHIA background jobs.
        
        This includes:
        - Heartbeat: Periodic agent heartbeat
        - Memory sync: Sync memory to external targets
        - Repo scan: Periodic repository scanning
        """
        # Import handlers here to avoid circular imports
        from .memory_sync import MemorySync
        
        # Heartbeat job
        heartbeat_interval = int(os.environ.get("SYNTHIA_HEARTBEAT_INTERVAL", "300"))
        self.add_interval_job(
            func=self._heartbeat_handler,
            seconds=heartbeat_interval,
            job_id="synthia_heartbeat",
            name="SYNTHIA Heartbeat",
        )
        
        # Memory sync job
        memory_sync_interval = int(os.environ.get("SYNTHIA_MEMORY_SYNC_INTERVAL", "3600"))
        self.add_interval_job(
            func=self._memory_sync_handler,
            seconds=memory_sync_interval,
            job_id="synthia_memory_sync",
            name="SYNTHIA Memory Sync",
        )
        
        # Repo scan job (daily by default)
        repo_scan_interval = int(os.environ.get("SYNTHIA_REPO_SCAN_INTERVAL", "86400"))
        self.add_interval_job(
            func=self._repo_scan_handler,
            seconds=repo_scan_interval,
            job_id="synthia_repo_scan",
            name="SYNTHIA Repository Scan",
        )
        
        logger.info("Registered default SYNTHIA jobs")
    
    def _heartbeat_handler(self) -> Dict:
        """Handle heartbeat job."""
        try:
            from src.synthia.webhook import ArchonXWebhook
            webhook = ArchonXWebhook()
            
            if not webhook.is_configured():
                logger.debug("Heartbeat: webhook not configured, skipping")
                return {"status": "skipped", "reason": "webhook not configured"}
            
            result = webhook.send_heartbeat("synthia-agent")
            logger.debug(f"Heartbeat sent: {result.get('status')}")
            return result
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _memory_sync_handler(self) -> Dict:
        """Handle memory sync job."""
        try:
            from .memory_sync import MemorySync
            sync = MemorySync()
            
            if not sync.is_configured():
                logger.debug("Memory sync: no targets configured, skipping")
                return {"status": "skipped", "reason": "no targets configured"}
            
            result = sync.sync()
            logger.debug(f"Memory sync completed: {result.status.value}")
            return result.to_dict()
        except Exception as e:
            logger.error(f"Memory sync failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _repo_scan_handler(self) -> Dict:
        """Handle repository scan job."""
        try:
            from src.synthia.investigation.repo_scanner import RepositoryScanner
            scanner = RepositoryScanner()
            
            # Scan current directory
            result = scanner.scan(".")
            logger.debug(f"Repo scan completed: {result.summary}")
            return result.to_dict()
        except Exception as e:
            logger.error(f"Repo scan failed: {e}")
            return {"status": "error", "error": str(e)}


# Default instance for convenience
scheduler = SchedulerManager()
