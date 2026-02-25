Human Summary

- Goal: Find flywheel/agent/prompt/memory/safety resources and integrate them into Devika to make a powerful, safe, multi-agent coding assistant.
- Top candidates to integrate: `claude_code_agent_farm`, `acip` (Advanced Cognitive Inoculation Prompt), `meta_skill` (`ms`), `markdown_web_browser` (`mdwb`), `destructive_command_guard` (DCG), `mcp_agent_mail`, `cass_memory_system`.

Key Recommendations
- Add an ACIP pre-check stage before any prompt is sent to an LLM. Use hybrid (fast-check + optional full audit).
- Add DCG gating around all OS/terminal actions and require approvals for destructive operations.
- Integrate `ms` as a local skill registry (MCP client or CLI wrapper) and consult it in `planner` and `coder` agents.
- Expose `mdwb` as a deterministic browser + provenance tool for the `researcher` agent; treat tool output as untrusted and pass through ACIP.
- Adopt safe farm/orchestration patterns (file locks, staggered start, restart limits) if running parallel agents.

Local Devika integration points (examples)
- Prompts: `src/agents/*/prompt.jinja2`
- LLM send: `src/llm/llm.py` and provider clients
- Runner/Patcher: `src/agents/runner/*`, `src/agents/patcher/*`
- Config toggles: `src/config.py`

No explicit `openclaw` training artifacts were found — recommend targeted search in remote repos for that term.

Latest Sprint Outcome (2026-02-25)
- Implemented production compatibility fixes for Brenner/MS/MarkdownBrowser integrations.
- Fixed job-runner import path issues so scripts run directly from repo root with `python scripts/jobs/...`.
- Fixed strategic planner runtime enum mismatches that blocked repo scan execution.
- Verified job runners:
	- `run_heartbeat.py` graceful when webhook is not configured.
	- `run_memory_sync.py --dry-run` returns structured status.
	- `run_repo_scan.py` writes artifact under `artifacts/`.
- Full verification completed: `73 passed, 1 skipped`.
