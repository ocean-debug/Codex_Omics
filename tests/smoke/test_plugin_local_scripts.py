from __future__ import annotations

import subprocess
import sys


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], text=True, capture_output=True, check=False)


def test_p0_help_scripts() -> None:
    scripts = [
        "plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py",
        "plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py",
        "plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py",
    ]
    for script in scripts:
        completed = run_script(script, "--help")
        assert completed.returncode == 0, completed.stderr
        assert "usage:" in completed.stdout


def test_environment_scripts_emit_json() -> None:
    scripts = [
        "plugins/omics-analysis/skills/single-cell-rna-qc/scripts/check_environment.py",
        "plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py",
        "plugins/omics-analysis/skills/nextflow-development/scripts/check_environment.py",
    ]
    for script in scripts:
        completed = run_script(script, "--json")
        assert completed.returncode == 0, completed.stderr
        assert '"status"' in completed.stdout
        assert '"install_hints"' in completed.stdout
