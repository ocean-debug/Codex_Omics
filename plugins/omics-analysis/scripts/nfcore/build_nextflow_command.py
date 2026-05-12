from __future__ import annotations

import argparse
import json

from omics_codex.common.io import load_yaml_or_json
from omics_codex.nfcore.command import build_nextflow_command


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    command = build_nextflow_command(load_yaml_or_json(args.config))
    print(json.dumps({"command": command}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
