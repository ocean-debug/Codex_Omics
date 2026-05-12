from __future__ import annotations

import argparse
import json

from omics_codex.common.environment import inspect_environment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", default="all", choices=["all", "nfcore", "scrna_qc", "scvi"])
    args = parser.parse_args()
    print(json.dumps(inspect_environment(args.kind), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
