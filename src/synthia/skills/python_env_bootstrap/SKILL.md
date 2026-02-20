---
name: python_env_bootstrap
description: "Bootstrap a local Python virtual environment, install requirements, and optionally run tests. Use when setting up or repairing Python tooling in this repo. Trigger phrases: 'bootstrap python env', 'setup python environment', 'python env fix'."
---

# Python Env Bootstrap

Run the repository bootstrap script to set up `.venv`, install dependencies, and optionally run tests.

## Commands

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap_python_env.ps1
```

With tests:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap_python_env.ps1 -RunTests
```

## Notes

- Script fails fast if Python is not installed.
- Script is idempotent and reuses existing `.venv`.
