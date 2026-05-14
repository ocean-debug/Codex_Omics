from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

from .. import __version__


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
    python_environment = inspect_python_environment()
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
    result: dict[str, Any] = {
        "python_environment": python_environment,
    }
    result.update({
        group: {name: command_version(name, args) for name, args in commands.items()}
        for group, commands in selected.items()
    })
    if kind in {"all", "nfcore"}:
        result.setdefault("nfcore", {})
        result["nfcore"]["python_environment"] = python_environment
        result["nfcore"]["environment"] = {
            "JAVA_HOME": os.environ.get("JAVA_HOME", ""),
            "NXF_HOME": os.environ.get("NXF_HOME", ""),
            "NXF_SYNTAX_PARSER": os.environ.get("NXF_SYNTAX_PARSER", ""),
            "NXF_SINGULARITY_CACHEDIR": os.environ.get("NXF_SINGULARITY_CACHEDIR", ""),
            "NXF_APPTAINER_CACHEDIR": os.environ.get("NXF_APPTAINER_CACHEDIR", ""),
            "PATH": os.environ.get("PATH", ""),
        }
        result["nfcore"].update(assess_nfcore_environment(result["nfcore"], python_environment))
    if kind in {"all", "scrna_qc"}:
        result.setdefault("scrna_qc", {})
        result["scrna_qc"]["environment"] = python_environment
        result["scrna_qc"]["python_packages"] = inspect_python_packages(["anndata", "scanpy"])
        result["scrna_qc"].update(assess_scrna_qc_environment(result["scrna_qc"], python_environment))
    if kind in {"all", "scvi"}:
        result.setdefault("scvi", {})
        result["scvi"]["environment"] = python_environment
        result["scvi"]["python_packages"] = inspect_python_ml_stack()
        result["scvi"]["gpu"] = inspect_gpu()
        result["scvi"].update(assess_scvi_environment(result["scvi"], python_environment))
    return result


def inspect_python_environment() -> dict[str, Any]:
    env_type = detect_python_environment_type(os.environ, Path.cwd())
    return {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "virtual_env": os.environ.get("VIRTUAL_ENV", ""),
        "conda_prefix": os.environ.get("CONDA_PREFIX", ""),
        "conda_default_env": os.environ.get("CONDA_DEFAULT_ENV", ""),
        "mamba_root_prefix": os.environ.get("MAMBA_ROOT_PREFIX", ""),
        "uv_project_env": os.environ.get("UV_PROJECT_ENVIRONMENT", ""),
        "inside_venv": bool(os.environ.get("VIRTUAL_ENV")) or sys.prefix != sys.base_prefix,
        "cwd_has_venv": (Path.cwd() / ".venv").exists(),
        "environment_type": env_type["environment_type"],
        "environment_manager": env_type["environment_manager"],
        "environment_confidence": env_type["confidence"],
        "environment_evidence": env_type["evidence"],
        "install_commands": install_command_templates(env_type["environment_type"]),
    }


def detect_python_environment_type(env: dict[str, str] | os._Environ[str] | None = None, cwd: str | Path | None = None) -> dict[str, Any]:
    values = dict(env or os.environ)
    workdir = Path(cwd or Path.cwd())
    evidence: list[str] = []
    if values.get("UV_PROJECT_ENVIRONMENT"):
        evidence.append("UV_PROJECT_ENVIRONMENT is set")
        return {"environment_type": "uv", "environment_manager": "uv", "confidence": "high", "evidence": evidence}
    virtual_env = values.get("VIRTUAL_ENV", "")
    if virtual_env:
        evidence.append("VIRTUAL_ENV is set")
        if Path(virtual_env).name == ".venv" and (workdir / "uv.lock").exists():
            evidence.append("VIRTUAL_ENV points to .venv and uv.lock is present")
            return {"environment_type": "uv", "environment_manager": "uv", "confidence": "medium", "evidence": evidence}
        return {"environment_type": "venv", "environment_manager": "pip", "confidence": "high", "evidence": evidence}
    if values.get("CONDA_PREFIX"):
        evidence.append("CONDA_PREFIX is set")
        if values.get("MAMBA_ROOT_PREFIX"):
            evidence.append("MAMBA_ROOT_PREFIX is set")
            manager = "mamba"
        else:
            manager = "conda"
        return {"environment_type": "conda", "environment_manager": manager, "confidence": "high", "evidence": evidence}
    if sys.prefix != sys.base_prefix:
        evidence.append("sys.prefix differs from sys.base_prefix")
        return {"environment_type": "venv", "environment_manager": "pip", "confidence": "medium", "evidence": evidence}
    evidence.append("No virtual environment marker detected")
    return {"environment_type": "system", "environment_manager": "unknown", "confidence": "medium", "evidence": evidence}


