from __future__ import annotations

import platform
import uuid
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from .io import write_json


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def package_versions(names: list[str]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in names:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return versions


def base_manifest(
    *,
    skill: str,
    status: str,
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    parameters: dict[str, Any] | None = None,
    commands: list[str] | None = None,
    errors: list[dict[str, Any]] | None = None,
    warnings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "run_id": str(uuid.uuid4()),
        "skill": skill,
        "status": status,
        "created_at": now_iso(),
        "inputs": inputs or {},
        "outputs": outputs or {},
        "parameters": parameters or {},
        "software": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": package_versions(["anndata", "scanpy", "scvi-tools", "torch", "numpy", "pandas", "scipy", "nf-core"]),
        },
        "commands": commands or [],
        "logs": [],
        "errors": errors or [],
        "warnings": warnings or [],
    }


def write_manifest(path: str | Path, manifest: dict[str, Any]) -> Path:
    return write_json(path, manifest)
