from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from check_environment import inspect_workflow_environment  # noqa: E402
from common.errors import warning  # noqa: E402
from common.io import ensure_outdir, write_json, write_text  # noqa: E402
from common.manifest import base_manifest, write_manifest  # noqa: E402
from common.report import write_report  # noqa: E402
from validate_input import optional_path, validate_input  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan a standard scRNA-seq workflow from existing Codex-Omics skills.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--batch-key", default="batch")
    parser.add_argument("--groupby", default="leiden")
    parser.add_argument("--marker-reference", default="")
    parser.add_argument("--gene-sets", default="")
    parser.add_argument("--skip-integration", action="store_true")
    parser.add_argument("--skip-annotation", action="store_true")
    parser.add_argument("--skip-marker-de", action="store_true")
    parser.add_argument("--skip-enrichment", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--config")
    return parser


def main(force_plan: bool = False) -> int:
    parser = build_parser()
    args = parser.parse_args()
    if force_plan:
        args.dry_run = True
    manifest = plan_workflow(args)
    print(json.dumps(manifest, indent=2, sort_keys=True, default=str))
    return 0


def plan_workflow(args: argparse.Namespace) -> dict[str, Any]:
    outdir = ensure_outdir(args.output_dir)
    input_path = Path(args.input)
    marker_reference = optional_path(args.marker_reference)
    gene_sets = optional_path(args.gene_sets)
    env = inspect_workflow_environment()
    validation = validate_input(input_path, marker_reference, gene_sets)
    parameters = {
        "batch_key": args.batch_key,
        "groupby": args.groupby,
        "marker_reference": str(marker_reference) if marker_reference else "",
        "gene_sets": str(gene_sets) if gene_sets else "",
        "skip_integration": bool(args.skip_integration),
        "skip_annotation": bool(args.skip_annotation),
        "skip_marker_de": bool(args.skip_marker_de),
        "skip_enrichment": bool(args.skip_enrichment),
        "plan_only": True,
    }
    errors = list(env.get("blockers", [])) + list(validation.get("errors", []))
    warnings = list(env.get("warnings", []))
    if str(args.approved).lower() in {"1", "true", "yes", "y"}:
        warnings.append(warning("PlanOnlyWorkflow", "scrna-standard-workflow records a composition plan only; child skills are not executed automatically.", "Run child approved commands step by step after reviewing their manifests."))
    if parameters["skip_marker_de"] and not parameters["skip_enrichment"]:
        parameters["skip_enrichment"] = True
        warnings.append(
            warning(
                "EnrichmentSkipped",
                "Pathway enrichment was skipped because marker-DE was skipped and no external marker table input is supported by this workflow planner.",
                "Run pathway-enrichment separately with an explicit marker table or gene list.",
            )
        )
    steps = build_steps(input_path, outdir, parameters)
    plan = {
        "workflow": "scrna-standard-workflow",
        "plan_only": True,
        "steps": steps,
        "review_order": [step["step_id"] for step in steps],
        "execution_policy": "Run each child skill in dry-run first; use --approved true only for reviewed steps.",
    }
    write_json(outdir / "workflow_plan.json", plan)
    write_text(outdir / "workflow_plan.md", render_plan_markdown(plan))
    status = "blocked" if errors else "planned"
    outputs = {
        "outdir": str(outdir),
        "workflow_plan_json": str(outdir / "workflow_plan.json"),
        "workflow_plan_md": str(outdir / "workflow_plan.md"),
        "manifest": str(outdir / "run_manifest.json"),
        "report": str(outdir / "report.md"),
    }
    manifest = base_manifest(
        skill="scrna-standard-workflow",
        status=status,
        inputs={"path": str(input_path), "validation": validation},
        outputs=outputs,
        parameters=parameters,
        commands=[command for step in steps for command in step["commands"]],
        errors=errors,
        warnings=warnings,
    )
    manifest["environment"] = env
    manifest["summary"] = {"n_steps": len(steps), "step_ids": [step["step_id"] for step in steps], "plan_only": True}
    manifest["plan"] = plan
    manifest["methods_text"] = "A standard scRNA-seq workflow plan was generated by composing Codex-Omics task skills for QC, preprocessing, optional integration, annotation, marker detection, enrichment, and reporting. No child analysis step was executed by this workflow planner."
    manifest["interpretation"] = ["This is a workflow plan, not completed biological analysis.", "Review each child dry-run manifest before executing approved commands."]
    write_manifest(outdir / "run_manifest.json", manifest)
    write_report(outdir / "report.md", manifest, title="scRNA Standard Workflow Plan")
    return manifest


def build_steps(input_path: Path, outdir: Path, parameters: dict[str, Any]) -> list[dict[str, Any]]:
    qc_out = outdir / "01_qc"
    preprocess_out = outdir / "02_preprocess"
    integration_out = outdir / "03_integration"
    annotation_out = outdir / "04_annotation"
    marker_out = outdir / "05_marker_de"
    enrichment_out = outdir / "06_enrichment"
    report_out = outdir / "07_report.md"
    filtered = qc_out / "filtered.h5ad"
    preprocessed = preprocess_out / "preprocessed.h5ad"
    integrated = integration_out / "integrated.h5ad"
    analysis_h5ad = preprocessed if parameters["skip_integration"] else integrated
    steps = [
        step("01_qc", "single-cell-rna-qc", [f"python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input {quote(input_path)} --output-dir {quote(qc_out)} --dry-run --json"], f"python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --input {quote(input_path)} --output-dir {quote(qc_out)} --approved true --write-manifest"),
        step("02_preprocess", "single-cell-preprocess", [f"python plugins/omics-analysis/skills/single-cell-preprocess/scripts/run.py --input {quote(filtered)} --output-dir {quote(preprocess_out)} --dry-run --json"], f"python plugins/omics-analysis/skills/single-cell-preprocess/scripts/run.py --input {quote(filtered)} --output-dir {quote(preprocess_out)} --approved true --write-manifest"),
    ]
    if not parameters["skip_integration"]:
        steps.append(step("03_integration", "single-cell-integration", [f"python plugins/omics-analysis/skills/single-cell-integration/scripts/run.py --input {quote(preprocessed)} --output-dir {quote(integration_out)} --backend scanpy-combat --batch-key {quote(parameters['batch_key'])} --dry-run --json"], f"python plugins/omics-analysis/skills/single-cell-integration/scripts/run.py --input {quote(preprocessed)} --output-dir {quote(integration_out)} --backend scanpy-combat --batch-key {quote(parameters['batch_key'])} --approved true --write-manifest"))
    if not parameters["skip_annotation"]:
        marker_ref = parameters["marker_reference"] or "marker_reference.csv"
        steps.append(step("04_annotation", "single-cell-annotation", [f"python plugins/omics-analysis/skills/single-cell-annotation/scripts/run.py --input {quote(analysis_h5ad)} --output-dir {quote(annotation_out)} --backend marker-based --marker-reference {quote(marker_ref)} --groupby {quote(parameters['groupby'])} --dry-run --json"], f"python plugins/omics-analysis/skills/single-cell-annotation/scripts/run.py --input {quote(analysis_h5ad)} --output-dir {quote(annotation_out)} --backend marker-based --marker-reference {quote(marker_ref)} --groupby {quote(parameters['groupby'])} --approved true --write-manifest"))
    if not parameters["skip_marker_de"]:
        steps.append(step("05_marker_de", "single-cell-marker-de", [f"python plugins/omics-analysis/skills/single-cell-marker-de/scripts/run.py --input {quote(analysis_h5ad)} --output-dir {quote(marker_out)} --groupby {quote(parameters['groupby'])} --dry-run --json"], f"python plugins/omics-analysis/skills/single-cell-marker-de/scripts/run.py --input {quote(analysis_h5ad)} --output-dir {quote(marker_out)} --groupby {quote(parameters['groupby'])} --approved true --write-manifest"))
    if not parameters["skip_enrichment"]:
        gene_sets = parameters["gene_sets"] or "gene_sets.gmt"
        steps.append(step("06_enrichment", "pathway-enrichment", [f"python plugins/omics-analysis/skills/pathway-enrichment/scripts/run.py --input {quote(marker_out / 'markers.csv')} --gene-sets {quote(gene_sets)} --output-dir {quote(enrichment_out)} --dry-run --json"], f"python plugins/omics-analysis/skills/pathway-enrichment/scripts/run.py --input {quote(marker_out / 'markers.csv')} --gene-sets {quote(gene_sets)} --output-dir {quote(enrichment_out)} --approved true --write-manifest"))
    steps.append(step("07_report", "omics-report", [f"python plugins/omics-analysis/skills/omics-report/scripts/render_report.py --manifest {quote(outdir / 'run_manifest.json')} --out {quote(report_out)}"], ""))
    return steps


def step(step_id: str, skill: str, commands: list[str], approved_command: str) -> dict[str, Any]:
    return {"step_id": step_id, "skill": skill, "commands": commands, "approved_command": approved_command}


def quote(value: str | Path) -> str:
    return shlex.quote(str(value))


def render_plan_markdown(plan: dict[str, Any]) -> str:
    lines = ["# scRNA Standard Workflow Plan", "", f"- Plan only: `{plan['plan_only']}`", "", "## Steps", ""]
    for item in plan["steps"]:
        lines.extend([f"### {item['step_id']} `{item['skill']}`", "", "Dry-run commands:"])
        lines.extend([f"- `{command}`" for command in item["commands"]])
        if item.get("approved_command"):
            lines.extend(["", "Approved command:", f"- `{item['approved_command']}`"])
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
