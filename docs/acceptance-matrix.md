# Acceptance Matrix

This matrix records the current v0.3 acceptance boundary for Codex Omics Skills.

| Area | Supported | Default validation | Heavy-only | Not promised |
| --- | --- | --- | --- | --- |
| Workflow orchestration | Safe-by-default multi-stage `workflow plan/run/resume/status`, `scrna_qc -> scvi` handoff, aggregate manifest/report, failed stage manifests for expected and unexpected exceptions | Synthetic QC-to-SCVI workflow | Larger real datasets | Arbitrary DAG schedulers |
| Router/templates | Input inspection plus safe spec generation from natural language or common templates: `bulk-rna`, `atac`, `scrna-qc`, `scrna-qc-scvi`, `scvi` | Route/template CLI generation with `approved: false` | Real user directory smoke checks | Perfect natural-language understanding |
| nf-core | Registry, schema fetch, params fallback validation, command generation, `rnaseq/sarek/atacseq` samplesheets, output inventory, project-local Java/Nextflow activation, project-local Singularity cache/config, runtime blockers and Nextflow failure classification | Command generation, structured environment inspection, route/template specs, and output inventory | `nf-core/rnaseq` test profile and real bulk RNA subset with MultiQC inventory must complete when preflight passes; ATAC true execution is out of the v0.3 routine validation path | Every nf-core pipeline end-to-end |
| scRNA QC | h5ad, 10x MTX, raw-count check, MAD/fixed filters, batch-aware summary, optional doublet/ambient planning notes | Synthetic h5ad and small 10x MTX fixture | Real 10x H5/large MTX | Full doublet/ambient correction by default |
| scVI | SCVI train, curated adapter validation, latent/downstream outputs, model summaries, UV/GPU/PyTorch environment diagnostics | SCVI synthetic train, curated validation, and structured `inspect-env --kind scvi` | SCANVI/TOTALVI/PEAKVI/MULTIVI light training; real h5ad subset SCVI training | Biological interpretation |
| Reporting | Methods-ready markdown from manifests, summaries, software, commands, errors, next steps | Manifest/report rendering | Full pipeline reports from large outputs | Publication-ready narrative |
| Extensibility | Skill template generator with SKILL.md, schema, example, test stubs | Unit template generation | Forward-testing new domain skills | Auto-implementing arbitrary papers |

## Real-data acceptance policy

`scripts/acceptance/run_all.sh` remains available for site-specific real-data
checks. For v0.3 usability work, scVI and bulk RNA are the active real-data
acceptance paths. ATAC command/spec/report compatibility is retained, but ATAC
true execution is not a routine blocker unless explicitly brought back in
scope.
