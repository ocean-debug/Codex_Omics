from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .errors import InvalidRunSpec
from .paths import plugin_root


SCHEMA_FILES = {
    "omics_run_spec": "omics_run_spec.schema.json",
    "run_manifest": "run_manifest.schema.json",
}


def schema_path(name: str) -> Path:
    try:
        filename = SCHEMA_FILES[name]
    except KeyError as exc:
        raise InvalidRunSpec(f"Unknown schema: {name}") from exc
    return plugin_root() / "schemas" / filename


def load_schema(name: str) -> dict[str, Any]:
    with schema_path(name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_payload(payload: dict[str, Any], schema_name: str) -> list[str]:
    validator = Draft202012Validator(load_schema(schema_name))
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.path))
    return [format_error(error) for error in errors]


def assert_valid(payload: dict[str, Any], schema_name: str) -> None:
    errors = validate_payload(payload, schema_name)
    if errors:
        raise InvalidRunSpec("; ".join(errors), "Edit the run spec to satisfy the schema.")


def format_error(error: Any) -> str:
    location = ".".join(str(part) for part in error.path) or "<root>"
    return f"{location}: {error.message}"
