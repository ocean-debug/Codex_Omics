from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.io import load_json_or_simple_yaml  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a single-cell RNA-seq QC manifest or summary file.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--config")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    payload = load_json_or_simple_yaml(args.input)
    print(json.dumps({"input": args.input, "summary": payload.get("summary", payload)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
