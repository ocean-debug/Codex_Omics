from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import inspect_scrna_qc_environment  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Check single-cell RNA-seq QC dependencies.")
    parser.add_argument("--config", help="Accepted for a uniform skill-local interface.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--dry-run", action="store_true", help="Accepted for a uniform skill-local interface.")
    parser.add_argument("--approved", default="false", help="Accepted for a uniform skill-local interface.")
    parser.add_argument("--write-manifest", action="store_true", help="Accepted for a uniform skill-local interface.")
    parser.parse_args()
    print(json.dumps(inspect_scrna_qc_environment(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
