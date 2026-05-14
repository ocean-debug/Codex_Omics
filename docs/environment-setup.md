# Environment Setup

Codex Omics diagnoses environments before running or installing anything.

## Detect the active environment

```bash
omics-codex doctor --json
```

The doctor output reports one of:

- `uv`: UV-managed project `.venv` or `UV_PROJECT_ENVIRONMENT`.
- `venv`: standard Python virtual environment.
- `conda`: conda or mamba environment.
- `system`: no scoped Python environment detected.

## Python packages

UV:

```bash
uv pip install ".[dev,nfcore,scverse]"
uv pip install scvi-tools
```

venv:

```bash
python -m pip install ".[dev,nfcore,scverse]"
python -m pip install scvi-tools
```

conda/mamba:

```bash
mamba install -c conda-forge scanpy anndata
mamba install -c bioconda -c conda-forge nf-core nextflow
python -m pip install scvi-tools
```

Use `conda` instead of `mamba` when mamba is unavailable.

## GPU PyTorch

Do not blindly install PyTorch. First inspect GPU and driver state:

```bash
nvidia-smi
omics-codex doctor --json
```

Then use the official PyTorch selector for the matching CUDA build. The plugin should present the command and ask before running it.

## Java and Nextflow

For project-local setup, install Java 17+ and Nextflow under `tools/`, then activate:

```bash
source envs/activate-nextflow.sh
```

This keeps Java/Nextflow scoped to the project and avoids changing the system runtime.
