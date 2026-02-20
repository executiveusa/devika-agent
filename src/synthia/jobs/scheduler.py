from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Callable, Any
import atexit
import logging

logger = logging.getLogger(__name__)


class SchedulerManager:
    """Simple scheduler manager using APScheduler for local development."""

    def __init__(self):
        self._sched = BackgroundScheduler()

    def add_interval_job(self, func: Callable[..., Any], seconds: int = 60, **kwargs):
        self._sched.add_job(
            func,
            IntervalTrigger(seconds=seconds),
            kwargs=kwargs,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
        )

    def start(self):
        if not self._sched.running:
            self._sched.start()
            atexit.register(self.shutdown)
            logger.info("Scheduler started")

    def shutdown(self):
        try:
            self._sched.shutdown(wait=False)
        except Exception as exc:
            logger.warning("Scheduler shutdown warning: %s", exc)
