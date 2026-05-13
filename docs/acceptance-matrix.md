# Acceptance Matrix

This matrix records the current v1 acceptance boundary for Codex Omics Skills.

| Area | Supported | Default validation | Heavy-only | Not promised |
| --- | --- | --- | --- | --- |
| Workflow orchestration | Safe-by-default multi-stage `workflow plan/run/resume/status`, `scrna_qc -> scvi` handoff, aggregate manifest/report, failed stage manifests for expected and unexpected exceptions | Synthetic QC-to-SCVI workflow | Larger real datasets | Arbitrary DAG schedulers |
| nf-core | Registry, schema fetch, params fallback validation, command generation, `rnaseq/sarek/atacseq` samplesheets, output inventory, project-local Java/Nextflow activation, project-local Singularity cache/config | Command generation, environment inspection, and output inventory | `nf-core/rnaseq` test profile with MultiQC inventory must complete when preflight passes | Every nf-core pipeline end-to-end |
| scRNA QC | h5ad, 10x MTX, raw-count check, MAD/fixed filters, batch-aware summary, optional doublet/ambient planning notes | Synthetic h5ad and small 10x MTX fixture | Real 10x H5/large MTX | Full doublet/ambient correction by default |
| scVI | SCVI train, curated adapter validation, latent/downstream outputs, model summaries | SCVI synthetic train and curated validation | SCANVI/TOTALVI/PEAKVI/MULTIVI light training | Biological interpretation |
| Reporting | Methods-ready markdown from manifests, summaries, software, commands, errors, next steps | Manifest/report rendering | Full pipeline reports from large outputs | Publication-ready narrative |
| Extensibility | Skill template generator with SKILL.md, schema, example, test stubs | Unit template generation | Forward-testing new domain skills | Auto-implementing arbitrary papers |
