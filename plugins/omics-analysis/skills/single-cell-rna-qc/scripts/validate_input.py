from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))


def validate_input(path: Path) -> dict[str, object]:
    suffix = "".join(path.suffixes).lower()
    supported = suffix.endswith(".h5ad") or suffix.endswith(".h5") or path.is_dir()
    return {
        "input": str(path),
        "exists": path.exists(),
        "supported": bool(path.exists() and supported),
        "format": "h5ad" if suffix.endswith(".h5ad") else ("10x_h5" if suffix.endswith(".h5") else ("10x_mtx_dir" if path.is_dir() else "unknown")),
        "errors": [] if path.exists() and supported else [{"error_type": "UnsupportedInput", "message": "Use .h5ad, 10x .h5, or a 10x MTX directory."}],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a single-cell RNA-seq QC input path.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--config")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate_input(Path(args.input)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
