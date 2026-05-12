from __future__ import annotations

import argparse
import json

from omics_codex.scvi.registry import inspect_model, list_models


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(required=True)
    sub.add_parser("list")
    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("model")
    args = parser.parse_args()
    payload = inspect_model(args.model) if hasattr(args, "model") else list_models()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
