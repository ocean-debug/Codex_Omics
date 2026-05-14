from __future__ import annotations

from pathlib import Path
from typing import Any

from .common.io import load_yaml_or_json, write_text


def render_report(manifest: dict[str, Any], extra: dict[str, Any] | None = None) -> str:
    extra = extra or load_manifest_extras(manifest)
    lines = [
        "# Omics Run Report",
        "",
        f"- Run ID: `{manifest.get('run_id', 'unknown')}`",
        f"- Skill: `{manifest.get('skill', 'unknown')}`",
        f"- Status: `{manifest.get('status', 'unknown')}`",
        f"- Created: `{manifest.get('created_at', 'unknown')}`",
        "",
        "## Methods Summary",
        "",
        *_methods_summary(manifest, extra),
        "",
        "## Key Parameters",
        "",
        *_key_parameters(manifest),
        "",
        "## Key Outputs",
        "",
        *_key_outputs(manifest, extra),
        "",
        "## Inputs",
        "",
        "```json",
        _json_like(manifest.get("inputs", {})),
        "```",
        "",
        "## Outputs",
        "",
        "```json",
        _json_like(manifest.get("outputs", {})),
        "```",
        "",
        "## Commands",
        "",
    ]
    commands = manifest.get("commands") or []
    if commands:
        lines.extend(f"- `{command}`" for command in commands)
    else:
        lines.append("- No commands recorded.")
    lines.extend(
        [
            "",
            "## Software",
            "",
            "```json",
            _json_like(manifest.get("software", {})),
            "```",
        ]
    )
    errors = manifest.get("errors") or []
    if errors:
        lines.extend(["", "## Errors", "", "```json", _json_like(errors), "```"])
        lines.extend(["", "## Failure Interpretation", "", *_failure_interpretation(errors)])
    if extra:
        lines.extend(["", "## Summary", "", "```json", _json_like(extra), "```"])
    lines.extend(["", "## Next Steps", "", *_next_steps(manifest)])
    return "\n".join(lines) + "\n"


def _json_like(payload: Any) -> str:
    import json

    return json.dumps(payload, indent=2, sort_keys=True)


def _methods_summary(manifest: dict[str, Any], extra: dict[str, Any]) -> list[str]:
    skill = manifest.get("skill")
    status = manifest.get("status", "unknown")
    if skill == "nf-core-universal":
        params = manifest.get("parameters", {}).get("nfcore", {}) or manifest.get("nfcore", {})
        pipeline = params.get("pipeline", "nf-core pipeline")
        profile = params.get("profile") or params.get("params", {}).get("profile") or "default"
        return [
            f"- Planned or ran `{pipeline}` with status `{status}`.",
            f"- Execution profile: `{profile}`.",
            "- Review the command, samplesheet, pipeline revision, container runtime, and MultiQC output before interpretation.",
        ]
    if skill == "single-cell-rna-qc":
        summary = extra.get("summary", {}) if isinstance(extra, dict) else {}
        before = summary.get("n_cells_before") or summary.get("cells_before")
        after = summary.get("n_cells_after") or summary.get("cells_after")
        count_text = f" Cells before/after filtering: `{before}` -> `{after}`." if before is not None and after is not None else ""
        return [
            f"- Ran single-cell RNA-seq QC with status `{status}`.{count_text}",
            "- Raw count preservation, threshold settings, and QC plots should be checked before downstream modeling.",
        ]
    if skill == "scvi-universal":
        params = manifest.get("parameters", {}).get("scvi", {}) or manifest.get("scvi", {})
        model = params.get("model", "SCVI")
        return [
            f"- Trained or validated `{model}` with status `{status}`.",
            "- Inspect latent embeddings, model-specific outputs, GPU/PyTorch/scvi-tools versions, and training parameters.",
        ]
    if skill == "omics-workflow":
        stages = manifest.get("stages", [])
        return [
            f"- Planned or ran a multi-stage omics workflow with status `{status}`.",
            f"- Stage count: `{len(stages)}`.",
            "- Use stage manifests for exact per-stage inputs, outputs, commands, and failures.",
        ]
    return [f"- Generated an omics report with status `{status}`."]


