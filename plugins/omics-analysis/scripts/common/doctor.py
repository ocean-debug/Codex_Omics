from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from omics_codex.common.environment import doctor_environment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", default="all", choices=["all", "nfcore", "scrna_qc", "scvi"])
    args = parser.parse_args()
    os.environ.setdefault("CODEX_OMICS_PLUGIN_ROOT", str(Path(__file__).resolve().parents[2]))
    print(json.dumps(doctor_environment(args.kind), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
