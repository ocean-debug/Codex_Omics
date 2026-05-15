# Environment Setup

Plugin-local scripts diagnose the active environment before running analysis.

Supported environment types:

- UV `.venv`
- standard Python `venv`
- conda/mamba
- system or unknown Python

The plugin reports install hints but does not silently install heavy dependencies.

Common dependency groups:

- scRNA QC: `scanpy anndata numpy scipy pandas matplotlib seaborn`
- scVI: `scvi-tools torch scanpy anndata`
- Nextflow: Java 17+, Nextflow, nf-core, git, Singularity/Apptainer or Docker

GPU PyTorch must match the machine GPU, driver, and CUDA stack. Use the official PyTorch selector after checking GPU status.
