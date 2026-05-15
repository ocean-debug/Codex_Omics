from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_router_generates_safe_nextflow_plan(tmp_path: Path) -> None:
    (tmp_path / "sample_R1.fastq.gz").write_text("", encoding="utf-8")
    (tmp_path / "sample_R2.fastq.gz").write_text("", encoding="utf-8")
    outdir = tmp_path / "route"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-router/scripts/route_omics.py",
            "--prompt",
            "run rnaseq workflow",
            "--input",
            str(tmp_path),
            "--outdir",
            str(outdir),
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["selected_skill"] == "nextflow-development"
    assert payload["approved"] is False
    assert payload["plan"]["approval_required"] is True


def test_report_renderer_from_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "run_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "skill": "single-cell-rna-qc",
                "status": "completed",
                "run_id": "test",
                "created_at": "now",
                "summary": {"before": {"n_cells": 10}, "after": {"n_cells": 8}, "removed_cells": 2, "counts_source": "X", "filter_mode": "mad"},
            }
        ),
        encoding="utf-8",
    )
    report = tmp_path / "report.md"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/omics-report/scripts/render_report.py",
            "--manifest",
            str(manifest),
            "--out",
            str(report),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    text = report.read_text(encoding="utf-8")
    assert "Cells before filtering" in text
    assert "Removed cells" in text


def test_install_planner_is_plan_only_by_default(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/scripts/common/install_planner.py",
            "--task",
            "scvi",
            "--output-dir",
            str(tmp_path),
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(completed.stdout)
    assert payload["approval_required"] is True
    assert payload["execution"]["executed"] is False
