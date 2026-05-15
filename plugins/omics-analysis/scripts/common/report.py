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
