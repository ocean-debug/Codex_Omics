from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from time import monotonic
from typing import Any

from .common.errors import OmicsError
from .common.io import load_yaml_or_json, write_text
from .common.manifest import base_manifest, now_iso, write_manifest
from .common.paths import prepare_outdir
from .common.schema import assert_valid
from .nfcore.command import run_nfcore
from .report import render_report
from .scrna_qc.workflow import run_scrna_qc
from .scvi.train import train_scvi, validate_scvi


def load_workflow(path: str | Path) -> dict[str, Any]:
    config = load_yaml_or_json(path)
    if "workflow" not in config:
        raise OmicsError("InvalidWorkflowSpec", "Workflow config must contain a 'workflow' object.", "Add workflow.stages.", "load_workflow")
    return config


def plan_workflow(config: dict[str, Any]) -> dict[str, Any]:
    workflow = config.get("workflow", {})
    stages = normalize_stages(config)
    outdir = prepare_outdir(workflow.get("outdir") or config.get("outputs", {}).get("outdir", "./results/workflow"))
    planned = []
    for index, stage in enumerate(stages, start=1):
        spec = stage["spec"]
        planned.append(
            {
                "index": index,
                "name": stage["name"],
                "skill": spec.get("run", {}).get("skill"),
                "status": "planned",
                "outdir": spec.get("outputs", {}).get("outdir"),
                "manifest": spec.get("outputs", {}).get("manifest"),
                "connect_from": stage.get("connect_from"),
            }
        )
    manifest = base_manifest(
        skill="omics-workflow",
        status="planned",
        inputs=config.get("inputs", {}),
        outputs={
            "outdir": str(outdir),
            "manifest": str(outdir / "workflow_manifest.json"),
            "report": str(outdir / "workflow_report.md"),
        },
        parameters={"workflow": workflow, "stages": planned},
    )
    manifest["stages"] = planned
    if not workflow.get("execution", config.get("execution", {})).get("approved", False):
        manifest["approval_required"] = True
    write_manifest(outdir / "workflow_manifest.json", manifest)
    write_text(outdir / "workflow_report.md", render_workflow_report(manifest))
    return manifest


def run_workflow(config: dict[str, Any], *, resume: bool = False) -> dict[str, Any]:
    workflow = config.get("workflow", {})
    execution = workflow.get("execution", config.get("execution", {}))
    if not execution.get("approved", False):
        return plan_workflow(config)
    outdir = prepare_outdir(workflow.get("outdir") or config.get("outputs", {}).get("outdir", "./results/workflow"), force=bool(execution.get("force", False)))
    stage_manifests: dict[str, dict[str, Any]] = {}
    stage_records: list[dict[str, Any]] = []
    status = "completed"
    errors: list[dict[str, Any]] = []
    for stage in normalize_stages(config):
        stage_manifest_path = Path(stage["spec"].get("outputs", {}).get("manifest", ""))
        if resume and stage_manifest_path.exists():
            existing = load_yaml_or_json(stage_manifest_path)
            if existing.get("status") == "completed":
                stage_manifests[stage["name"]] = existing
                stage_records.append(stage_record(stage, existing, skipped=True, started_at=now_iso(), completed_at=now_iso(), duration_seconds=0.0))
                continue
        spec = resolve_stage_connections(stage["spec"], stage, stage_manifests)
        started_at = now_iso()
        start = monotonic()
        try:
            manifest = run_stage(spec)
        except Exception as exc:
            manifest = write_failed_stage_manifest(stage, spec, exc)
        completed_at = now_iso()
        duration_seconds = round(monotonic() - start, 3)
        stage_manifests[stage["name"]] = manifest
        stage_records.append(stage_record(stage, manifest, started_at=started_at, completed_at=completed_at, duration_seconds=duration_seconds))
        if manifest.get("status") != "completed":
            status = "failed"
            errors.extend(manifest.get("errors", []))
            if workflow.get("stop_on_failure", True):
                break
    manifest = base_manifest(
        skill="omics-workflow",
        status=status,
        inputs=config.get("inputs", {}),
        outputs={
            "outdir": str(outdir),
            "manifest": str(outdir / "workflow_manifest.json"),
            "report": str(outdir / "workflow_report.md"),
            "stage_manifests": {name: item.get("outputs", {}).get("manifest") for name, item in stage_manifests.items()},
        },
        parameters={"workflow": workflow},
        errors=errors,
    )
    manifest["stages"] = stage_records
    write_manifest(outdir / "workflow_manifest.json", manifest)
    write_text(outdir / "workflow_report.md", render_workflow_report(manifest))
    return manifest


