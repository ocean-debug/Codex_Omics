from __future__ import annotations

import argparse
import json

from omics_codex.nfcore.registry import inspect_pipeline, list_pipelines


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(required=True)
    sub.add_parser("list")
    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("pipeline")
    args = parser.parse_args()
    if hasattr(args, "pipeline"):
        payload = inspect_pipeline(args.pipeline)
    else:
        payload = list_pipelines()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
