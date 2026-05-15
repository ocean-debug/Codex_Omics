from __future__ import annotations

from pathlib import Path
from typing import Any


def install_commands(environment_type: str) -> dict[str, list[str]]:
    if environment_type == "uv":
        return {
            "python_packages": ["uv pip install <package>"],
            "scrna_qc": ["uv pip install scanpy anndata numpy scipy pandas matplotlib seaborn"],
            "scvi": ["uv pip install scvi-tools"],
            "nfcore": ["uv pip install nf-core"],
            "torch_gpu": ["Use the official PyTorch selector for a CUDA build matching this GPU driver, then run the generated uv pip command."],
        }
    if environment_type == "conda":
        return {
            "python_packages": ["mamba install -c conda-forge <package>", "conda install -c conda-forge <package>"],
            "scrna_qc": ["mamba install -c conda-forge scanpy anndata numpy scipy pandas matplotlib seaborn"],
            "scvi": ["python -m pip install scvi-tools"],
            "nfcore": ["mamba install -c bioconda -c conda-forge nf-core nextflow"],
            "torch_gpu": ["Install PyTorch from the channel/command recommended by the official PyTorch selector for this driver/CUDA stack."],
        }
    if environment_type == "venv":
        return {
            "python_packages": ["python -m pip install <package>"],
            "scrna_qc": ["python -m pip install scanpy anndata numpy scipy pandas matplotlib seaborn"],
            "scvi": ["python -m pip install scvi-tools"],
            "nfcore": ["python -m pip install nf-core"],
            "torch_gpu": ["Use the official PyTorch selector for a CUDA build matching this GPU driver, then run the generated pip command."],
        }
    return {
        "python_packages": ["Activate a UV .venv, standard venv, or conda/mamba environment first."],
        "scrna_qc": ["No install command generated for unscoped system Python."],
        "scvi": ["No install command generated for unscoped system Python."],
        "nfcore": ["No install command generated for unscoped system Python."],
        "torch_gpu": ["Choose a scoped environment before installing GPU PyTorch."],
    }


def build_install_plan(
    *,
    task: str,
    python_environment: dict[str, Any],
    gpu: dict[str, Any] | None = None,
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    env_type = str(python_environment.get("environment_type", "system"))
    commands = install_commands(env_type)
    root = Path(project_root or Path.cwd())
    task = task.lower().replace("-", "_")
    actions: list[dict[str, Any]] = []
    blockers: list[dict[str, str]] = []

    if env_type == "system":
        blockers.append(
            {
                "error_type": "UnsupportedRuntime",
                "message": "No scoped Python environment was detected.",
                "suggested_fix": "Activate a UV .venv, venv, conda, or mamba environment before installing omics dependencies.",
            }
        )

    if task in {"scrna_qc", "single_cell_rna_qc"}:
        actions.append({"name": "install_scrna_qc_python_packages", "commands": commands["scrna_qc"], "can_execute": env_type != "system"})
    elif task in {"scvi", "scvi_tools"}:
        actions.append({"name": "install_scvi_tools", "commands": commands["scvi"], "can_execute": env_type != "system"})
        actions.append(
            {
                "name": "review_gpu_pytorch",
                "commands": commands["torch_gpu"],
                "can_execute": False,
                "reason": "GPU PyTorch must match the node GPU, driver, and CUDA compatibility matrix.",
                "gpu": gpu or {},
            }
        )
    elif task in {"nfcore", "nextflow"}:
        actions.append({"name": "install_nf_core_python_cli", "commands": commands["nfcore"], "can_execute": env_type != "system"})
        actions.append(
            {
                "name": "prepare_project_local_nextflow_tools",
                "commands": [
                    f"Install Java 17+ and Nextflow under {root / 'tools'}",
                    "Export JAVA_HOME, PATH, and NXF_HOME only for this project before running Nextflow.",
                ],
                "can_execute": False,
                "reason": "Project-local Java/Nextflow installation is platform-specific and should be reviewed before execution.",
            }
        )
    else:
        blockers.append(
            {
                "error_type": "UnsupportedTask",
                "message": f"Unsupported install task: {task}",
                "suggested_fix": "Use one of: scrna_qc, scvi, nfcore.",
            }
        )

    return {
        "task": task,
        "status": "blocked" if blockers else "planned",
        "python_environment": python_environment,
        "project_root": str(root),
        "actions": actions,
        "blockers": blockers,
        "approval_required": True,
    }
