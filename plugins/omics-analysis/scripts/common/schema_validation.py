from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_schema(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_payload(payload: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    try:
        import jsonschema  # type: ignore

        jsonschema.validate(payload, schema)
        return {"valid": True, "mode": "jsonschema", "errors": []}
    except ImportError:
        return lightweight_validate(payload, schema)
    except Exception as exc:
        return {"valid": False, "mode": "jsonschema", "errors": [str(exc)]}


def validate_payload_file(payload_path: str | Path, schema_path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8-sig"))
    schema = load_schema(schema_path)
    return validate_payload(payload, schema)


def lightweight_validate(payload: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for key in schema.get("required", []) or []:
        if key not in payload:
            errors.append(f"Missing required key: {key}")
    properties = schema.get("properties", {}) or {}
    for key, spec in properties.items():
        if key not in payload or not isinstance(spec, dict):
            continue
        expected = spec.get("type")
        if expected and not type_matches(payload[key], expected):
            errors.append(f"{key}: expected {expected}, got {type(payload[key]).__name__}")
    return {"valid": not errors, "mode": "lightweight", "errors": errors}


def type_matches(value: Any, expected: str | list[str]) -> bool:
    if isinstance(expected, list):
        return any(type_matches(value, item) for item in expected)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True
