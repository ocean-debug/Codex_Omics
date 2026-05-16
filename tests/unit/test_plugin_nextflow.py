from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path


def test_nextflow_samplesheet_generation(tmp_path: Path) -> None:
    (tmp_path / "sample_R1.fastq.gz").write_text("", encoding="utf-8")
    (tmp_path / "sample_R2.fastq.gz").write_text("", encoding="utf-8")
    sheet = tmp_path / "samplesheet.csv"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py",
            "--pipeline",
            "rnaseq",
            "--input",
            str(tmp_path),
            "--out",
            str(sheet),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    with sheet.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["sample"] == "sample"
    assert rows[0]["fastq_1"].endswith("sample_R1.fastq.gz")
    assert rows[0]["fastq_2"].endswith("sample_R2.fastq.gz")


def test_nextflow_failure_classifies_container_pull_timeout() -> None:
    script = Path("plugins/omics-analysis/skills/nextflow-development/scripts/run_nextflow.py")
    spec = importlib.util.spec_from_file_location("run_nextflow", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    failure = module.classify_failure(
        """
        Failed to pull singularity image
          status : 143
          hint   : Try and increase singularity.pullTimeout in the config (current is "20m")
          INFO:    Downloading network image
        """
    )

    assert failure["error_type"] == "ContainerPullTimeout"
    assert "pullTimeout" in failure["suggested_fix"]


def test_nextflow_command_can_write_pull_timeout_config(tmp_path: Path) -> None:
    sheet = tmp_path / "samplesheet.csv"
    sheet.write_text("sample,fastq_1,fastq_2\ns,a_R1.fastq.gz,a_R2.fastq.gz\n", encoding="utf-8")
    outdir = tmp_path / "plan"

    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py",
            "--pipeline",
            "rnaseq",
            "--input",
            str(sheet),
            "--outdir",
            str(outdir),
            "--profile",
            "singularity",
            "--pull-timeout",
            "4 h",
            "--overwrite-reports",
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    command = (outdir / "command.sh").read_text(encoding="utf-8")
    config = (outdir / "nextflow.config").read_text(encoding="utf-8")
    assert "-c" in command
    assert "nextflow.config" in command
    assert "pullTimeout = '4 h'" in config
    assert "report { overwrite = true }" in config