def _key_parameters(manifest: dict[str, Any]) -> list[str]:
    params = manifest.get("parameters", {})
    skill = manifest.get("skill")
    if skill == "nf-core-universal":
        nfcore = params.get("nfcore", {}) if isinstance(params, dict) else {}
        pipeline = nfcore.get("pipeline") or params.get("pipeline") or "unknown"
        profile = nfcore.get("profile") or params.get("profile") or "unknown"
        max_cpus = params.get("execution", {}).get("max_cpus") if isinstance(params.get("execution"), dict) else None
        return [
            f"- Pipeline: `{pipeline}`.",
            f"- Profile: `{profile}`.",
            f"- Max CPUs: `{max_cpus or 'not recorded'}`.",
        ]
    if skill == "scvi-universal":
        scvi = params.get("scvi", {}) if isinstance(params, dict) else {}
        train = scvi.get("train", {}) if isinstance(scvi.get("train"), dict) else {}
        downstream = scvi.get("downstream", {}) if isinstance(scvi.get("downstream"), dict) else {}
        return [
            f"- Model: `{scvi.get('model', 'SCVI')}`.",
            f"- Max epochs: `{train.get('max_epochs', 'not recorded')}`.",
            f"- Latent key: `{downstream.get('latent_key', 'not recorded')}`.",
        ]
    if skill == "single-cell-rna-qc":
        qc = params.get("scrna_qc", {}) if isinstance(params, dict) else {}
        filt = qc.get("filter", {}) if isinstance(qc.get("filter"), dict) else {}
        return [
            f"- Filter mode: `{filt.get('mode', 'not recorded')}`.",
            f"- Counts layer: `{qc.get('counts_layer', 'not recorded')}`.",
            f"- Preserve raw counts: `{qc.get('preserve_raw_counts', 'not recorded')}`.",
        ]
    if skill == "omics-workflow":
        stages = manifest.get("stages", [])
        return [f"- Stages: `{', '.join(str(stage.get('name')) for stage in stages) if stages else 'not recorded'}`."]
    return ["- Parameters are recorded in the manifest JSON below."]


def _key_outputs(manifest: dict[str, Any], extra: dict[str, Any]) -> list[str]:
    outputs = manifest.get("outputs", {})
    lines = [
        f"- Output directory: `{outputs.get('outdir', 'not recorded')}`.",
        f"- Manifest: `{outputs.get('manifest', 'not recorded')}`.",
        f"- Report: `{outputs.get('report', 'not recorded')}`.",
    ]
    verification = extra.get("verification", {}) if isinstance(extra, dict) else {}
    if isinstance(verification, dict):
        multiqc = verification.get("multiqc_reports") or verification.get("multiqc")
        if multiqc:
            lines.append(f"- MultiQC: `{multiqc}`.")
    for key in ["filtered_h5ad", "trained_h5ad", "model_dir", "summary"]:
        if outputs.get(key):
            lines.append(f"- {key}: `{outputs[key]}`.")
    return lines


def _failure_interpretation(errors: list[dict[str, Any]]) -> list[str]:
    lines = []
    for error in errors:
        error_type = error.get("error_type") or error.get("status") or "unknown"
        message = error.get("message", "No error message recorded.")
        suggested = error.get("suggested_fix")
        lines.append(f"- `{error_type}`: {message}")
        if suggested:
            lines.append(f"- Suggested fix: {suggested}")
    return lines or ["- No structured failure details were recorded."]


def write_report(manifest_path: str | Path, output_path: str | Path | None = None) -> Path:
    manifest = load_yaml_or_json(manifest_path)
    target = Path(output_path or manifest.get("outputs", {}).get("report") or Path(manifest_path).with_suffix(".md"))
    return write_text(target, render_report(manifest))


def load_manifest_extras(manifest: dict[str, Any]) -> dict[str, Any]:
    outputs = manifest.get("outputs", {})
    extras: dict[str, Any] = {}
    for key in ["summary", "verification"]:
        value = outputs.get(key)
        if isinstance(value, dict):
            extras[key] = value
            continue
        if isinstance(value, str) and Path(value).exists():
            try:
                extras[key] = load_yaml_or_json(value)
            except Exception as exc:
                extras[f"{key}_warning"] = str(exc)
    return extras


def _next_steps(manifest: dict[str, Any]) -> list[str]:
    status = manifest.get("status")
    skill = manifest.get("skill")
    if status == "failed":
        return ["- Inspect the errors above and rerun with the same output directory when fixed."]
    if status == "planned":
        return ["- Review generated commands and set `execution.approved: true` before running long workflows."]
    if skill == "single-cell-rna-qc":
        return ["- Inspect QC plots before using filtered cells for downstream modeling."]
    if skill == "scvi-universal":
        return ["- Inspect latent embeddings and model summary before biological interpretation."]
    if skill == "nf-core-universal":
        return ["- Inspect MultiQC and pipeline-specific outputs before downstream analysis."]
    if skill == "omics-workflow":
        return ["- Review each stage manifest and the aggregate workflow status."]
    return ["- Review outputs and provenance before using results downstream."]
