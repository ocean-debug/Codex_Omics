from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.io import write_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize nf-core MultiQC data for reports.")
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--out")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = summarize_multiqc(Path(args.outdir))
    if args.out:
        write_json(args.out, result)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


def summarize_multiqc(outdir: Path) -> dict[str, Any]:
    candidates = sorted(outdir.glob("**/multiqc_data/multiqc_data.json"))
    if not candidates:
        return {
            "status": "missing",
            "multiqc_data": None,
            "summary": {},
            "interpretation": ["MultiQC data JSON was not found; inspect pipeline logs and output directories manually."],
        }
    source = candidates[0]
    try:
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"status": "error", "multiqc_data": str(source), "summary": {}, "interpretation": [f"Could not parse MultiQC data: {exc}"]}

    report_general = payload.get("report_general_stats_data", [])
    sections = payload.get("report_saved_raw_data", {})
    module_names = sorted({str(key).split("_")[0] for key in sections.keys()})
    n_samples = 0
    if isinstance(report_general, list) and report_general:
        first = report_general[0]
        if isinstance(first, dict):
            n_samples = len(first)
    summary = {
        "multiqc_data": str(source),
        "general_stats_blocks": len(report_general) if isinstance(report_general, list) else 0,
        "samples_in_general_stats": n_samples,
        "module_count": len(module_names),
        "modules": module_names[:50],
    }
    interpretation = [
        f"MultiQC data were parsed from {source}.",
        f"Detected {summary['module_count']} MultiQC module groups and {summary['samples_in_general_stats']} samples in general stats.",
    ]
    return {"status": "ok", "multiqc_data": str(source), "summary": summary, "interpretation": interpretation}


if __name__ == "__main__":
    raise SystemExit(main())
