from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

from .errors import missing_software, warning
from .install_hints import install_commands


def detect_python_environment(env: dict[str, str] | None = None, cwd: str | Path | None = None) -> dict[str, Any]:
    values = dict(env or os.environ)
    workdir = Path(cwd or Path.cwd())
    evidence: list[str] = []
    if values.get("UV_PROJECT_ENVIRONMENT"):
        evidence.append("UV_PROJECT_ENVIRONMENT is set")
        env_type = "uv"
        manager = "uv"
        confidence = "high"
    elif values.get("VIRTUAL_ENV"):
        evidence.append("VIRTUAL_ENV is set")
        if Path(values["VIRTUAL_ENV"]).name == ".venv" and (workdir / "uv.lock").exists():
            evidence.append("VIRTUAL_ENV points to .venv and uv.lock is present")
            env_type = "uv"
            manager = "uv"
            confidence = "medium"
        else:
            env_type = "venv"
            manager = "pip"
            confidence = "high"
    elif values.get("CONDA_PREFIX"):
        evidence.append("CONDA_PREFIX is set")
        if values.get("MAMBA_ROOT_PREFIX"):
            evidence.append("MAMBA_ROOT_PREFIX is set")
            manager = "mamba"
        else:
            manager = "conda"
        env_type = "conda"
        confidence = "high"
    elif sys.prefix != sys.base_prefix:
        evidence.append("sys.prefix differs from sys.base_prefix")
        env_type = "venv"
        manager = "pip"
        confidence = "medium"
    else:
        evidence.append("No scoped Python environment marker detected")
        env_type = "system"
        manager = "unknown"
        confidence = "medium"
    return {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "environment_type": env_type,
        "environment_manager": manager,
        "confidence": confidence,
        "evidence": evidence,
        "virtual_env": values.get("VIRTUAL_ENV", ""),
        "conda_prefix": values.get("CONDA_PREFIX", ""),
        "conda_default_env": values.get("CONDA_DEFAULT_ENV", ""),
        "uv_project_env": values.get("UV_PROJECT_ENVIRONMENT", ""),
        "install_commands": install_commands(env_type),
    }