def resume_workflow(config: dict[str, Any]) -> dict[str, Any]:
    return run_workflow(config, resume=True)


def workflow_status(config: dict[str, Any]) -> dict[str, Any]:
    workflow = config.get("workflow", {})
    outdir = Path(workflow.get("outdir") or config.get("outputs", {}).get("outdir", "./results/workflow"))
    manifest_path = outdir / "workflow_manifest.json"
    if not manifest_path.exists():
        return {"status": "missing", "manifest": str(manifest_path)}
    manifest = load_yaml_or_json(manifest_path)
    stages = stage_statuses(config, manifest)
    return {
        "status": derive_workflow_status(stages, manifest.get("status", "unknown")),
        "manifest_status": manifest.get("status", "unknown"),
        "manifest": str(manifest_path),
        "stages": stages,
        "report": manifest.get("outputs", {}).get("report"),
    }


def normalize_stages(config: dict[str, Any]) -> list[dict[str, Any]]:
    workflow = config.get("workflow", {})
    raw_stages = workflow.get("stages") or []
    if not raw_stages:
        raise OmicsError("InvalidWorkflowSpec", "Workflow config must define workflow.stages.", "Add at least one stage.", "normalize_stages")
    stages: list[dict[str, Any]] = []
    base_outdir = Path(workflow.get("outdir") or config.get("outputs", {}).get("outdir", "./results/workflow"))
    for index, raw in enumerate(raw_stages, start=1):
        name = raw.get("name") or f"stage_{index}"
        spec = deepcopy(raw.get("spec") or raw)
        spec.pop("connect_from", None)
        spec.setdefault("execution", {})
        if workflow.get("execution"):
            spec["execution"] = {**workflow["execution"], **spec.get("execution", {})}
        spec.setdefault("outputs", {})
        spec["outputs"].setdefault("outdir", str(base_outdir / name))
        spec["outputs"].setdefault("manifest", str(Path(spec["outputs"]["outdir"]) / "run_manifest.json"))
        spec["outputs"].setdefault("report", str(Path(spec["outputs"]["outdir"]) / "report.md"))
        assert_valid(spec, "omics_run_spec")
        stages.append({"name": name, "spec": spec, "connect_from": raw.get("connect_from")})
    return stages


def resolve_stage_connections(spec: dict[str, Any], stage: dict[str, Any], manifests: dict[str, dict[str, Any]]) -> dict[str, Any]:
    resolved = deepcopy(spec)
    link = stage.get("connect_from") or {}
    if not link:
        return resolved
    source_name = link.get("stage")
    source_output = link.get("output", "filtered_h5ad")
    if source_name not in manifests:
        raise OmicsError("WorkflowConnectionFailed", f"Stage '{source_name}' has not completed.", "Check workflow.stages order.", "resolve_stage_connections")
    value = manifests[source_name].get("outputs", {}).get(source_output)
    if not value:
        raise OmicsError(
            "WorkflowConnectionFailed",
            f"Output '{source_output}' was not found in stage '{source_name}'.",
            "Use a valid output key from the source stage manifest.",
            "resolve_stage_connections",
        )
    resolved.setdefault("inputs", {})["path"] = value
    return resolved


def run_stage(spec: dict[str, Any]) -> dict[str, Any]:
    skill = spec.get("run", {}).get("skill")
    if skill == "nf-core-universal":
        return run_nfcore(spec)
    if skill == "single-cell-rna-qc":
        return run_scrna_qc(spec)
    if skill == "scvi-universal":
        validation = validate_scvi(spec)
        if not validation.get("valid"):
            raise OmicsError("AnnDataValidationFailed", "scVI stage validation failed.", "Run omics-codex scvi validate for details.", "workflow_scvi_validate")
        return train_scvi(spec)
    raise OmicsError("InvalidWorkflowSpec", f"Unsupported workflow stage skill: {skill}", "Choose nf-core, scRNA QC, or scVI.", "run_stage")


