from __future__ import annotations

import os
from pathlib import Path

import pytest

from omics_codex.nfcore.command import run_nfcore, runtime_blockers


pytestmark = [
    pytest.mark.heavy,
    pytest.mark.skipif(os.environ.get("RUN_HEAVY_OMICS") != "1", reason="set RUN_HEAVY_OMICS=1 to run heavy Nextflow checks"),
]


def test_nfcore_rnaseq_test_profile(tmp_path) -> None:
    nextflow_config = Path.cwd() / "envs" / "nextflow-singularity.config"
    params_config = tmp_path / "nfcore-rnaseq-heavy.config"
    params_config.write_text(
        "params {\n"
        "    skip_qc = true\n"
        "    skip_alignment = true\n"
        "    skip_pseudo_alignment = true\n"
        "    skip_quantification_merge = true\n"
        "}\n",
        encoding="utf-8",
    )
    spec = {
        "run": {"name": "nfcore_rnaseq_test_profile", "type": "nfcore_pipeline", "skill": "nf-core-universal"},
        "inputs": {"path": "", "type": "test_profile"},
        "nfcore": {
            "pipeline": "rnaseq",
            "version": "latest",
            "profile": "singularity",
            "params": {"outdir": str(tmp_path / "rnaseq")},
        },
        "execution": {
            "mode": "test_profile",
            "approved": True,
            "resume": True,
            "force": True,
            "workdir": str(tmp_path),
            "max_cpus": 12,
            "nextflow_configs": [str(nextflow_config), str(params_config)],
        },
        "outputs": {"outdir": str(tmp_path / "rnaseq"), "manifest": str(tmp_path / "rnaseq" / "run_manifest.json")},
    }
    blockers = runtime_blockers(spec)
    manifest = run_nfcore(spec)
    if blockers:
        assert manifest["status"] == "blocked"
        assert manifest["errors"]
    else:
        assert manifest["status"] == "completed"
        assert manifest["outputs"]["verification"]["has_multiqc"]
