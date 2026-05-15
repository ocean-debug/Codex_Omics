# Acceptance Matrix

| Area | Supported | Verification | Out of scope |
|---|---|---|---|
| Plugin package | Metadata, skills, common scripts, schemas, references, examples | release package check | Marketplace publication |
| single-cell-rna-qc | env check, input validation, dry-run, approved QC, manifest/report | script smoke and synthetic h5ad tests | automatic biological interpretation |
| scvi-tools | env check, model listing, AnnData validation, dry-run, approved training | script smoke and optional synthetic training | blind GPU stack installation |
| nextflow-development | env check, FASTQ detection, samplesheet, command build, approved execution wrapper | script smoke and command fixtures | guaranteed HPC execution |
| Router | skill selection by prompt and input inspection | plugin-local router smoke test | every custom assay inference |
| Report | manifest-to-Markdown rendering with skill-specific key results | plugin-local report renderer test | publication-ready interpretation |
| Install planner | UV, venv, conda/mamba, and system Python install planning | plan-only test | silent heavy dependency installation |
| Safety | dry-run first, approval required for long tasks | manifest/report tests | silent dependency installation |
