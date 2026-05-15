from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.report import write_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Codex-Omics report from a run manifest.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out")
    parser.add_argument("--title", default="Codex-Omics Report")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    out = Path(args.out) if args.out else manifest_path.with_name("report.md")
    write_report(out, manifest, title=args.title)
    result = {"status": "ok", "report": str(out), "manifest": str(manifest_path)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
