from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_scrna_qc_dry_run_writes_manifest(tmp_path: Path) -> None:
    input_path = tmp_path / "cells.h5ad"
    input_path.write_text("", encoding="utf-8")
    outdir = tmp_path / "out"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(outdir),
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["skill"] == "single-cell-rna-qc"
    assert manifest["status"] in {"planned", "blocked"}
    assert (outdir / "report.md").exists()


def test_single_cell_preprocess_dry_run_writes_manifest(tmp_path: Path) -> None:
    input_path = tmp_path / "filtered.h5ad"
    input_path.write_text("", encoding="utf-8")
    outdir = tmp_path / "preprocess"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/single-cell-preprocess/scripts/run.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(outdir),
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["skill"] == "single-cell-preprocess"
    assert manifest["status"] in {"planned", "blocked"}
    assert "preprocessed.h5ad" in manifest.get("plan", {}).get("will_write", []) or manifest["status"] == "blocked"
    assert (outdir / "report.md").exists()
