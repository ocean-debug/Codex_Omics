from __future__ import annotations

import argparse

from omics_codex.common.io import load_yaml_or_json
from omics_codex.common.manifest import write_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    write_manifest(args.out, load_yaml_or_json(args.manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
