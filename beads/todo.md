# Sprint Todo (snapshot — updated 2026-02-17)

- [x] Clone or initialize repository (create git, add remote) — done: git init + remote added
- [x] Read key docs and prompt templates to scope changes — done: full gap analysis
- [x] Integrate ACIP (prompt-injection checker) as pre-checker — done: src/security/acip_integration.py, wired in llm.py, config-flagged
- [x] Integrate DCG (destructive command guard) around runner/sandbox — done: src/sandbox/dcg_wrapper.py, wired in runner.py, config-flagged
- [x] Integrate `ms` (Meta Skill) as skill store / MCP client — done: src/integrations/ms_client.py, wired in planner.py
- [x] Add `mdwb` (markdown_web_browser) browsing tool and provenance — done: src/tools/markdown_browser.py, wired in researcher.py with ACIP gate
- [x] Scaffold code changes and update prompt templates/agents — done: all agents updated, config flags added, packages have __init__.py
- [x] Create agents-toolbox.md master reference — done
- [ ] Run unit/integration tests and fix failures — BLOCKED: Python not available in runner env; push to remote and let CI run
- [x] Commit and push changes to `main` — in progress
