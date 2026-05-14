# Changelog

## Unreleased

- Set project-local Nextflow activation to `NXF_SYNTAX_PARSER=v1` for compatibility with nf-core pipelines that still use legacy config syntax.
- Added ATAC acceptance auto-detection for `read_length`, with `CODEX_OMICS_ATAC_READ_LENGTH` and `CODEX_OMICS_ATAC_MACS_GSIZE` overrides.
- Classified ATAC `--read_length` / `--macs_gsize`, samplesheet, and container-pull failures more precisely.
- Added project-local Apptainer cache settings alongside Singularity cache settings.

## 0.2.1

- Hardened real-data acceptance aggregation: `scripts/acceptance/run_all.sh` now runs all projects, writes per-project exit codes, produces a machine-readable `summary.json`, and exits nonzero when required `scvi` or `bulk_rna` checks fail.
- Added an explicit ATAC acceptance policy: ATAC may remain failed/blocked only when the manifest contains a known classified pipeline pull, config-parse, or container-pull failure with preserved commands and logs.
- Improved nf-core environment consistency by treating unparseable Java versions as blockers in both `inspect-env --kind nfcore` and runtime preflight.
- Strengthened acceptance input preparation with early structured errors for missing h5ad, missing paired FASTQ files, missing genome FASTA/GTF, and empty samplesheets.
- Extended FASTQ discovery to common `_1/_2` and `_R1/_R2` naming with `.fq.gz` or `.fastq.gz`.
- Improved router-generated specs from real input directories, including FASTQ pair counts, h5ad discovery, reference file hints, safe `approved: false` defaults, and software requirements.

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
