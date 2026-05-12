from __future__ import annotations

import subprocess
import sys


def test_cli_help() -> None:
    completed = subprocess.run([sys.executable, "-m", "omics_codex", "--help"], text=True, capture_output=True, check=False)
    assert completed.returncode == 0
    assert "Codex Omics Skills CLI" in completed.stdout


def test_cli_validate_example() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "omics_codex", "validate", "--config", "examples/scrna_qc/omics_run_spec.yaml"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert '"valid": true' in completed.stdout


def test_cli_nfcore_verify_output(tmp_path) -> None:
    (tmp_path / "multiqc_report.html").write_text("<html></html>", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "omics_codex", "nfcore", "verify-output", "--pipeline", "rnaseq", "--outdir", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert '"has_multiqc": true' in completed.stdout


def test_cli_workflow_plan() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "omics_codex", "workflow", "plan", "--config", "examples/workflows/scrna_qc_scvi.yaml"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert '"skill": "omics-workflow"' in completed.stdout
