---
name: brenner-skill
description: "Brenner Bot deep-reasoning skill. Trigger with 'brenner:deepreason'. Use when agents need a live, streamed deep-reasoning session or artifact compilation assistance."
---

# Brenner Skill

This skill provides a bridge to the Brenner Bot deep-reasoning flow. It should be triggered by the exact prefix `brenner:deepreason` in agent prompts. The skill is safe-by-default: calls are simulated when the underlying integration is not enabled in `config.toml`.

See `src/integrations/brenner_adapter/` for adapter internals and `data/brenner/` for `heart.json` / `soul.json` artifacts.
