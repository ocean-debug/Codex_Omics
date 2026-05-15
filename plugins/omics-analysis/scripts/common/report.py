from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .io import write_text


def render_report(manifest: dict[str, Any], title: str = "Analysis Report") -> str:
    lines = [
        f"# {title}",
        "",
        f"- Skill: `{manifest.get('skill', 'unknown')}`",
        f"- Status: `{manifest.get('status', 'unknown')}`",
        f"- Run ID: `{manifest.get('run_id', 'unknown')}`",
        f"- Created: `{manifest.get('created_at', 'unknown')}`",
        "",
        "## Key Results",
        "",
        *key_results(manifest),
        "",
        "## Inputs",
        "",
        "```json",
        json.dumps(manifest.get("inputs", {}), indent=2, sort_keys=True, default=str),
        "```",
        "",
        "## Parameters",
        "",
        "```json",
        json.dumps(manifest.get("parameters", {}), indent=2, sort_keys=True, default=str),
        "```",
        "",
        "## Outputs",
        "",
        "```json",
        json.dumps(manifest.get("outputs", {}), indent=2, sort_keys=True, default=str),
        "```",
        "",
        "## Commands",
        "",
    ]
    commands = manifest.get("commands") or []
    lines.extend([f"- `{command}`" for command in commands] or ["- No commands recorded."])
    if manifest.get("errors"):
        lines.extend(["", "## Errors", "", "```json", json.dumps(manifest["errors"], indent=2, sort_keys=True, default=str), "```"])
    if manifest.get("warnings"):
        lines.extend(["", "## Warnings", "", "```json", json.dumps(manifest["warnings"], indent=2, sort_keys=True, default=str), "```"])
    lines.extend(
        [
            "",
            "## Software",
            "",
            "```json",
            json.dumps(manifest.get("software", {}), indent=2, sort_keys=True, default=str),
            "```",
            "",
            "## Suggested Next Steps",
            "",
            *next_steps(manifest),
            "",
        ]
    )
    return "\n".join(lines)


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
