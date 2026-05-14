from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
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
    probes: dict[str, dict[str, list[str] | None]] = {
        "nfcore": {
            "java": ["-version"],
            "nextflow": ["-version"],
            "nf-core": ["--version"],
            "git": ["--version"],
            "docker": ["--version"],
            "singularity": ["--version"],
            "apptainer": ["--version"],
        },
        "scrna_qc": {"python": ["--version"]},
        "scvi": {"python": ["--version"]},
    }
    selected = probes if kind == "all" else {kind: probes.get(kind, {})}
    result = {
        group: {name: command_version(name, args) for name, args in commands.items()}
        for group, commands in selected.items()
    }
    if kind in {"all", "nfcore"}:
        result.setdefault("nfcore", {})
        result["nfcore"]["environment"] = {
            "JAVA_HOME": os.environ.get("JAVA_HOME", ""),
            "NXF_HOME": os.environ.get("NXF_HOME", ""),
            "NXF_SINGULARITY_CACHEDIR": os.environ.get("NXF_SINGULARITY_CACHEDIR", ""),
            "NXF_APPTAINER_CACHEDIR": os.environ.get("NXF_APPTAINER_CACHEDIR", ""),
            "PATH": os.environ.get("PATH", ""),
        }
        result["nfcore"].update(assess_nfcore_environment(result["nfcore"]))
    if kind in {"all", "scvi"}:
        result.setdefault("scvi", {})
        result["scvi"]["environment"] = inspect_python_environment()
        result["scvi"]["python_packages"] = inspect_python_ml_stack()
        result["scvi"]["gpu"] = inspect_gpu()
        result["scvi"].update(assess_scvi_environment(result["scvi"]))
    return result


def inspect_python_environment() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "virtual_env": os.environ.get("VIRTUAL_ENV", ""),
        "uv_project_env": os.environ.get("UV_PROJECT_ENVIRONMENT", ""),
        "inside_venv": bool(os.environ.get("VIRTUAL_ENV")) or sys.prefix != sys.base_prefix,
        "cwd_has_venv": (Path.cwd() / ".venv").exists(),
    }


