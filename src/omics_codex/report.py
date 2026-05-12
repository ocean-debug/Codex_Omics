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
    if extra:
        lines.extend(["", "## Summary", "", "```json", _json_like(extra), "```"])
    lines.extend(["", "## Next Steps", "", *_next_steps(manifest)])
    return "\n".join(lines) + "\n"


def _json_like(payload: Any) -> str:
    import json

    return json.dumps(payload, indent=2, sort_keys=True)


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
