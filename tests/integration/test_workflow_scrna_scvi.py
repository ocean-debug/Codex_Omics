from __future__ import annotations

import pytest

from omics_codex.common.io import load_yaml_or_json
from omics_codex.workflow import run_workflow


@pytest.mark.integration
def test_workflow_scrna_qc_scvi_synthetic(tmp_path) -> None:
    pytest.importorskip("scvi")
    config = load_yaml_or_json("examples/workflows/scrna_qc_scvi.approved.yaml")
    config["workflow"]["outdir"] = str(tmp_path / "workflow")
    config["workflow"]["stages"][0]["spec"]["inputs"]["path"] = str(tmp_path / "synthetic_qc.h5ad")
    config["workflow"]["stages"][0]["spec"]["outputs"]["outdir"] = str(tmp_path / "workflow" / "scrna_qc")
    config["workflow"]["stages"][0]["spec"]["outputs"]["manifest"] = str(tmp_path / "workflow" / "scrna_qc" / "run_manifest.json")
    config["workflow"]["stages"][1]["spec"]["outputs"]["outdir"] = str(tmp_path / "workflow" / "scvi")
    config["workflow"]["stages"][1]["spec"]["outputs"]["manifest"] = str(tmp_path / "workflow" / "scvi" / "run_manifest.json")
    manifest = run_workflow(config)
    assert manifest["status"] == "completed"
    assert len(manifest["stages"]) == 2


@pytest.mark.integration
def test_workflow_failed_stage_writes_manifest(tmp_path) -> None:
    pytest.importorskip("anndata")
    config = {
        "workflow": {
            "name": "failed_stage_demo",
            "outdir": str(tmp_path / "workflow"),
            "execution": {"mode": "command_and_run", "approved": True, "force": True},
            "stages": [
                {
                    "name": "bad_scvi",
                    "spec": {
                        "run": {"name": "bad_scvi", "type": "scvi_model", "skill": "scvi-universal"},
                        "inputs": {"path": str(tmp_path / "bad.h5ad"), "type": "h5ad", "synthetic": True},
                        "scvi": {"model": "SCVI", "setup_anndata": {"layer": "missing_counts", "batch_key": "batch"}},
                        "outputs": {
                            "outdir": str(tmp_path / "workflow" / "bad_scvi"),
                            "manifest": str(tmp_path / "workflow" / "bad_scvi" / "run_manifest.json"),
                            "report": str(tmp_path / "workflow" / "bad_scvi" / "report.md"),
                        },
                    },
                }
            ],
        }
    }
    manifest = run_workflow(config)
    assert manifest["status"] == "failed"
    assert (tmp_path / "workflow" / "bad_scvi" / "run_manifest.json").exists()
    assert manifest["stages"][0]["duration_seconds"] is not None
