from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import gzip
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_runner(root: Path, project: str, body: str) -> None:
    script = root / "scripts" / "acceptance" / f"run_{project}.sh"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + body, encoding="utf-8")


def _completed_runner(project: str) -> str:
    return f"""
OUT="${{CODEX_OMICS_RESULT_DIR}}/{project}"
mkdir -p "${{OUT}}"
cat > "${{OUT}}/run_manifest.json" <<'JSON'
{{"status": "completed", "errors": [], "outputs": {{"command": "command.sh"}}, "commands": ["echo ok"], "logs": []}}
JSON
"""


def _run_all(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    fake_root = tmp_path / "fake_root"
    result_dir = tmp_path / "result"
    data_dir = tmp_path / "data"
    env = {
        "CODEX_OMICS_ROOT": str(fake_root),
        "CODEX_OMICS_DATA_DIR": str(data_dir),
        "CODEX_OMICS_RESULT_DIR": str(result_dir),
    }
    command = ["bash", str(REPO_ROOT / "scripts" / "acceptance" / "run_all.sh")]
    return subprocess.run(command, cwd=REPO_ROOT, env={**os.environ, **env}, text=True, capture_output=True, check=False)


@pytest.mark.skipif(os.name == "nt" or shutil.which("bash") is None, reason="bash on POSIX paths is required for acceptance script tests")
def test_run_all_allows_classified_atac_pipeline_failure(tmp_path: Path) -> None:
    fake_root = tmp_path / "fake_root"
    _write_runner(fake_root, "scvi", _completed_runner("scvi"))
    _write_runner(fake_root, "bulk_rna", _completed_runner("bulk_rna"))
    _write_runner(
        fake_root,
        "atac",
        """
OUT="${CODEX_OMICS_RESULT_DIR}/atac"
mkdir -p "${OUT}"
cat > "${OUT}/run_manifest.json" <<'JSON'
{
  "status": "failed",
  "errors": [
    {
      "error_type": "PipelineConfigParseFailed",
      "details": {"classification": "pipeline_config_parse"}
    }
  ],
  "outputs": {"command": "command.sh"},
  "commands": ["nextflow run nf-core/atacseq"],
  "logs": ["nextflow.stderr.log"]
}
JSON
exit 1
""",
    )

    completed = _run_all(tmp_path)

    assert completed.returncode == 0, completed.stderr + completed.stdout
    summary = json.loads((tmp_path / "result" / "summary.json").read_text(encoding="utf-8"))
    assert summary["exit_policy"]["status"] == "passed"
    assert summary["atac"]["allowed_failure"] is True


@pytest.mark.skipif(os.name == "nt" or shutil.which("bash") is None, reason="bash on POSIX paths is required for acceptance script tests")
def test_run_all_returns_nonzero_when_required_project_fails(tmp_path: Path) -> None:
    fake_root = tmp_path / "fake_root"
    _write_runner(fake_root, "scvi", _completed_runner("scvi"))
    _write_runner(fake_root, "bulk_rna", "mkdir -p \"${CODEX_OMICS_RESULT_DIR}/bulk_rna\"\nexit 7\n")
    _write_runner(fake_root, "atac", _completed_runner("atac"))

    completed = _run_all(tmp_path)

    assert completed.returncode == 1
    summary = json.loads((tmp_path / "result" / "summary.json").read_text(encoding="utf-8"))
    assert summary["exit_policy"]["status"] == "failed"
    assert any(failure["project"] == "bulk_rna" for failure in summary["exit_policy"]["failures"])
    assert (tmp_path / "result" / "atac" / "run.log").exists()


def test_prepare_inputs_reports_empty_bulk_rna_data_as_structured_error(tmp_path: Path) -> None:
    env = {
        **os.environ,
        "CODEX_OMICS_ROOT": str(tmp_path),
        "CODEX_OMICS_DATA_DIR": str(tmp_path / "data"),
        "CODEX_OMICS_RESULT_DIR": str(tmp_path / "result"),
    }
    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "acceptance" / "prepare_test_inputs.py"), "bulk_rna"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    payload = json.loads(completed.stderr)
    assert payload["error_type"] == "InputPreparationFailed"
    assert "FASTQ input directory" in payload["message"]


def test_prepare_atac_samplesheet_uses_replicate_one_per_unique_sample(tmp_path: Path) -> None:
    data = tmp_path / "data"
    atac = data / "nf-core" / "atac"
    genome = data / "nf-core" / "genome"
    atac.mkdir(parents=True)
    genome.mkdir(parents=True)
    (genome / "genome.fa").write_text(">chr1\nACGT\n", encoding="utf-8")
    (genome / "genes.gtf").write_text("chr1\ttest\tgene\t1\t4\t.\t+\t.\tgene_id \"g1\";\n", encoding="utf-8")
    for sample in ["1-WT_combined", "2-KO_combined"]:
        for read in ["R1", "R2"]:
            with gzip.open(atac / f"{sample}_{read}.fastq.gz", "wt", encoding="utf-8") as handle:
                handle.write("@read\nACGT\n+\n!!!!\n")
    env = {
        **os.environ,
        "CODEX_OMICS_ROOT": str(tmp_path),
        "CODEX_OMICS_DATA_DIR": str(data),
        "CODEX_OMICS_RESULT_DIR": str(tmp_path / "result"),
        "CODEX_OMICS_READS_PER_FASTQ": "1",
    }

    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "acceptance" / "prepare_test_inputs.py"), "atac"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    sheet = tmp_path / "result" / "atac" / "samplesheet.csv"
    rows = sheet.read_text(encoding="utf-8").splitlines()
    assert rows[1].endswith(",1")
    assert rows[2].endswith(",1")
