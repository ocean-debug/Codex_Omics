from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import detect_python_environment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Check pathway enrichment dependencies.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    parser.parse_args()
    result = {
        "status": "ready",
        "python_environment": detect_python_environment(),
        "python_packages": {},
        "blockers": [],
        "warnings": [],
        "install_hints": ["No extra packages are required for lightweight ORA."],
    }
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
