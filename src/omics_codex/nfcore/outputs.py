from __future__ import annotations

from pathlib import Path
from typing import Any


def verify_generic_outputs(outdir: str | Path) -> dict[str, Any]:
    root = Path(outdir)
    multiqc = list(root.rglob("*multiqc_report.html")) if root.exists() else []
    return {
        "outdir": str(root),
        "exists": root.exists(),
        "multiqc_reports": [str(path) for path in multiqc],
        "file_count": sum(1 for path in root.rglob("*") if path.is_file()) if root.exists() else 0,
    }


def verify_pipeline_outputs(pipeline: str, outdir: str | Path) -> dict[str, Any]:
    short = pipeline.replace("nf-core/", "").lower()
    inventory = verify_generic_outputs(outdir)
    root = Path(outdir)
    expected_patterns = {
        "rnaseq": ["multiqc_report.html", "star_salmon", "salmon", "featurecounts"],
        "atacseq": ["multiqc_report.html", "bwa", "macs2", "consensus_peaks"],
        "sarek": ["multiqc_report.html", "variant_calling", "preprocessing", "reports"],
    }.get(short, ["multiqc_report.html"])
    matches: dict[str, list[str]] = {}
    if root.exists():
        for pattern in expected_patterns:
            matches[pattern] = [str(path) for path in root.rglob(f"*{pattern}*")]
    inventory.update(
        {
            "pipeline": f"nf-core/{short}",
            "expected_patterns": expected_patterns,
            "matches": matches,
            "has_multiqc": bool(inventory["multiqc_reports"]),
        }
    )
    return inventory
