# Devika/SYNTHIA Production Hardening PRD

## 1. Purpose
Move `devika-agent-main` from sprint scaffolding to production-ready operation with:
- deterministic local bootstrap/build/test,
- enforced quality and security gates,
- real (not simulated) cross-repo integrations,
- repeatable deployment and observability.

## 2. Scope
In scope:
- Python backend (`src/`), SYNTHIA orchestration (`src/synthia/`), integration adapters (`src/integrations/`), job runners (`scripts/`), and CI workflows (`.github/workflows/`).
- Local build/test behavior and release gates.

Out of scope (for this PRD phase):
- Full UI redesign.
- Multi-repo code changes outside this repository.

## 3. Current State (Verified Locally)
Validated on this machine:
- `python -m compileall src`: passes.
- `pytest -q`: `70 passed, 1 skipped`.
- Python env bootstrap script runs and installs dependencies.

Fixes completed during this pass:
- Added logger fallback when `fastlogging` is unavailable: `src/logger.py`.
- Prevented Python 3.13 build break on `fastlogging`: `requirements.txt`.
- Fixed syntax bug in design pattern snippet: `src/synthia/design/awwwards.py`.
- Fixed syntax bug in niche profile palette definition: `src/synthia/investigation/niche_detector.py`.
- Stabilized cross-platform scanner test behavior (Windows permission semantics):
  - `skills/universal-skills-manager/tests/test_scan_skill.py`
  - `skills/universal-skills-manager/universal-skills-manager/scripts/scan_skill.py`

## 4. Gap Inventory (Feature-by-Feature)

### P0 (Must close before production)
1. CI scheduler still contains placeholder jobs and no real task execution:
- `.github/workflows/ci-scheduler.yml`
- Risk: false confidence; scheduled jobs do not perform heartbeat/scan/audit work.

2. Brenner integration defaults to simulated responses:
- `src/integrations/brenner_adapter/agent_mail.py`
- Risk: "deep reasoning" path appears active but does not perform real transport unless env vars are manually set.

3. Meta-skill client is still stubbed:
- `src/integrations/ms_client.py`
- Risk: planner/researcher skill enrichment is non-functional in production.

4. Markdown browser integration is wrapper-level only:
- `src/tools/markdown_browser.py`
- Risk: no deterministic external browser/runtime contract enforcement.

### P1 (Should close in hardening sprint)
1. Memory sync is dry-run-first and not connected to external sync targets:
- `src/synthia/jobs/memory_sync.py`

2. Scheduler wiring is minimal and lacks durable job registration/state:
- `src/synthia/jobs/scheduler.py`
- `scripts/jobs/run_scheduler.py`

3. Some service utility functions silently swallow exceptions:
- `src/services/utils.py`
- Risk: operational faults may be hidden.

4. Quality checks rely partly on synthetic/adaptive paths rather than deployment-grade external tooling contracts:
- `src/synthia/quality/*`
- `src/synthia/trainer/hooks.py`

### P2 (Operational maturity)
1. Expand test coverage beyond current focused tests for:
- ecosystem awareness lifecycle,
- Agent Mail contract compatibility,
- scheduler failover behavior,
- integration timeout/retry paths.

2. Add release SLO dashboards and runbook links.

## 5. Target Production Architecture

### 5.1 Runtime Contracts
- Agent orchestration: deterministic per-agent pre-execution guard via Ralphy loop.
- Integration contracts:
  - Brenner: HTTP transport with auth, timeout, retry, structured error class.
  - Agent Mail MCP: authenticated endpoint + schema validation.
  - MS client: real CLI/HTTP parser with non-empty returns and caching.

### 5.2 Scheduled Operations
Implement real jobs (not placeholders):
- Every 60s: heartbeat publish.
- Every 5-15m: memory sync flush.
- Daily: repo integrity scan report.
- Weekly: dependency and SAST audit.
- Push to `main`: smoke tests + ecosystem sync export.

### 5.3 Quality and Security Gates
Required release gates:
- `python -m compileall src`
- `pytest -q`
- dependency audit (`pip-audit`)
- static analysis (`bandit`, `semgrep`)
- no-secret policy checks on tracked files

## 6. Delivery Plan

### Phase 1: Integration Truthfulness
- Replace simulated-only code paths with real adapters + explicit disabled-state responses.
- Add strict config validation and startup checks for required integration keys.

### Phase 2: Scheduled Reliability
- Wire real job handlers for heartbeat/memory sync/repo scan.
- Persist job state and expose health endpoint.

### Phase 3: CI/CD Enforcement
- Replace placeholder echo steps in `.github/workflows/ci-scheduler.yml` with executable scripts.
- Upload artifacts for scans/audits and fail on threshold breaches.

### Phase 4: Observability + Runbooks
- Add structured logs and error taxonomy for all adapter failures.
- Add docs for incident handling, rollback, and credential rotation.

## 7. Acceptance Criteria
Production-ready is achieved when all are true:
1. No placeholder/simulated primary execution path in production mode.
2. All scheduled jobs run real logic and produce verifiable outputs.
3. CI fails correctly on tests, compile, security, and audit regressions.
4. Cross-repo awareness payloads are contract-validated and replay-safe.
5. Full test suite passes in CI and local bootstrap path is deterministic.

## 8. Security Notes
- Do not store PATs/tokens in code, logs, committed config, or branch URLs.
- Continue using local env/secret manager for credentials.
- Keep rotating any credential previously exposed in chat or shell history.
