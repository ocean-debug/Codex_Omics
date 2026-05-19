from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.io import load_json_or_simple_yaml  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a single-cell marker/DE manifest.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    manifest = load_json_or_simple_yaml(args.manifest)
    summary = manifest.get("summary", {})
    result = {
        "skill": manifest.get("skill"),
        "status": manifest.get("status"),
        "outputs": manifest.get("outputs", {}),
        "groupby": summary.get("groupby"),
        "n_markers": summary.get("n_markers"),
        "top_markers": summary.get("top_markers", {}),
        "warnings": manifest.get("warnings", []),
    }
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
