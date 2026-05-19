from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = Path(__file__).resolve().parents[3]


REQUIRED_CHILD_SCRIPTS = {
    "single-cell-rna-qc": "skills/single-cell-rna-qc/scripts/qc_analysis.py",
    "single-cell-preprocess": "skills/single-cell-preprocess/scripts/run.py",
    "single-cell-integration": "skills/single-cell-integration/scripts/run.py",
    "single-cell-annotation": "skills/single-cell-annotation/scripts/run.py",
    "single-cell-marker-de": "skills/single-cell-marker-de/scripts/run.py",
    "pathway-enrichment": "skills/pathway-enrichment/scripts/run.py",
    "omics-report": "skills/omics-report/scripts/render_report.py",
}


def inspect_workflow_environment() -> dict[str, Any]:
    missing = []
    scripts = {}
    for skill, relative in REQUIRED_CHILD_SCRIPTS.items():
        path = PLUGIN_ROOT / relative
        scripts[skill] = {"path": str(path), "exists": path.exists()}
        if not path.exists():
            missing.append({"error_type": "MissingChildScript", "skill": skill, "path": relative, "message": f"Missing child script for {skill}."})
    return {
        "status": "blocked" if missing else "ready",
        "skill_root": str(SKILL_ROOT),
        "plugin_root": str(PLUGIN_ROOT),
        "child_scripts": scripts,
        "blockers": missing,
        "warnings": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check scRNA standard workflow planning prerequisites.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    parser.parse_args()
    print(json.dumps(inspect_workflow_environment(), indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
