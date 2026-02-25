## Production Sprint Plan (Reset 2026-02-22)

Goal: finish PRD phases end-to-end with deterministic local build/test and CI-enforced jobs.

### Phase 1 - Close P0 integration gaps
1. Normalize adapter contracts for Brenner/MS/MarkdownBrowser.
2. Ensure startup config validation is wired and non-breaking in non-strict mode.
3. Align tests with current dataclass-return APIs.

### Phase 2 - Harden jobs and scheduler
1. Fix script/job result handling (no dict-vs-dataclass mismatches).
2. Ensure scheduler jobs are safe when webhook/repo scanner targets are unavailable.
3. Persist scan/audit artifacts under `artifacts/`.

### Phase 3 - CI gates and release quality
1. Keep CI jobs executable (no placeholders).
2. Enforce compile + smoke + targeted tests.
3. Keep weekly audit and nightly scan deterministic.

### Phase 4 - Verify, commit, push
1. Run full local verify suite.
2. Update beads summary/todo with final status.
3. Commit and push to `main`.