def inspect_python_ml_stack() -> dict[str, Any]:
    payload: dict[str, Any] = {}
    try:
        import torch

        payload["torch"] = {
            "available": True,
            "version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_version": getattr(torch.version, "cuda", None),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
        if torch.cuda.is_available():
            payload["torch"]["devices"] = [
                {
                    "index": index,
                    "name": torch.cuda.get_device_name(index),
                    "capability": ".".join(map(str, torch.cuda.get_device_capability(index))),
                }
                for index in range(torch.cuda.device_count())
            ]
    except Exception as exc:
        payload["torch"] = {"available": False, "error": str(exc)}
    try:
        import scvi

        payload["scvi"] = {"available": True, "version": getattr(scvi, "__version__", "unknown")}
    except Exception as exc:
        payload["scvi"] = {"available": False, "error": str(exc)}
    for package in ["anndata", "scanpy"]:
        try:
            __import__(package)
            payload[package] = {"available": True, "version": metadata.version(package)}
        except Exception as exc:
            payload[package] = {"available": False, "error": str(exc)}
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
        "gpus": parse_nvidia_smi_csv(completed.stdout),
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def parse_nvidia_smi_csv(text: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for line in text.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) >= 3:
            records.append({"name": parts[0], "memory_total": parts[1], "driver_version": parts[2]})
    return records


def assess_nfcore_environment(payload: dict[str, Any]) -> dict[str, Any]:
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    hints = [
        "Activate the project environment first: source .venv/bin/activate",
        "For project-local Java/Nextflow, also run: source envs/activate-nextflow.sh",
        "Install nf-core in the active environment when needed: python -m pip install nf-core",
        "Use Singularity or Apptainer on HPC; pre-cache pipelines with: nextflow pull nf-core/<pipeline>",
    ]
    if not payload.get("java", {}).get("available"):
        blockers.append(missing("java", "Install Java 17+ and expose it through JAVA_HOME/PATH before running Nextflow."))
    else:
        major = parse_java_major(payload.get("java", {}))
        if major is not None and major < 17:
            blockers.append(
                {
                    "error_type": "UnsupportedRuntime",
                    "message": f"Java {major} detected; Nextflow requires Java 17+.",
                    "suggested_fix": "Activate envs/activate-nextflow.sh or install Java 17+ for this project.",
                    "failed_step": "preflight_java",
                }
            )
    if not payload.get("nextflow", {}).get("available"):
        blockers.append(missing("nextflow", "Install Nextflow or activate envs/activate-nextflow.sh."))
    if not payload.get("nf-core", {}).get("available"):
        blockers.append(missing("nf-core", "Install nf-core in the active environment: python -m pip install nf-core."))
    if not any(payload.get(name, {}).get("available") for name in ["singularity", "apptainer", "docker"]):
        blockers.append(missing("container backend", "Install or load Singularity/Apptainer, or choose a valid local container profile."))
    if not payload.get("git", {}).get("available"):
        warnings.append(
            {
                "error_type": "MissingGit",
                "message": "git is not available on PATH; Nextflow may still use JGit, but pre-caching and debugging pipeline pulls are harder.",
                "suggested_fix": "Load git or pre-cache nf-core pipelines before running on restricted compute nodes.",
            }
        )
    env = payload.get("environment", {})
    if not env.get("NXF_HOME"):
        warnings.append(
            {
                "error_type": "MissingNxfHome",
                "message": "NXF_HOME is not set; Nextflow will use the default user cache.",
                "suggested_fix": "Run source envs/activate-nextflow.sh to use the project-local Nextflow cache.",
            }
        )
    return {
        "status": "blocked" if blockers else ("warning" if warnings else "ready"),
        "blockers": blockers,
        "warnings": warnings,
        "install_hints": hints,
    }


def assess_scvi_environment(payload: dict[str, Any]) -> dict[str, Any]:
    packages = payload.get("python_packages", {})
    gpu = payload.get("gpu", {})
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    hints = [
        "Activate the UV environment first: source .venv/bin/activate",
        "Install project extras first: python -m pip install -e \".[dev,nfcore,scverse]\"",
        "Install scvi-tools inside the active UV environment: uv pip install scvi-tools",
        "Install a PyTorch build that matches the node GPU driver/CUDA stack; use the official PyTorch selector for the exact uv/pip command.",
    ]
    if not packages.get("torch", {}).get("available"):
        blockers.append(missing("torch", "Install PyTorch in the active UV environment before running scVI."))
    if not packages.get("scvi", {}).get("available"):
        blockers.append(missing("scvi-tools", "Install scvi-tools in the active UV environment, for example: uv pip install scvi-tools."))
    if not packages.get("anndata", {}).get("available") or not packages.get("scanpy", {}).get("available"):
        blockers.append(missing("scverse stack", "Install the scverse extra: python -m pip install -e \".[scverse]\"."))
    torch_info = packages.get("torch", {})
    if gpu.get("available") and torch_info.get("available") and not torch_info.get("cuda_available"):
        warnings.append(
            {
                "error_type": "TorchCudaUnavailable",
                "message": "GPU hardware is visible, but torch.cuda.is_available() is false; scVI will not use GPU acceleration.",
                "suggested_fix": "Install a CUDA-enabled PyTorch build matching the node driver/CUDA stack in the active UV environment.",
            }
        )
    if not gpu.get("available"):
        warnings.append(
            {
                "error_type": "GpuNotDetected",
                "message": "nvidia-smi did not report an available GPU.",
                "suggested_fix": "Run on a GPU node for GPU training, or use CPU knowingly for small validation jobs.",
            }
        )
    return {
        "status": "blocked" if blockers else ("warning" if warnings else "ready"),
        "blockers": blockers,
        "warnings": warnings,
        "install_hints": hints,
    }


def missing(name: str, suggested_fix: str) -> dict[str, str]:
    return {
        "error_type": "MissingSoftware",
        "message": f"Required software is not available: {name}",
        "suggested_fix": suggested_fix,
        "failed_step": "inspect_environment",
    }


def parse_java_major(command_payload: dict[str, Any]) -> int | None:
    text = "\n".join(str(command_payload.get(key, "")) for key in ["stdout", "stderr"])
    match = re.search(r'version "(\d+)(?:\.(\d+))?', text)
    if not match:
        return None
    first = int(match.group(1))
    if first == 1 and match.group(2):
        return int(match.group(2))
    return first
