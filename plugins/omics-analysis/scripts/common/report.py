from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .io import write_text


def render_report(manifest: dict[str, Any], title: str = "Analysis Report") -> str:
    lines = [
        f"# {title}",
        "",
        "## Analysis Overview",
        "",
        f"- Skill: `{manifest.get('skill', 'unknown')}`",
        f"- Status: `{manifest.get('status', 'unknown')}`",
        f"- Run ID: `{manifest.get('run_id', 'unknown')}`",
        f"- Created: `{manifest.get('created_at', 'unknown')}`",
    ]
    if manifest.get("completed_at"):
        lines.append(f"- Completed: `{manifest.get('completed_at')}`")
    if manifest.get("methods_text"):
        lines.extend(["", "### Methods-ready Text", "", str(manifest["methods_text"])])
    lines.extend(["", "## Input Data Summary", "", "```json", json.dumps(manifest.get("inputs", {}), indent=2, sort_keys=True, default=str), "```"])
    lines.extend(
        [
            "",
            "## Environment and Dependencies",
            "",
            "```json",
            json.dumps({"environment": manifest.get("environment", {}), "software": manifest.get("software", {})}, indent=2, sort_keys=True, default=str),
            "```",
            "",
            "## Methods and Parameters",
            "",
            "```json",
            json.dumps(manifest.get("parameters", {}), indent=2, sort_keys=True, default=str),
            "```",
            "",
            "## Results and QC Interpretation",
            "",
            *key_results(manifest),
        ]
    )
    if manifest.get("qc_summary"):
        lines.extend(["", "### QC Summary", "", "```json", json.dumps(manifest["qc_summary"], indent=2, sort_keys=True, default=str), "```"])
    if manifest.get("interpretation"):
        lines.extend(["", "### Result Interpretation", "", *format_interpretation(manifest["interpretation"])])
    lines.extend(["", "### Outputs", "", "```json", json.dumps(manifest.get("outputs", {}), indent=2, sort_keys=True, default=str), "```"])

    lines.extend(["", "## Warnings / Failures / Suggested Fixes", ""])
    if manifest.get("errors"):
        lines.extend(["### Errors", "", "```json", json.dumps(manifest["errors"], indent=2, sort_keys=True, default=str), "```", ""])
    if manifest.get("warnings"):
        lines.extend(["### Warnings", "", "```json", json.dumps(manifest["warnings"], indent=2, sort_keys=True, default=str), "```", ""])
    auto_fix_plan = manifest.get("auto_fix_plan") or collect_auto_fix_plan(manifest)
    if auto_fix_plan:
        lines.extend(["### Suggested Fixes", "", *[f"- {item}" for item in auto_fix_plan]])
    else:
        lines.extend(next_steps(manifest))

    lines.extend(["", "## Reproducibility Appendix", "", "### Commands", ""])
    commands = manifest.get("commands") or []
    lines.extend([f"- `{command}`" for command in commands] or ["- No commands recorded."])
    lines.extend(
        [
            "",
            "### Manifest Pointers",
            "",
            "```json",
            json.dumps(
                {"outputs": manifest.get("outputs", {}), "logs": manifest.get("logs", []), "schema_version": manifest.get("schema_version")},
                indent=2,
                sort_keys=True,
                default=str,
            ),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def format_interpretation(value: Any) -> list[str]:
    if isinstance(value, list):
        return [f"- {item}" for item in value]
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, list):
                lines.append(f"- {key}:")
                lines.extend(f"  - {entry}" for entry in item)
            else:
                lines.append(f"- {key}: {item}")
        return lines
    return [f"- {value}"]


def collect_auto_fix_plan(manifest: dict[str, Any]) -> list[str]:
    fixes: list[str] = []
    for error in manifest.get("errors", []) or []:
        if not isinstance(error, dict):
            continue
        for item in error.get("auto_fix_plan", []) or []:
            if item not in fixes:
                fixes.append(str(item))
        suggested = error.get("suggested_fix")
        if suggested and suggested not in fixes:
            fixes.append(str(suggested))
    return fixes


def key_results(manifest: dict[str, Any]) -> list[str]:
    skill = manifest.get("skill", "")
    summary = manifest.get("summary") or {}
    if skill == "single-cell-rna-qc":
        before = summary.get("before", {})
        after = summary.get("after", {})
        removed = summary.get("removed_cells", "unknown")
        return [
            f"- Cells before filtering: `{before.get('n_cells', 'unknown')}`",
            f"- Cells after filtering: `{after.get('n_cells', 'unknown')}`",
            f"- Removed cells: `{removed}`",
            f"- Counts source: `{summary.get('counts_source', summary.get('counts_layer', 'unknown'))}`",
            f"- Filter mode: `{summary.get('filter_mode', 'unknown')}`",
        ]
    if skill == "single-cell-preprocess":
        after = summary.get("after", summary if isinstance(summary, dict) else {})
        return [
            f"- Cells: `{after.get('n_cells', 'unknown')}`",
            f"- Genes: `{after.get('n_genes', 'unknown')}`",
            f"- Highly variable genes: `{after.get('n_hvg', 'unknown')}`",
            f"- PCA available: `{after.get('has_pca', 'unknown')}`",
            f"- UMAP available: `{after.get('has_umap', 'unknown')}`",
            f"- Leiden clusters: `{after.get('leiden_clusters', 'unknown')}`",
        ]
    if skill == "scvi-tools":
        return [
            f"- Model: `{summary.get('model', manifest.get('parameters', {}).get('model', 'unknown'))}`",
            f"- Latent key: `{summary.get('latent_key', 'not recorded')}`",
            f"- Max epochs: `{summary.get('max_epochs', manifest.get('parameters', {}).get('max_epochs', 'unknown'))}`",
            f"- Model-specific outputs: `{', '.join(summary.get('model_specific_outputs', []) or ['not recorded'])}`",
        ]
    if skill == "nextflow-development":
        inventory = manifest.get("output_inventory", {})
        return [
            f"- Pipeline: `{manifest.get('parameters', {}).get('pipeline', 'unknown')}`",
            f"- Profile: `{manifest.get('parameters', {}).get('profile', 'unknown')}`",
            f"- MultiQC reports: `{len(inventory.get('multiqc_reports', []))}`",
            f"- Nextflow logs: `{len(inventory.get('nextflow_logs', []))}`",
        ]
    return ["- See manifest sections below for recorded results."]


def next_steps(manifest: dict[str, Any]) -> list[str]:
    status = manifest.get("status")
    if status == "planned":
        return ["- Review the plan and rerun with `--approved true` only if execution is intended."]
    if status == "blocked":
        return ["- Resolve the blockers above, then rerun the same command."]
    if status == "failed":
        return ["- Inspect logs and structured errors, fix the cause, then rerun."]
    return ["- Review outputs and provenance before downstream interpretation."]


def write_report(path: str | Path, manifest: dict[str, Any], title: str = "Analysis Report") -> Path:
    return write_text(path, render_report(manifest, title=title))
