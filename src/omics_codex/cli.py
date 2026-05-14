from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .common.environment import inspect_environment
from .common.errors import OmicsError
from .common.io import load_yaml_or_json, write_json
from .common.schema import assert_valid, validate_payload
from .nfcore.command import build_nextflow_command, run_nfcore
from .nfcore.outputs import verify_pipeline_outputs
from .nfcore.registry import inspect_pipeline, list_pipelines
from .nfcore.samplesheet import make_samplesheet
from .nfcore.schema_tools import create_params_template, fetch_pipeline_schema, load_pipeline_schema, validate_params_with_provenance
from .report import write_report
from .router import build_request_spec, build_template_spec, inspect_input_path, list_templates
from .scrna_qc.workflow import run_scrna_qc
from .scvi.registry import inspect_model, list_models
from .scvi.train import train_scvi, validate_scvi
from .skill_template import create_omics_skill_template
from .workflow import load_workflow, plan_workflow, resume_workflow, run_workflow, workflow_status


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.func(args)
    except OmicsError as exc:
        print(json.dumps(exc.to_dict(), indent=2, sort_keys=True), file=sys.stderr)
        return 2
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error_type": exc.__class__.__name__,
                    "message": str(exc),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    if result is not None:
        emit(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omics-codex", description="Codex Omics Skills CLI")
    parser.add_argument("--version", action="version", version=f"omics-codex {__version__}")
    sub = parser.add_subparsers(required=True)

    init_parser = sub.add_parser("init", help="Show initialization guidance")
    init_parser.set_defaults(func=cmd_init)

    route_parser = sub.add_parser("route", help="Route a natural-language request to a run spec")
    route_parser.add_argument("--prompt", required=True, help="Prompt text or a path to a prompt file")
    route_parser.add_argument("--input", help="Optional input path")
    route_parser.add_argument("--outdir", default="./results/omics", help="Result directory to write into generated specs")
    route_parser.add_argument("--out", help="Optional output run spec path")
    route_parser.set_defaults(func=cmd_route)

    validate_parser = sub.add_parser("validate", help="Validate an omics run spec")
    validate_parser.add_argument("--config", required=True)
    validate_parser.set_defaults(func=cmd_validate)

    run_parser = sub.add_parser("run", help="Run the workflow selected by the run spec")
    run_parser.add_argument("--config", required=True)
    run_parser.set_defaults(func=cmd_run)

    report_parser = sub.add_parser("report", help="Render a report from a run manifest")
    report_parser.add_argument("--manifest", required=True)
    report_parser.add_argument("--out")
    report_parser.set_defaults(func=cmd_report)

    inspect_data_parser = sub.add_parser("inspect-data", help="Inspect an omics input path before routing")
    inspect_data_parser.add_argument("--input", required=True)
    inspect_data_parser.set_defaults(func=lambda args: inspect_input_path(args.input))

    env_parser = sub.add_parser("inspect-env", help="Inspect local or remote active environment")
    env_parser.add_argument("--kind", default="all", choices=["all", "nfcore", "scrna_qc", "scvi"])
    env_parser.set_defaults(func=lambda args: inspect_environment(args.kind))

    template_parser = sub.add_parser("skill-template", help="Create a starter omics skill template")
    template_sub = template_parser.add_subparsers(required=True)
    create_template = template_sub.add_parser("create", help="Create SKILL.md, schema, example, and test stubs")
    create_template.add_argument("--name", required=True)
    create_template.add_argument("--outdir", required=True)
    create_template.set_defaults(func=lambda args: create_omics_skill_template(args.name, args.outdir))

    run_template_parser = sub.add_parser("template", help="Create common omics run/workflow specs")
    run_template_sub = run_template_parser.add_subparsers(required=True)
    run_template_sub.add_parser("list", help="List common run/workflow templates").set_defaults(func=lambda args: {"templates": list_templates()})
    create_run_template = run_template_sub.add_parser("create", help="Create a safe default spec from a common template")
    create_run_template.add_argument("--name", required=True, choices=["bulk-rna", "atac", "scrna-qc", "scrna-qc-scvi", "scvi"])
    create_run_template.add_argument("--input", help="Optional input path")
    create_run_template.add_argument("--outdir", default="./results/omics", help="Result directory to write into generated specs")
    create_run_template.add_argument("--out", help="Optional output YAML/JSON path")
    create_run_template.set_defaults(func=cmd_template_create)

    add_nfcore(sub)
    add_scrna_qc(sub)
    add_scvi(sub)
    add_workflow(sub)
    return parser


def add_nfcore(parent: argparse._SubParsersAction) -> None:
    parser = parent.add_parser("nfcore", help="nf-core helpers")
    sub = parser.add_subparsers(required=True)
    sub.add_parser("list", help="List nf-core pipelines").set_defaults(func=lambda args: list_pipelines())
    inspect_parser = sub.add_parser("inspect", help="Inspect one nf-core pipeline")
    inspect_parser.add_argument("pipeline")
    inspect_parser.set_defaults(func=lambda args: inspect_pipeline(args.pipeline))
    params_parser = sub.add_parser("create-params", help="Create a params template from pipeline schema")
    params_parser.add_argument("pipeline")
    params_parser.add_argument("--version", default="latest")
    params_parser.add_argument("--out")
    params_parser.set_defaults(func=cmd_nfcore_create_params)
    validate_parser = sub.add_parser("validate-params", help="Validate params against a pipeline schema")
    validate_parser.add_argument("--pipeline", required=True)
    validate_parser.add_argument("--version", default="latest")
    validate_parser.add_argument("--params", required=True)
    validate_parser.set_defaults(func=cmd_nfcore_validate_params)
    build_parser_ = sub.add_parser("build-command", help="Build a Nextflow command from a run spec")
    build_parser_.add_argument("--config", required=True)
    build_parser_.set_defaults(func=cmd_nfcore_build_command)
    run_parser = sub.add_parser("run", help="Run or plan an nf-core workflow")
    run_parser.add_argument("--config", required=True)
    run_parser.set_defaults(func=lambda args: run_nfcore(load_yaml_or_json(args.config)))
    sheet_parser = sub.add_parser("make-samplesheet", help="Create an nf-core samplesheet from FASTQ files")
    sheet_parser.add_argument("--pipeline", required=True, choices=["rnaseq", "sarek", "atacseq", "nf-core/rnaseq", "nf-core/sarek", "nf-core/atacseq"])
    sheet_parser.add_argument("--input", required=True, help="FASTQ directory")
    sheet_parser.add_argument("--out", required=True, help="Output CSV path")
    sheet_parser.set_defaults(func=cmd_nfcore_make_samplesheet)
    verify_parser = sub.add_parser("verify-output", help="Inspect expected nf-core output files")
    verify_parser.add_argument("--pipeline", required=True)
    verify_parser.add_argument("--outdir", required=True)
    verify_parser.set_defaults(func=cmd_nfcore_verify_output)


def add_scrna_qc(parent: argparse._SubParsersAction) -> None:
    parser = parent.add_parser("scrna-qc", help="single-cell RNA-seq QC")
    sub = parser.add_subparsers(required=True)
    run_parser = sub.add_parser("run", help="Run scRNA-seq QC")
    run_parser.add_argument("--config", required=True)
    run_parser.set_defaults(func=lambda args: run_scrna_qc(load_yaml_or_json(args.config)))


def add_scvi(parent: argparse._SubParsersAction) -> None:
    parser = parent.add_parser("scvi", help="scvi-tools helpers")
    sub = parser.add_subparsers(required=True)
    sub.add_parser("list-models", help="List installed scvi-tools models").set_defaults(func=lambda args: list_models())
    inspect_parser = sub.add_parser("inspect", help="Inspect one scvi-tools model")
    inspect_parser.add_argument("model")
    inspect_parser.set_defaults(func=lambda args: inspect_model(args.model))
    validate_parser = sub.add_parser("validate", help="Validate AnnData for a scvi model")
    validate_parser.add_argument("--config", required=True)
    validate_parser.set_defaults(func=lambda args: validate_scvi(load_yaml_or_json(args.config)))
    train_parser = sub.add_parser("train", help="Train a scvi-tools model")
    train_parser.add_argument("--config", required=True)
    train_parser.set_defaults(func=lambda args: train_scvi(load_yaml_or_json(args.config)))


def add_workflow(parent: argparse._SubParsersAction) -> None:
    parser = parent.add_parser("workflow", help="multi-stage omics workflows")
    sub = parser.add_subparsers(required=True)
    plan_parser = sub.add_parser("plan", help="Plan a multi-stage workflow")
    plan_parser.add_argument("--config", required=True)
    plan_parser.set_defaults(func=lambda args: plan_workflow(load_workflow(args.config)))
    run_parser = sub.add_parser("run", help="Run an approved multi-stage workflow")
    run_parser.add_argument("--config", required=True)
    run_parser.set_defaults(func=lambda args: run_workflow(load_workflow(args.config)))
    resume_parser = sub.add_parser("resume", help="Resume a multi-stage workflow by skipping completed stages")
    resume_parser.add_argument("--config", required=True)
    resume_parser.set_defaults(func=lambda args: resume_workflow(load_workflow(args.config)))
    status_parser = sub.add_parser("status", help="Inspect workflow manifest status")
    status_parser.add_argument("--config", required=True)
    status_parser.set_defaults(func=lambda args: workflow_status(load_workflow(args.config)))


def cmd_init(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "status": "ok",
        "message": "Codex Omics Skills is repo-local. Validate in your configured remote codex-omics environment.",
        "remote_workdir": "<remote-workdir>/codex_omics/",
        "remote_env": "source .venv/bin/activate",
        "node": "<gpu-node>",
        "cores": "<core-count>",
    }


def cmd_route(args: argparse.Namespace) -> dict[str, Any]:
    prompt = Path(args.prompt).read_text(encoding="utf-8") if Path(args.prompt).exists() else args.prompt
    spec = build_request_spec(prompt, input_path=args.input, outdir=args.outdir)
    if args.out:
        write_json(args.out, spec)
    return spec


def cmd_template_create(args: argparse.Namespace) -> dict[str, Any]:
    spec = build_template_spec(args.name, input_path=args.input, outdir=args.outdir)
    if args.out:
        write_json(args.out, spec)
    return spec


def cmd_validate(args: argparse.Namespace) -> dict[str, Any]:
    payload = load_yaml_or_json(args.config)
    errors = validate_payload(payload, "omics_run_spec")
    return {"valid": not errors, "errors": errors, "config": args.config}


def cmd_run(args: argparse.Namespace) -> dict[str, Any]:
    spec = load_yaml_or_json(args.config)
    assert_valid(spec, "omics_run_spec")
    skill = spec.get("run", {}).get("skill")
    if skill == "nf-core-universal":
        return run_nfcore(spec)
    if skill == "single-cell-rna-qc":
        return run_scrna_qc(spec)
    if skill == "scvi-universal":
        return train_scvi(spec)
    raise OmicsError("InvalidRunSpec", f"No executable runner for skill: {skill}", "Choose nf-core, scRNA QC, or scVI.", "dispatch_run")


def cmd_report(args: argparse.Namespace) -> dict[str, Any]:
    path = write_report(args.manifest, args.out)
    return {"status": "ok", "report": str(path)}


def cmd_nfcore_create_params(args: argparse.Namespace) -> dict[str, Any]:
    schema_path = fetch_pipeline_schema(args.pipeline, args.version)
    template = create_params_template(load_pipeline_schema(schema_path))
    if args.out:
        write_json(args.out, template)
    return {"pipeline": args.pipeline, "schema": str(schema_path), "params": template}


def cmd_nfcore_validate_params(args: argparse.Namespace) -> dict[str, Any]:
    schema_path = fetch_pipeline_schema(args.pipeline, args.version)
    schema = load_pipeline_schema(schema_path)
    params = load_yaml_or_json(args.params)
    result = validate_params_with_provenance(schema, params, schema_path)
    return {**result, "schema": str(schema_path)}


def cmd_nfcore_build_command(args: argparse.Namespace) -> dict[str, Any]:
    spec = load_yaml_or_json(args.config)
    command = build_nextflow_command(spec)
    return {"command": command}


def cmd_nfcore_make_samplesheet(args: argparse.Namespace) -> dict[str, Any]:
    return make_samplesheet(args.pipeline, args.input, args.out)


def cmd_nfcore_verify_output(args: argparse.Namespace) -> dict[str, Any]:
    return verify_pipeline_outputs(args.pipeline, args.outdir)


def emit(result: Any) -> None:
    if isinstance(result, str):
        print(result)
    else:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