def inspect_packages(packages: list[tuple[str, str]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for distribution, import_name in packages:
        try:
            __import__(import_name)
            try:
                version = metadata.version(distribution)
            except metadata.PackageNotFoundError:
                version = "unknown"
            result[distribution] = {"available": True, "version": version}
        except Exception as exc:
            result[distribution] = {"available": False, "error": str(exc)}
    return result


def command_version(command: str, args: list[str] | None = None) -> dict[str, Any]:
    executable = shutil.which(command)
    if not executable:
        return {"name": command, "available": False}
    try:
        completed = subprocess.run([executable, *(args or ["--version"])], text=True, capture_output=True, timeout=20, check=False)
    except Exception as exc:
        return {"name": command, "available": True, "path": executable, "error": str(exc)}
    return {
        "name": command,
        "available": True,
        "path": executable,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


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
    gpus = []
    for line in completed.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) >= 3:
            gpus.append({"name": parts[0], "memory_total": parts[1], "driver_version": parts[2]})
    return {"available": completed.returncode == 0, "gpus": gpus, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}


def inspect_scrna_qc_environment() -> dict[str, Any]:
    py_env = detect_python_environment()
    packages = inspect_packages(
        [
            ("anndata", "anndata"),
            ("scanpy", "scanpy"),
            ("numpy", "numpy"),
            ("scipy", "scipy"),
            ("pandas", "pandas"),
            ("matplotlib", "matplotlib"),
            ("seaborn", "seaborn"),
        ]
    )
    blockers = []
    commands = py_env["install_commands"]
    for name in ["anndata", "scanpy"]:
        if not packages.get(name, {}).get("available"):
            blockers.append(missing_software(name, f"Install scRNA QC dependencies: {commands['scrna_qc'][0]}"))
    return {
        "status": "blocked" if blockers else "ready",
        "python_environment": py_env,
        "python_packages": packages,
        "blockers": blockers,
        "warnings": [],
        "install_hints": [commands["scrna_qc"][0], "Ask the user before installing dependencies."],
    }


def inspect_scvi_environment() -> dict[str, Any]:
    py_env = detect_python_environment()
    packages = inspect_packages(
        [
            ("anndata", "anndata"),
            ("scanpy", "scanpy"),
            ("scvi-tools", "scvi"),
            ("torch", "torch"),
        ]
    )
    gpu = inspect_gpu()
    blockers = []
    warnings = []
    commands = py_env["install_commands"]
    for name in ["anndata", "scanpy"]:
        if not packages.get(name, {}).get("available"):
            blockers.append(missing_software(name, f"Install scverse dependencies: {commands['scrna_qc'][0]}"))
    if not packages.get("scvi-tools", {}).get("available"):
        blockers.append(missing_software("scvi-tools", f"Install scvi-tools: {commands['scvi'][0]}"))
    if not packages.get("torch", {}).get("available"):
        blockers.append(missing_software("torch", "Install PyTorch matching this CPU/GPU environment."))
    else:
        try:
            import torch

            packages["torch"]["cuda_available"] = bool(torch.cuda.is_available())
            packages["torch"]["cuda_version"] = getattr(torch.version, "cuda", None)
            packages["torch"]["device_count"] = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
            if gpu.get("available") and not torch.cuda.is_available():
                warnings.append(
                    warning(
                        "TorchCudaUnavailable",
                        "GPU hardware is visible, but torch.cuda.is_available() is false.",
                        commands["torch_gpu"][0],
                    )
                )
        except Exception as exc:
            packages["torch"]["cuda_probe_error"] = str(exc)
    if not gpu.get("available"):
        warnings.append(warning("GpuNotDetected", "nvidia-smi did not report a GPU.", "Use CPU for small tests or run on a GPU node."))
    return {
        "status": "blocked" if blockers else ("warning" if warnings else "ready"),
        "python_environment": py_env,
        "python_packages": packages,
        "gpu": gpu,
        "blockers": blockers,
        "warnings": warnings,
        "install_hints": [commands["scvi"][0], commands["torch_gpu"][0], "Ask the user before installing dependencies."],
    }


def inspect_nextflow_environment() -> dict[str, Any]:
    py_env = detect_python_environment()
    commands = py_env["install_commands"]
    checks = {
        "java": command_version("java", ["-version"]),
        "nextflow": command_version("nextflow", ["-version"]),
        "nf-core": command_version("nf-core", ["--version"]),
        "git": command_version("git", ["--version"]),
        "singularity": command_version("singularity", ["--version"]),
        "apptainer": command_version("apptainer", ["--version"]),
        "docker": command_version("docker", ["--version"]),
    }
    blockers = []
    warnings = []
    if not checks["java"].get("available"):
        blockers.append(missing_software("Java 17+", "Install Java 17+ and expose it through JAVA_HOME/PATH."))
    else:
        major = parse_java_major(checks["java"])
        if major is None or major < 17:
            blockers.append(
                {
                    "error_type": "UnsupportedRuntime",
                    "message": "Java is available, but Java 17+ was not detected.",
                    "suggested_fix": "Install Java 17+ for Nextflow.",
                    "failed_step": "check_java",
                }
            )
    for name, fix in [
        ("nextflow", "Install Nextflow or load a project-local Nextflow."),
        ("nf-core", f"Install nf-core: {commands['nfcore'][0]}"),
    ]:
        if not checks[name].get("available"):
            blockers.append(missing_software(name, fix))
    if not any(checks[name].get("available") for name in ["singularity", "apptainer", "docker"]):
        blockers.append(missing_software("container backend", "Install or load Singularity/Apptainer for HPC, or Docker for local runs."))
    if not checks["git"].get("available"):
        warnings.append(warning("MissingGit", "git is not available on PATH.", "Load git or pre-cache nf-core pipelines."))
    return {
        "status": "blocked" if blockers else ("warning" if warnings else "ready"),
        "python_environment": py_env,
        "commands": checks,
        "environment": {
            "JAVA_HOME": os.environ.get("JAVA_HOME", ""),
            "NXF_HOME": os.environ.get("NXF_HOME", ""),
            "PATH": os.environ.get("PATH", ""),
        },
        "blockers": blockers,
        "warnings": warnings,
        "install_hints": [
            commands["nfcore"][0],
            "Install Java 17+ and Nextflow as project-local tools when possible.",
            "Ask the user before installing dependencies.",
        ],
    }


def parse_java_major(payload: dict[str, Any]) -> int | None:
    text = "\n".join(str(payload.get(key, "")) for key in ["stdout", "stderr"])
    match = re.search(r'version "(\d+)(?:\.(\d+))?', text)
    if not match:
        return None
    first = int(match.group(1))
    if first == 1 and match.group(2):
        return int(match.group(2))
    return first
