from __future__ import annotations

from omics_codex.common.io import load_yaml_or_json
from omics_codex.common.manifest import base_manifest, write_manifest
from omics_codex.workflow import normalize_stages, plan_workflow, run_workflow, workflow_status


def test_workflow_plan_example() -> None:
    config = load_yaml_or_json("examples/workflows/scrna_qc_scvi.yaml")
    manifest = plan_workflow(config)
    assert manifest["status"] == "planned"
    assert manifest["approval_required"] is True
    assert [stage["name"] for stage in manifest["stages"]] == ["scrna_qc", "scvi"]


def test_workflow_connection_is_recorded() -> None:
    config = load_yaml_or_json("examples/workflows/scrna_qc_scvi.yaml")
    stages = normalize_stages(config)
    assert stages[1]["connect_from"]["stage"] == "scrna_qc"


def test_workflow_run_without_approval_only_plans() -> None:
    config = load_yaml_or_json("examples/workflows/scrna_qc_scvi.yaml")
    manifest = run_workflow(config)
    assert manifest["status"] == "planned"


def test_workflow_status_reports_missing_manifest(tmp_path) -> None:
    config = load_yaml_or_json("examples/workflows/scrna_qc_scvi.yaml")
    config["workflow"]["outdir"] = str(tmp_path / "missing")
    status = workflow_status(config)
    assert status["status"] == "missing"


def test_workflow_status_prefers_stage_manifest_status(tmp_path) -> None:
    config = load_yaml_or_json("examples/workflows/scrna_qc_scvi.yaml")
    config["workflow"]["outdir"] = str(tmp_path / "workflow")
    stage_manifest = tmp_path / "workflow" / "scrna_qc" / "run_manifest.json"
    config["workflow"]["stages"] = config["workflow"]["stages"][:1]
    config["workflow"]["stages"][0]["spec"]["outputs"]["manifest"] = str(stage_manifest)
    workflow_manifest = base_manifest(
        skill="omics-workflow",
        status="completed",
        inputs={},
        outputs={"outdir": str(tmp_path / "workflow"), "manifest": str(tmp_path / "workflow" / "workflow_manifest.json")},
    )
    workflow_manifest["stages"] = [{"name": "scrna_qc", "status": "completed", "manifest": str(stage_manifest)}]
    write_manifest(tmp_path / "workflow" / "workflow_manifest.json", workflow_manifest)
    failed_stage = base_manifest(skill="single-cell-rna-qc", status="failed", inputs={}, outputs={"manifest": str(stage_manifest)})
    write_manifest(stage_manifest, failed_stage)

    status = workflow_status(config)

    assert status["status"] == "failed"
    assert status["manifest_status"] == "completed"
    assert status["stages"][0]["status"] == "failed"
    assert status["stages"][0]["workflow_record_status"] == "completed"


def test_workflow_generic_exception_writes_failed_stage_manifest(tmp_path, monkeypatch) -> None:
    import omics_codex.workflow as workflow_module

    config = {
        "workflow": {
            "name": "generic_failure",
            "outdir": str(tmp_path / "workflow"),
            "execution": {"mode": "command_and_run", "approved": True},
            "stages": [
                {
                    "name": "nfcore",
                    "spec": {
                        "run": {"name": "nfcore", "type": "nfcore_pipeline", "skill": "nf-core-universal"},
                        "inputs": {"path": "", "type": "test_profile"},
                        "nfcore": {"pipeline": "rnaseq", "params": {}},
                        "outputs": {"outdir": str(tmp_path / "workflow" / "nfcore"), "manifest": str(tmp_path / "workflow" / "nfcore" / "run_manifest.json")},
                    },
                }
            ],
        }
    }

    def boom(_spec):
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr(workflow_module, "run_stage", boom)
    manifest = run_workflow(config)

    assert manifest["status"] == "failed"
    assert (tmp_path / "workflow" / "nfcore" / "run_manifest.json").exists()
    assert manifest["stages"][0]["errors"][0]["error_type"] == "RuntimeError"
