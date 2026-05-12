from __future__ import annotations

import argparse
import json

from omics_codex.common.io import load_yaml_or_json
from omics_codex.scvi.train import validate_scvi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    payload = validate_scvi(load_yaml_or_json(args.config))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
