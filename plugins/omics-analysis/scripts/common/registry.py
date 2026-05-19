from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import load_json_or_simple_yaml


PLUGIN_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = PLUGIN_ROOT / "skill_registry.yaml"


def load_skill_registry(path: str | Path | None = None) -> dict[str, Any]:
    registry_path = Path(path) if path else DEFAULT_REGISTRY
    registry = load_json_or_simple_yaml(registry_path)
    skills = registry.get("skills", {})
    if not isinstance(skills, dict):
        raise TypeError("skill_registry.yaml must contain a skills object")
    for skill_id, entry in skills.items():
        if not isinstance(entry, dict):
            raise TypeError(f"Registry entry for {skill_id} must be an object")
        entry.setdefault("skill_id", skill_id)
        entry.setdefault("layer", "task")
        entry.setdefault("domain", "infrastructure")
        entry.setdefault("backends", [])
        entry.setdefault("composes", [])
        entry.setdefault("public_entrypoint", True)
        entry.setdefault("maturity", "experimental")
        entry.setdefault("tasks", [])
        entry.setdefault("input_formats", [])
        entry.setdefault("constraints", [])
        entry.setdefault("scripts", {})
        entry.setdefault("schemas", {})
        entry.setdefault("outputs", [])
        entry.setdefault("approval", {})
        entry.setdefault("reporting", {})
        entry.setdefault("examples", [])
        entry.setdefault("router_keywords", [])
    return registry


def skill_entries(path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    return load_skill_registry(path)["skills"]


def resolve_plugin_path(relative_path: str | Path) -> Path:
    return PLUGIN_ROOT / relative_path


def validate_registry_paths(registry: dict[str, Any] | None = None) -> list[str]:
    registry = registry or load_skill_registry()
    missing: list[str] = []
    for skill_id, entry in registry.get("skills", {}).items():
        for group in ("scripts", "schemas"):
            values = entry.get(group, {})
            if isinstance(values, dict):
                paths = values.values()
            else:
                paths = values
            for value in paths:
                if value and not resolve_plugin_path(str(value)).exists():
                    missing.append(f"{skill_id}.{group}: {value}")
        for value in entry.get("examples", []) or []:
            if value and not resolve_plugin_path(str(value)).exists():
                missing.append(f"{skill_id}.examples: {value}")
        diagram = entry.get("workflow_diagram")
        if diagram and not resolve_plugin_path(str(diagram)).exists():
            missing.append(f"{skill_id}.workflow_diagram: {diagram}")
    return missing
