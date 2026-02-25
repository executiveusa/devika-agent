"""Runtime configuration validation for production integrations."""

from dataclasses import dataclass
from typing import Dict, List

from src.config import Config


@dataclass
class ValidationResult:
    ok: bool
    errors: List[str]
    warnings: List[str]


def validate_runtime_config(strict: bool = False) -> ValidationResult:
    cfg = Config()
    errors: List[str] = []
    warnings: List[str] = []

    if not cfg.get_sqlite_db():
        errors.append("STORAGE.SQLITE_DB is required")

    if not cfg.get_projects_dir():
        errors.append("STORAGE.PROJECTS_DIR is required")

    brenner_endpoint = cfg.get_brenner_http_endpoint().strip()
    brenner_sim = cfg.get_brenner_simulate()
    if not brenner_sim and not brenner_endpoint:
        warnings.append("BRENNER_SIMULATE=false but API_ENDPOINTS.BRENNER_HTTP is not set")

    if cfg.get_ralphy_loop_enabled() and not cfg.get_dcg_enabled():
        warnings.append("RALPHY loop enabled while DCG is disabled; command safety may be reduced")

    # Validate optional binaries when configured.
    ms_bin = cfg.get_ms_binary().strip()
    mdwb_bin = cfg.get_mdwb_binary().strip()
    if ms_bin and " " in ms_bin and not ms_bin.startswith('"'):
        warnings.append("FEATURES.MS_BINARY contains spaces and may need quotes")
    if mdwb_bin and " " in mdwb_bin and not mdwb_bin.startswith('"'):
        warnings.append("FEATURES.MDWB_BINARY contains spaces and may need quotes")

    if strict and (errors or warnings):
        errors.extend([f"STRICT: {w}" for w in warnings])
        warnings = []

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings)
