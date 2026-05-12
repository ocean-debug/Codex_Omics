from __future__ import annotations

import shutil
import subprocess
from typing import Any


def command_version(command: str, args: list[str] | None = None) -> dict[str, Any]:
    executable = shutil.which(command)
    if not executable:
        return {"name": command, "available": False}
    probe = [executable, *(args or ["--version"])]
    try:
        completed = subprocess.run(probe, text=True, capture_output=True, timeout=20, check=False)
    except Exception as exc:  # pragma: no cover - defensive environment probe
        return {"name": command, "available": True, "path": executable, "error": str(exc)}
    return {
        "name": command,
        "available": True,
        "path": executable,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def inspect_environment(kind: str = "all") -> dict[str, Any]:
    probes = {
        "nfcore": ["java", "nextflow", "nf-core", "docker", "singularity", "apptainer"],
        "scrna_qc": ["python"],
        "scvi": ["python"],
    }
    selected = probes if kind == "all" else {kind: probes.get(kind, [])}
    result = {
        group: {name: command_version(name) for name in commands}
        for group, commands in selected.items()
    }
    if kind in {"all", "scvi"}:
        result.setdefault("scvi", {})
        result["scvi"]["python_packages"] = inspect_python_ml_stack()
        result["scvi"]["gpu"] = inspect_gpu()
    return result


def inspect_python_ml_stack() -> dict[str, Any]:
    payload: dict[str, Any] = {}
    try:
        import torch

        payload["torch"] = {
            "version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_version": getattr(torch.version, "cuda", None),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    except Exception as exc:
        payload["torch"] = {"available": False, "error": str(exc)}
    try:
        import scvi

        payload["scvi"] = {"version": getattr(scvi, "__version__", "unknown")}
    except Exception as exc:
        payload["scvi"] = {"available": False, "error": str(exc)}
    return payload


def inspect_gpu() -> dict[str, Any]:
    if not shutil.which("nvidia-smi"):
        return {"available": False, "reason": "nvidia-smi not found"}
    try:
        completed = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        return {"available": False, "error": str(exc)}
    return {
        "available": completed.returncode == 0,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }
