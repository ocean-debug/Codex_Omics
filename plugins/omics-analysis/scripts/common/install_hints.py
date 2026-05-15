from __future__ import annotations


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