def install_command_templates(environment_type: str) -> dict[str, list[str]]:
    if environment_type == "uv":
        return {
            "python_packages": ["uv pip install <package>"],
            "scverse": ["uv pip install '.[scverse]'"],
            "scvi": ["uv pip install scvi-tools"],
            "nfcore": ["uv pip install nf-core"],
        }
    if environment_type == "conda":
        return {
            "python_packages": ["mamba install -c conda-forge <package>", "conda install -c conda-forge <package>"],
            "scverse": ["mamba install -c conda-forge scanpy anndata", "conda install -c conda-forge scanpy anndata"],
            "scvi": ["python -m pip install scvi-tools"],
            "nfcore": ["mamba install -c bioconda -c conda-forge nf-core nextflow", "conda install -c bioconda -c conda-forge nf-core nextflow"],
        }
    if environment_type == "venv":
        return {
            "python_packages": ["python -m pip install <package>"],
            "scverse": ["python -m pip install '.[scverse]'"],
            "scvi": ["python -m pip install scvi-tools"],
            "nfcore": ["python -m pip install nf-core"],
        }
    return {
        "python_packages": ["Activate a project venv, UV .venv, or conda environment before installing packages."],
        "scverse": ["No install command generated for an unscoped system Python."],
        "scvi": ["No install command generated for an unscoped system Python."],
        "nfcore": ["No install command generated for an unscoped system Python."],
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


def inspect_python_packages(packages: list[str]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for package in packages:
        try:
            __import__(package.replace("-", "_"))
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


def assess_nfcore_environment(payload: dict[str, Any], python_environment: dict[str, Any] | None = None) -> dict[str, Any]:
    python_environment = python_environment or inspect_python_environment()
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    commands = install_command_templates((python_environment or {}).get("environment_type", "system"))
    hints = [
        f"Detected Python environment: {(python_environment or {}).get('environment_type', 'unknown')}.",
        "For project-local Java/Nextflow, also run: source envs/activate-nextflow.sh",
        f"Install nf-core in the active environment when needed: {commands['nfcore'][0]}",
        "Use Singularity or Apptainer on HPC; pre-cache pipelines with: nextflow pull nf-core/<pipeline>",
        "Do not install automatically; ask the user before changing the environment.",
    ]
    if not payload.get("java", {}).get("available"):
        blockers.append(missing("java", "Install Java 17+ and expose it through JAVA_HOME/PATH before running Nextflow."))
    else:
        major = parse_java_major(payload.get("java", {}))
        if major is None:
            blockers.append(
                {
                    "error_type": "UnsupportedRuntime",
                    "message": "Java is available, but its version could not be parsed; Nextflow requires Java 17+.",
                    "suggested_fix": "Activate envs/activate-nextflow.sh or install Java 17+ for this project.",
                    "failed_step": "preflight_java",
                }
            )
        elif major < 17:
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

def assess_scrna_qc_environment(payload: dict[str, Any], python_environment: dict[str, Any] | None = None) -> dict[str, Any]:
    python_environment = python_environment or inspect_python_environment()
    packages = payload.get("python_packages", {})
    blockers: list[dict[str, str]] = []
    commands = install_command_templates((python_environment or {}).get("environment_type", "system"))
    if not packages.get("anndata", {}).get("available") or not packages.get("scanpy", {}).get("available"):
        blockers.append(missing("scverse stack", f"Install scanpy/anndata in the active environment: {commands['scverse'][0]}"))
    return {
        "status": "blocked" if blockers else "ready",
        "blockers": blockers,
        "warnings": [],
        "install_hints": [
            f"Detected Python environment: {(python_environment or {}).get('environment_type', 'unknown')}.",
            f"Install scRNA QC dependencies in the active environment when needed: {commands['scverse'][0]}",
            "Do not install automatically; ask the user before changing the environment.",
        ],
    }


def assess_scvi_environment(payload: dict[str, Any], python_environment: dict[str, Any] | None = None) -> dict[str, Any]:
    python_environment = python_environment or inspect_python_environment()
    packages = payload.get("python_packages", {})
    gpu = payload.get("gpu", {})
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    commands = install_command_templates((python_environment or {}).get("environment_type", "system"))
    hints = [
        f"Detected Python environment: {(python_environment or {}).get('environment_type', 'unknown')}.",
        f"Install scverse dependencies in the active environment when needed: {commands['scverse'][0]}",
        f"Install scvi-tools in the active environment when needed: {commands['scvi'][0]}",
        "Install a PyTorch build that matches the node GPU driver/CUDA stack; use the official PyTorch selector for the exact uv/pip command.",
        "Do not install automatically; ask the user before changing the environment.",
    ]
    if not packages.get("torch", {}).get("available"):
        blockers.append(missing("torch", "Install PyTorch in the active environment before running scVI."))
    if not packages.get("scvi", {}).get("available"):
        blockers.append(missing("scvi-tools", f"Install scvi-tools in the active environment, for example: {commands['scvi'][0]}."))
    if not packages.get("anndata", {}).get("available") or not packages.get("scanpy", {}).get("available"):
        blockers.append(missing("scverse stack", f"Install the scverse dependencies: {commands['scverse'][0]}."))
    torch_info = packages.get("torch", {})
    if gpu.get("available") and torch_info.get("available") and not torch_info.get("cuda_available"):
        warnings.append(
            {
                "error_type": "TorchCudaUnavailable",
                "message": "GPU hardware is visible, but torch.cuda.is_available() is false; scVI will not use GPU acceleration.",
                "suggested_fix": "Install a CUDA-enabled PyTorch build matching the node driver/CUDA stack in the active environment.",
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


def doctor_environment(kind: str = "all") -> dict[str, Any]:
    checks = inspect_environment(kind)
    py_env = checks.get("python_environment", inspect_python_environment())
    task_status: dict[str, str] = {}
    for task in ["nfcore", "scrna_qc", "scvi"]:
        if task in checks:
            task_status[task] = checks[task].get("status", "unknown")
    status_values = set(task_status.values())
    overall = "blocked" if "blocked" in status_values else ("warning" if "warning" in status_values else "ready")
    return {
        "status": overall,
        "version": {"omics_codex": __version__},
        "python_environment": py_env,
        "task_status": task_status,
        "checks": checks,
        "install_policy": {
            "default": "Do not install heavy dependencies automatically.",
            "approval_required": True,
            "allowed_targets": ["active Python environment", "project-local tools/"],
            "notes": [
                "Ask the user before installing scvi-tools, PyTorch, Java, Nextflow, nf-core, or container tooling.",
                "For unknown/system Python, generate an installation plan instead of mutating the environment.",
            ],
        },
        "suggested_user_path": [
            "omics-codex doctor --json",
            "omics-codex inspect-data --input <input-path>",
            "omics-codex route --prompt <goal> --input <input-path> --outdir <results> --out workflow.json",
            "omics-codex workflow plan --config workflow.json",
            "Set approved: true only after review, then run.",
        ],
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
