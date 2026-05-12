from __future__ import annotations

import os

import pytest

from omics_codex.nfcore.command import run_nfcore


pytestmark = [
    pytest.mark.heavy,
    pytest.mark.skipif(os.environ.get("RUN_HEAVY_OMICS") != "1", reason="set RUN_HEAVY_OMICS=1 to run heavy Nextflow checks"),
]


def test_nfcore_rnaseq_test_profile(tmp_path) -> None:
    spec = {
        "run": {"name": "nfcore_rnaseq_test_profile", "type": "nfcore_pipeline", "skill": "nf-core-universal"},
        "inputs": {"path": "", "type": "test_profile"},
        "nfcore": {"pipeline": "rnaseq", "version": "latest", "profile": "singularity", "params": {"outdir": str(tmp_path / "rnaseq")}},
        "execution": {"mode": "test_profile", "approved": True, "resume": True, "force": True, "workdir": str(tmp_path)},
        "outputs": {"outdir": str(tmp_path / "rnaseq"), "manifest": str(tmp_path / "rnaseq" / "run_manifest.json")},
    }
    manifest = run_nfcore(spec)
    assert manifest["status"] in {"completed", "blocked"}
    if manifest["status"] == "blocked":
        assert manifest["errors"]
