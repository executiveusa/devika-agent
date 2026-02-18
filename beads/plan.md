## YOLO Sprint Plan — Integrate Flywheel Prompts, Agents, and Tools

Constraint: All integrations must be implemented inside the existing `devika-agent-main` repository — no new external repositories will be created. External tools (e.g., `ms`, `mdwb`) may be invoked via their CLI/binaries but any glue code must live in this repo.

TL;DR - What/Why/How
- What: Integrate flywheel prompts, safety (ACIP/DCG), skill registry (`ms`), and `markdown_web_browser` into Devika.
- Why: Improve agent safety, multi-agent coordination, deterministic browsing provenance, and make reusable skills available for planning/coding.
- How: Add scaffolding modules, update agent prompt flows, gate all OS-level actions with DCG, add ACIP pre-send checks, and expose `ms` and `mdwb` via local wrappers.

Steps
1. Initialize local git workspace (in-place) and create feature branch if desired.
2. Read prompts and templates (`src/agents/*/prompt.jinja2`, `devika.py`, `src/llm/*`, `src/memory/*`).
3. Implement ACIP prompt-checker: `src/security/acip_integration.py` and call from `src/llm/*` before sending requests.
4. Implement DCG wrapper: `src/sandbox/dcg_wrapper.py` and gate runner/patcher execution.
5. Implement `ms` client: `src/integrations/ms_client.py` for skill lookup and progressive disclosure.
6. Implement mdwb wrapper: `src/tools/markdown_browser.py` for deterministic page capture + provenance ingestion.
7. Update prompts to call skill lookup & safety checks.
8. Add tests and run smoke/integration checks.
9. Commit, push, and merge per YOLO sprint rules (permitted).

Files to create/modify (first pass)
- Create: `src/security/acip_integration.py`
- Create: `src/sandbox/dcg_wrapper.py`
- Create: `src/integrations/ms_client.py`
- Create: `src/tools/markdown_browser.py`
- Modify: `src/llm/llm.py`, `src/llm/*_client.py` (call ACIP)
- Modify: `src/agents/runner/runner.py`, `src/agents/patcher/patcher.py` (call DCG)
- Modify: `src/agents/planner/planner.py`, `src/agents/coder/coder.py`, `src/agents/researcher/researcher.py` (call `ms_client`/`markdown_browser`)
- Modify: `devika.py` to wire DCG/config toggles

Verification
- Unit tests for new modules (pytest)
- Smoke test: start server and run an end-to-end prompt
- Safety test: simulate destructive command and confirm DCG blocks it

Next: begin implementing ACIP scaffold and DCG adapter (first files).