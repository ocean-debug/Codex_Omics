from __future__ import annotations

from omics_codex.common.io import load_yaml_or_json
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
