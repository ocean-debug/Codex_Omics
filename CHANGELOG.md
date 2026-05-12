# Changelog

## 0.1.0

- Initial public usability release.
- Added repo-local Codex plugin structure with nf-core, scRNA QC, scVI, router, report, and skill-template skills.
- Added `omics-codex` CLI for validation, workflow planning/running, reports, nf-core helpers, scRNA QC, and scVI workflows.
- Added safe-by-default workflow examples; unapproved workflow configs plan only, while approved examples are explicit.
- Added manifests and markdown reports for run provenance.
- Verified smoke, unit, and integration tests on the remote validation environment.
- Known limitation: real nf-core execution requires site-provided Java 17+, Nextflow, and a container backend.
