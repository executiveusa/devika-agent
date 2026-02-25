"""Run repository scan and export report artifact."""

import json
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.synthia.investigation.repo_scanner import RepositoryScanner


def main() -> int:
    scanner = RepositoryScanner()
    result = scanner.scan(".")

    out_dir = Path("artifacts")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"repo-scan-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"

    with out_file.open("w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2)

    print(f"[repo-scan] wrote {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
