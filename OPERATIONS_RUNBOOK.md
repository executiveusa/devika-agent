# Operations Runbook

## Deployment Gates
1. `python -m compileall src`
2. `pytest -q`
3. `python scripts/jobs/run_smoke_tests.py`
4. `python scripts/jobs/run_dependency_audit.py`

## Scheduler
- Start: `python scripts/jobs/run_scheduler.py`
- Heartbeat: `python scripts/jobs/run_heartbeat.py`
- Memory sync: `python scripts/jobs/run_memory_sync.py`
- Repo scan: `python scripts/jobs/run_repo_scan.py`

## Required Secrets
- `ARCHON_X_WEBHOOK_URL`
- `ARCHON_X_WEBHOOK_SECRET`
- `BRENNER_HTTP_URL` and `BRENNER_HTTP_TOKEN` (if Brenner is enabled)

## Rollback
1. Identify last known good commit: `git log --oneline -n 20`
2. Re-deploy previous tag/commit in environment.
3. Run smoke tests and confirm scheduler heartbeat and sync job success.

## Incident Response
- Adapter failures: inspect app logs and scheduled job output.
- Memory sync failures: run `python scripts/jobs/run_memory_sync.py --dry-run` to validate payload generation.
- Webhook outage: scheduler keeps running; investigate endpoint health and retry backlog.

## Credential Rotation
1. Rotate secret in provider.
2. Update CI secret.
3. Re-run heartbeat and memory sync jobs.
4. Confirm successful webhook responses.
