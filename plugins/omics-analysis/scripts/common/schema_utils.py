from __future__ import annotations

import argparse
import json

from omics_codex.common.io import load_yaml_or_json
from omics_codex.common.schema import validate_payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True, choices=["omics_run_spec", "run_manifest"])
    parser.add_argument("--payload", required=True)
    args = parser.parse_args()
    errors = validate_payload(load_yaml_or_json(args.payload), args.schema)
    print(json.dumps({"valid": not errors, "errors": errors}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