def write_failed_stage_manifest(stage: dict[str, Any], spec: dict[str, Any], exc: Exception) -> dict[str, Any]:
    outputs = dict(spec.get("outputs", {}))
    outdir = prepare_outdir(outputs.get("outdir", "./results/workflow_failed_stage"))
    outputs.setdefault("outdir", str(outdir))
    outputs.setdefault("manifest", str(outdir / "run_manifest.json"))
    outputs.setdefault("report", str(outdir / "report.md"))
    manifest = base_manifest(
        skill=spec.get("run", {}).get("skill", "unknown"),
        status="failed",
        inputs=spec.get("inputs", {}),
        outputs=outputs,
        parameters=spec,
        errors=[exception_to_error(exc)],
    )
    write_manifest(outputs["manifest"], manifest)
    write_text(outputs["report"], render_report(manifest))
    return manifest


def stage_statuses(config: dict[str, Any], workflow_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    records = {record.get("name"): record for record in workflow_manifest.get("stages", [])}
    statuses: list[dict[str, Any]] = []
    for stage in normalize_stages(config):
        record = dict(records.get(stage["name"], {}))
        manifest_path = Path(record.get("manifest") or stage["spec"].get("outputs", {}).get("manifest", ""))
        record.setdefault("name", stage["name"])
        record.setdefault("skill", stage["spec"].get("run", {}).get("skill"))
        record["manifest"] = str(manifest_path)
        if manifest_path.exists():
            stage_manifest = load_yaml_or_json(manifest_path)
            record["manifest_exists"] = True
            if record.get("status"):
                record["workflow_record_status"] = record["status"]
            record["status"] = stage_manifest.get("status") or record.get("status")
            record["stage_manifest_status"] = stage_manifest.get("status")
            record["errors"] = stage_manifest.get("errors", [])
        else:
            record["manifest_exists"] = False
            record["status"] = record.get("status") or "missing"
        statuses.append(record)
    return statuses


def exception_to_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, OmicsError):
        return exc.to_dict()
    return {
        "status": "failed",
        "error_type": exc.__class__.__name__,
        "message": str(exc),
        "suggested_fix": "Inspect the stage report, manifest, and Python traceback context, then rerun the workflow.",
        "failed_step": "run_stage",
    }


def derive_workflow_status(stages: list[dict[str, Any]], fallback: str) -> str:
    statuses = {str(stage.get("status")) for stage in stages if stage.get("status")}
    if not statuses:
        return fallback
    for status in ["failed", "blocked", "missing"]:
        if status in statuses:
            return status
    if statuses <= {"completed", "skipped_completed"}:
        return "completed"
    if "planned" in statuses:
        return "planned"
    return fallback


def stage_record(
    stage: dict[str, Any],
    manifest: dict[str, Any],
    *,
    skipped: bool = False,
    started_at: str | None = None,
    completed_at: str | None = None,
    duration_seconds: float | None = None,
) -> dict[str, Any]:
    return {
        "name": stage["name"],
        "skill": manifest.get("skill"),
        "status": "skipped_completed" if skipped else manifest.get("status"),
        "manifest": manifest.get("outputs", {}).get("manifest") or stage["spec"].get("outputs", {}).get("manifest"),
        "outdir": manifest.get("outputs", {}).get("outdir"),
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_seconds": duration_seconds,
        "errors": manifest.get("errors", []),
    }


def render_workflow_report(manifest: dict[str, Any]) -> str:
    stage_lines = []
    for stage in manifest.get("stages", []):
        duration = stage.get("duration_seconds")
        duration_text = f", {duration}s" if duration is not None else ""
        stage_lines.append(f"- `{stage.get('name')}`: `{stage.get('status')}` ({stage.get('skill')}{duration_text})")
    base = render_report(manifest, {"stages": manifest.get("stages", [])})
    approval = "\n## Approval\n\n- This workflow is planned only. Set `workflow.execution.approved: true` in an approved config before execution.\n" if manifest.get("approval_required") else ""
    return base + approval + "\n## Workflow Stages\n\n" + ("\n".join(stage_lines) if stage_lines else "- No stages recorded.") + "\n"
