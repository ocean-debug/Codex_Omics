# Changelog

## 1.0.0

- Refactored Codex-Omics into a plugin-only omics skill collection.
- Removed the backend CLI entrypoint and backend runtime package from the supported user path.
- Added plugin-local P0 skills for `single-cell-rna-qc`, `scvi-tools`, and `nextflow-development`.
- Added standard-library common runtime helpers for environment checks, install hints, manifests, reports, and safe command execution.
- Updated release checks to verify plugin-local scripts and reject backend CLI references in plugin packages.
- Validated scvi-tools training acceptance and nf-core/rnaseq execution through completion on a user-managed server.
- Added registry-driven router planning, skill registry validation, seven-section reports, scvi model recommendation and diagnostics, Nextflow `params.yaml` generation, MultiQC parsing, and workflow diagrams.
- Validated registry/router architecture on gpu03 with `pytest`: 43 tests passed.
- Documented slow Galaxy container registry recovery with increased pull timeout, manual Singularity/Apptainer cache placement, and `-resume`.
- Clarified that heavy runtimes such as Java, Nextflow, nf-core, container backends, scverse, scvi-tools, and GPU PyTorch are user-environment dependencies.
- Marked marketplace publication and guaranteed HPC/container registry behavior as out of scope for repository release checks.
