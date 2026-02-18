"""Run a one-off scheduler instance for local testing."""
from src.synthia.jobs.scheduler import SchedulerManager
import time
import logging

logging.basicConfig(level=logging.INFO)


def sample_job(message: str = "heartbeat"):
    print(f"[scheduler] job executed: {message}")


def main():
    sched = SchedulerManager()
    sched.add_interval_job(sample_job, seconds=5, message="heartbeat")
    sched.start()

    try:
        # run for 15 seconds then exit
        time.sleep(15)
    finally:
        sched.shutdown()


if __name__ == "__main__":
    main()
