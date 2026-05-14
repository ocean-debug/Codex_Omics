# Changelog

## 0.2.0

- Added structured environment diagnostics for `omics-codex inspect-env --kind scvi|nfcore|all`, including `status`, `blockers`, `warnings`, and install hints.
- Added scVI preflight checks for `scvi-tools`, PyTorch, scverse packages, GPU visibility, and CUDA-enabled torch availability in UV `.venv` environments.
- Added nf-core preflight coverage for Java 17+, Nextflow, nf-core CLI, container backends, project-local Nextflow cache settings, and clearer install guidance.
- Classified common Nextflow failures, including nf-core pipeline pull/network failures such as `github.com/nf-core/atacseq.git: connection failed`.
- Added reusable real-data acceptance scripts under `scripts/acceptance/` for scVI, bulk RNA `nf-core/rnaseq`, and ATAC `nf-core/atacseq`.
- Recorded current real-data acceptance boundary: scVI real h5ad subset completed, bulk RNA rnaseq subset completed with MultiQC, ATAC command/input preparation completed while execution may fail on restricted or incompatible nf-core/Nextflow environments with preserved logs and a classified failure.

## 0.1.0

- Initial public usability release.
- Added repo-local Codex plugin structure with nf-core, scRNA QC, scVI, router, report, and skill-template skills.
- Added `omics-codex` CLI for validation, workflow planning/running, reports, nf-core helpers, scRNA QC, and scVI workflows.
- Added safe-by-default workflow examples; unapproved workflow configs plan only, while approved examples are explicit.
- Added manifests and markdown reports for run provenance.
- Verified smoke, unit, and integration tests on the remote validation environment.
- Known limitation: real nf-core execution requires site-provided Java 17+, Nextflow, and a container backend.
- v0.2 acceptance work starts from project-local Java/Nextflow activation and real nf-core test-profile enforcement when preflight passes.
