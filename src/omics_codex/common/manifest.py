from __future__ import annotations

import platform
import uuid
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from .io import write_json
from .schema import assert_valid


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def base_manifest(
    *,
    skill: str,
    status: str,
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    parameters: dict[str, Any] | None = None,
    commands: list[str] | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "run_id": str(uuid.uuid4()),
        "status": status,
        "skill": skill,
        "created_at": now_iso(),
        "inputs": inputs or {},
        "outputs": outputs or {},
        "parameters": parameters or {},
        "software": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": package_versions(
                [
                    "codex-omics-skills",
                    "anndata",
                    "scanpy",
                    "scvi-tools",
                    "numpy",
                    "pandas",
                    "scipy",
                    "torch",
                    "jsonschema",
                ]
            ),
        },
        "commands": commands or [],
        "logs": [],
        "errors": errors or [],
    }


def package_versions(names: list[str]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in names:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return versions


def write_manifest(path: str | Path, manifest: dict[str, Any]) -> Path:
    assert_valid(manifest, "run_manifest")
    return write_json(path, manifest)
