from __future__ import annotations

import csv
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
