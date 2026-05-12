from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

from ..common.errors import OmicsError
from ..common.paths import repo_root
from .registry import inspect_pipeline


def cache_dir() -> Path:
    return repo_root() / ".cache" / "nfcore"


def resolve_version(pipeline: str, version: str = "latest") -> str:
    if version and version != "latest":
        return version
    metadata = inspect_pipeline(pipeline)
    return metadata.get("latest_release") or "latest"


def schema_cache_path(pipeline: str, version: str = "latest") -> Path:
    short = pipeline.replace("nf-core/", "")
    resolved = resolve_version(short, version)
    return cache_dir() / short / resolved / "nextflow_schema.json"


def fetch_pipeline_schema(pipeline: str, version: str = "latest", outdir: str | Path | None = None) -> Path:
    short = pipeline.replace("nf-core/", "")
    resolved = resolve_version(short, version)
    target = Path(outdir) / "nextflow_schema.json" if outdir else schema_cache_path(short, resolved)
    if target.exists():
        return target
    try:
        import requests
    except ImportError as exc:
        raise OmicsError(
            "PipelineSchemaMissing",
            "requests is required to fetch nf-core pipeline schemas.",
            "Install the nfcore extra or provide a local schema path.",
            "fetch_pipeline_schema",
        ) from exc
    urls = []
    if resolved != "latest":
        urls.append(f"https://raw.githubusercontent.com/nf-core/{short}/{resolved}/nextflow_schema.json")
    urls.extend(
        [
            f"https://raw.githubusercontent.com/nf-core/{short}/master/nextflow_schema.json",
            f"https://raw.githubusercontent.com/nf-core/{short}/main/nextflow_schema.json",
        ]
    )
    for url in urls:
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(response.text, encoding="utf-8")
                return target
        except Exception:
            continue
    raise OmicsError(
        "PipelineSchemaMissing",
        f"Could not fetch nextflow_schema.json for nf-core/{short} version {resolved}.",
        "Check network access or provide a local schema path.",
        "fetch_pipeline_schema",
    )


def load_pipeline_schema(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_params(schema: dict[str, Any], params: dict[str, Any]) -> list[str]:
    properties, required = extract_param_contract(schema)
    param_schema = {
        "type": "object",
        "properties": properties,
        "required": sorted(required),
        "additionalProperties": True,
    }
    validator = Draft7Validator(param_schema)
    return [f"{'.'.join(map(str, err.path)) or '<root>'}: {err.message}" for err in validator.iter_errors(params)]


def validate_params_with_provenance(schema: dict[str, Any], params: dict[str, Any], schema_path: str | Path | None = None) -> dict[str, Any]:
    official = try_official_schema_validation(params, schema_path)
    fallback_errors = validate_params(schema, params)
    return {
        "valid": not (official.get("errors") or fallback_errors),
        "official_validator": official,
        "fallback_errors": fallback_errors,
        "errors": official.get("errors") or fallback_errors,
    }


def try_official_schema_validation(params: dict[str, Any], schema_path: str | Path | None) -> dict[str, Any]:
    if not schema_path or not shutil.which("nf-core"):
        return {"available": False, "reason": "nf-core command not available or schema path not provided"}
    return {
        "available": True,
        "used": False,
        "reason": "No stable non-interactive nf-core parameter validation command is assumed; Python JSON Schema fallback was used.",
        "schema": str(schema_path),
    }


def create_params_template(schema: dict[str, Any]) -> dict[str, Any]:
    template: dict[str, Any] = {}
    for name, spec in extract_param_properties(schema).items():
        if "default" in spec:
            template[name] = spec["default"]
        elif spec.get("type") == "boolean":
            template[name] = False
        elif spec.get("type") in {"integer", "number"}:
            template[name] = None
        else:
            template[name] = ""
    return template


def extract_param_properties(schema: dict[str, Any]) -> dict[str, Any]:
    properties, _ = extract_param_contract(schema)
    return properties


def extract_param_contract(schema: dict[str, Any]) -> tuple[dict[str, Any], set[str]]:
    defs: dict[str, Any] = {}
    required: set[str] = set()

    def add_object_contract(node: dict[str, Any]) -> None:
        props = node.get("properties")
        if isinstance(props, dict):
            defs.update(props)
        for name in node.get("required") or []:
            if isinstance(name, str):
                required.add(name)

    top = schema.get("properties", {})
    if isinstance(top, dict):
        defs.update(top)
    for name in schema.get("required") or []:
        if isinstance(name, str):
            required.add(name)
    for definition in (schema.get("definitions") or {}).values():
        if isinstance(definition, dict):
            add_object_contract(definition)
    for group in (schema.get("$defs") or {}).values():
        if isinstance(group, dict):
            add_object_contract(group)
    return defs, required
