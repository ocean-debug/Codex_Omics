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


def test_cli_route_generates_safe_workflow(tmp_path) -> None:
    (tmp_path / "sample_R1.fastq.gz").write_text("", encoding="utf-8")
    (tmp_path / "sample_R2.fastq.gz").write_text("", encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "omics_codex",
            "route",
            "--prompt",
            "Create a bulk RNA workflow",
            "--input",
            str(tmp_path),
            "--outdir",
            str(tmp_path / "results"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert '"approved": false' in completed.stdout
    assert '"name": "rnaseq_workflow"' in completed.stdout


def test_cli_template_list() -> None:
    completed = subprocess.run([sys.executable, "-m", "omics_codex", "template", "list"], text=True, capture_output=True, check=False)
    assert completed.returncode == 0
    assert '"bulk-rna"' in completed.stdout
    assert '"scrna-qc-scvi"' in completed.stdout
