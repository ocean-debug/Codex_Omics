from __future__ import annotations

import argparse
import json

from omics_codex.nfcore.schema_tools import fetch_pipeline_schema


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline", required=True)
    parser.add_argument("--version", default="latest")
    parser.add_argument("--out")
    args = parser.parse_args()
    path = fetch_pipeline_schema(args.pipeline, args.version, args.out)
    print(json.dumps({"schema": str(path)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
