from __future__ import annotations

import argparse
import json

from omics_codex.common.io import load_yaml_or_json
from omics_codex.scrna_qc.workflow import run_scrna_qc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    print(json.dumps(run_scrna_qc(load_yaml_or_json(args.config)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
