# Acceptance Matrix

| Area | Supported | Verification | Out of scope |
|---|---|---|---|
| Plugin package | Metadata, skills, common scripts, schemas, references, examples | release package check | Marketplace publication |
| single-cell-rna-qc | env check, input validation, dry-run, approved QC, manifest/report | script smoke and synthetic h5ad tests | automatic biological interpretation |
| scvi-tools | env check, model listing, AnnData validation, dry-run, approved training | gpu03 SCVI small training completed | blind GPU stack installation |
| nextflow-development | env check, FASTQ detection, samplesheet, command build, optional pull-timeout config, approved execution wrapper | RNA-seq completed on gpu03 after manual container cache plus `-resume`; container pull timeout classified; ATAC plan completed | guaranteed HPC execution or remote container registry performance |
| Router | skill selection by prompt and input inspection | plugin-local router smoke test | every custom assay inference |
| Report | manifest-to-Markdown rendering with skill-specific key results | plugin-local report renderer test | publication-ready interpretation |
| Install planner | UV, venv, conda/mamba, and system Python install planning | plan-only test | silent heavy dependency installation |
| Safety | dry-run first, approval required for long tasks | manifest/report tests | silent dependency installation |

## Remote nf-core note

The gpu03 RNA-seq acceptance run confirmed the plugin command path and nf-core execution through completion. The remote server's container downloads from `depot.galaxyproject.org` were slow enough to exceed Nextflow's default `singularity.pullTimeout` of `20m` for uncached images; the final successful path manually cached the missing image and resumed the existing run. Use `build_nextflow_command.py --pull-timeout "4 h" --overwrite-reports --resume` or pre-cache required Singularity/Apptainer images before retrying on slow HPC networks.
