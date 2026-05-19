# Acceptance Matrix

| Area | Supported | Verification | Out of scope |
|---|---|---|---|
| Plugin package | Metadata, skills, common scripts, schemas, references, examples | release package check | Marketplace publication |
| single-cell-rna-qc | env check, input validation, dry-run, approved QC, manifest/report | script smoke and synthetic h5ad tests | automatic biological interpretation |
| single-cell-preprocess | env check, h5ad validation, dry-run, approved normalization/log1p/HVG/PCA/neighbors/UMAP/Leiden, manifest/report | gpu03 validation covered router, dry-run, approved synthetic h5ad run, summarize, and `47 passed` pytest | batch-aware integration or annotation |
| scvi-tools | env check, model recommendation, model listing, AnnData validation, dry-run, approved training, lightweight training diagnostics | gpu03 SCVI small training completed; registry/router validation smoke covered model recommendation | blind GPU stack installation or publication-grade benchmark metrics |
| nextflow-development | env check, FASTQ/spatial detection, samplesheet, command build, `params.yaml`, optional pull-timeout config, approved execution wrapper, MultiQC parsing, error recovery suggestions | RNA-seq completed on gpu03 after manual container cache plus `-resume`; container pull timeout classified; ATAC plan completed; registry/router validation smoke covered `params.yaml` and MultiQC parser | guaranteed HPC execution or remote container registry performance |
| Router | registry-driven skill selection using prompt intent, input inventory, constraints, candidate scores, and structured `router_plan` | gpu03 registry/router validation: scvi, QC, report, new-skill, and Nextflow planning smoke tests passed | every custom assay inference |
| Report | seven-section manifest-to-Markdown rendering with QC interpretation and suggested fixes | gpu03 registry/router validation covered failed manifest, interpretation, warnings, errors, commands, and auto-fix plan rendering | publication-ready biological interpretation |
| Install planner | UV, venv, conda/mamba, and system Python install planning | plan-only test | silent heavy dependency installation |
| Safety | dry-run first, approval required for long tasks | manifest/report tests | silent dependency installation |

## Remote nf-core note

The gpu03 RNA-seq acceptance run confirmed the plugin command path and nf-core execution through completion. The remote server's container downloads from `depot.galaxyproject.org` were slow enough to exceed Nextflow's default `singularity.pullTimeout` of `20m` for uncached images; the final successful path manually cached the missing image and resumed the existing run. Use `build_nextflow_command.py --pull-timeout "4 h" --overwrite-reports --resume` or pre-cache required Singularity/Apptainer images before retrying on slow HPC networks.

## Registry/router validation note

On 2026-05-18, gpu03 validation for the registry-driven architecture completed
under `/home/hywang/codex/codex_omics/data/test/result/registry_router_validation_20260518/`.
The run used Python 3.12.13, node `gpu03`, and 12 cores. The validation covered
`compileall`, `check_release.py`, `pytest`, registry loading without PyYAML,
structured router plans, scvi model recommendation, Nextflow `params.yaml`
generation with parameter audit, MultiQC parsing, and seven-section failed
manifest report rendering. Result: `43 passed in 36.59s`, overall status `ok`.

## Single-cell preprocess validation note

On 2026-05-19, gpu03 validation for `single-cell-preprocess` completed under
`/home/hywang/codex/codex_omics/data/test/result/single_cell_preprocess_skill_20260519/`.
The run covered `compileall`, `check_release.py`, full `pytest`, router
selection, dry-run manifest/report, approved preprocessing on a synthetic h5ad,
and manifest summarization. Result: `47 passed in 43.13s`, overall status `ok`.
The approved smoke wrote PCA, neighbors, UMAP, `preprocessed.h5ad`,
`preprocess_summary.json`, `run_manifest.json`, and `report.md`; missing
`leidenalg` was recorded as a `LeidenSkipped` warning instead of failing the
run.
