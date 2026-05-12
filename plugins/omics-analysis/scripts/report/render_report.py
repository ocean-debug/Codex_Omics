from __future__ import annotations

import argparse
import json

from omics_codex.report import write_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()
    path = write_report(args.manifest, args.out)
    print(json.dumps({"report": str(path)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
