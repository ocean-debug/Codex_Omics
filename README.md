# Codex-Omics

Codex-Omics is a Codex plugin for reproducible omics analysis. It provides
plugin-local skills for single-cell QC/preprocessing/integration/annotation/marker analysis,
pathway enrichment, bulk RNA DE, scvi-tools workflows, nf-core/Nextflow planning, routing,
reporting, and skill authoring.

The plugin is the product: load `plugins/omics-analysis/` in Codex and use the
bundled `SKILL.md` files plus local scripts. There is no backend CLI
requirement.

## What It Provides

| Skill | Use for |
|---|---|
| `omics-router` | Choose the right skill from user intent, input inventory, constraints, and registered capabilities. |
| `single-cell-rna-qc` | Validate `.h5ad` or 10x inputs, plan/run QC, write filtered AnnData, plots, manifest, and report. |
| `single-cell-preprocess` | Normalize/log-transform filtered `.h5ad`, mark HVGs, build PCA/neighbors/UMAP/Leiden, and write a preprocessed AnnData plus report. |
| `single-cell-integration` | Integrate batches from preprocessed `.h5ad`; default approved backend is Scanpy ComBat, with SCVI/Harmony/Scanorama planned or blocked cleanly. |
| `single-cell-annotation` | Assign cell type labels from local marker references, or plan CellTypist/SingleR/SCANVI annotation with blocked manifests when resources are missing. |
| `single-cell-marker-de` | Rank marker genes or group-vs-rest DE from preprocessed `.h5ad`, write marker table, summary, manifest, and report. |
| `pathway-enrichment` | Run lightweight ORA from marker tables or gene lists against local GMT/CSV gene sets, then write enrichment table and report. |
| `bulk-rna-de` | Run exploratory count-table bulk RNA DE from local counts, metadata, and explicit contrast, then write DE table and report. |
| `scrna-standard-workflow` | Generate a plan-only end-to-end scRNA workflow that composes QC, preprocess, integration, annotation, marker, enrichment, and report steps. |
| `scvi-tools` | Recommend SCVI/SCANVI/TOTALVI/PEAKVI/MULTIVI, validate AnnData, plan/train approved models, record diagnostics. |
| `nextflow-development` | Generate nf-core samplesheets, build `command.sh` and `params.yaml`, parse MultiQC, run only after approval. |
| `omics-report` | Render seven-section Markdown reports from run manifests. |
| `skill-authoring-kit` | Add new plugin-local bioinformatics skills or extend existing adapters. |

Skills are registered in `plugins/omics-analysis/skill_registry.yaml`, so the
router and release checks can discover scripts, schemas, outputs, approval
rules, examples, and workflow diagrams.

## Skill Architecture

Codex-Omics keeps skill directories flat and records hierarchy in the registry:

| Layer | Purpose | Current examples |
|---|---|---|
| `system` | Routing, reporting, authoring, and safety infrastructure. | `omics-router`, `omics-report`, `skill-authoring-kit` |
| `task` | User-facing analysis tasks with stable inputs and outputs. | `single-cell-rna-qc`, `single-cell-preprocess`, `single-cell-integration`, `single-cell-annotation`, `single-cell-marker-de`, `pathway-enrichment`, `bulk-rna-de` |
| `tool_family` | Adapters for complex tool ecosystems used by task skills. | `scvi-tools`, `nextflow-development` |
| `workflow` | Plan and compose multiple skills into an end-to-end workflow. | `scrna-standard-workflow` |

Task skills answer **what to do**, tool-family skills answer **what to use**,
and workflow skills answer **how to chain steps**. New skills should stay in
`skills/<skill-id>/` and declare `layer`, `domain`, `backends`, `composes`,
`public_entrypoint`, and `maturity` in `skill_registry.yaml`.

## Quick Start

Use the plugin directory directly during development:

```text
plugins/omics-analysis/
```

For release use, build or download the zip package, extract it, and load the
extracted `omics-analysis/` plugin directory:

```bash
python scripts/release/build_plugin_package.py
python scripts/release/check_release.py --plugin-package dist/codex-omics-plugin-v1.0.0.zip
```

Route a request:

```bash
python plugins/omics-analysis/skills/omics-router/scripts/route_omics.py \
  --prompt "run rnaseq workflow" \
  --input data \
  --outdir results/route \
  --json
```

Run skill scripts in the same pattern:

```bash
# Plan single-cell QC
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py \
  --input cells.h5ad \
  --output-dir results/qc \
  --dry-run \
  --json

# Plan single-cell preprocessing after QC
python plugins/omics-analysis/skills/single-cell-preprocess/scripts/run.py \
  --input results/qc/filtered.h5ad \
  --output-dir results/preprocess \
  --dry-run \
  --json

# Plan batch integration after preprocessing
python plugins/omics-analysis/skills/single-cell-integration/scripts/run.py \
  --input results/preprocess/preprocessed.h5ad \
  --output-dir results/integration \
  --backend scanpy-combat \
  --batch-key batch \
  --dry-run \
  --json

# Plan marker detection after preprocessing
python plugins/omics-analysis/skills/single-cell-marker-de/scripts/run.py \
  --input results/preprocess/preprocessed.h5ad \
  --output-dir results/markers \
  --groupby leiden \
  --dry-run \
  --json

# Plan marker-based cell type annotation
python plugins/omics-analysis/skills/single-cell-annotation/scripts/run.py \
  --input results/preprocess/preprocessed.h5ad \
  --output-dir results/annotation \
  --backend marker-based \
  --marker-reference data/marker_reference.csv \
  --groupby leiden \
  --dry-run \
  --json

# Plan pathway enrichment from marker genes
python plugins/omics-analysis/skills/pathway-enrichment/scripts/run.py \
  --input results/markers/markers.csv \
  --gene-sets data/gene_sets.gmt \
  --output-dir results/enrichment \
  --dry-run \
  --json

# Plan an end-to-end scRNA workflow without executing child steps
python plugins/omics-analysis/skills/scrna-standard-workflow/scripts/run.py \
  --input cells.h5ad \
  --output-dir results/scrna_workflow \
  --dry-run \
  --json

# Plan bulk RNA DE from local counts and metadata
python plugins/omics-analysis/skills/bulk-rna-de/scripts/run.py \
  --counts counts.csv \
  --metadata metadata.csv \
  --contrast condition:control:treatment \
  --output-dir results/bulk_de \
  --dry-run \
  --json

# Recommend an scvi-tools model
python plugins/omics-analysis/skills/scvi-tools/scripts/recommend_model.py \
  --input cells.h5ad \
  --task "batch correction" \
  --json

# Build an nf-core command without executing it
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py \
  --pipeline rnaseq \
  --input samplesheet.csv \
  --outdir results/rnaseq \
  --profile singularity \
  --dry-run \
  --json
```

Long-running execution remains explicit:

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/run_nextflow.py \
  --config nfcore_run.yaml \
  --approved true
```

## Supported nf-core Adapters

`nextflow-development` currently includes lightweight adapters for:

- `nf-core/rnaseq`
- `nf-core/scrnaseq`
- `nf-core/riboseq`
- `nf-core/spatialvi`
- `nf-core/atacseq`
- `nf-core/sarek`

To add another nf-core workflow, start from:

```text
plugins/omics-analysis/skills/nextflow-development/references/nfcore-workflow-adapter-template.md
```

For a new non-nf-core analysis capability, create a task-level skill first.
Create a tool-family skill only when multiple task skills need the same complex
backend. Create a workflow skill only when composing existing skills.

## Safety Model

Codex-Omics is plan-first.

- Dry-run or planned mode is the default.
- Real Nextflow execution, scvi training, heavy downloads, dependency
  installation, and destructive actions require explicit approval.
- Scripts write `run_manifest.json` and `report.md` when they plan or execute a
  workflow.
- The plugin does not silently install Java, Nextflow, nf-core, container
  runtimes, scverse, scvi-tools, GPU PyTorch, or reference data.

## Requirements

Base plugin scripts use Python 3.10+ and the standard library.

Analysis runtimes are provided by the user environment and checked per skill:

| Area | Typical requirements |
|---|---|
| single-cell QC/preprocess/integration | `scanpy`, `anndata`, `numpy`, `scipy`, `pandas`, plotting libraries for QC; optional `scvi-tools`, `harmonypy`, or `scanorama` for non-default integration backends |
| single-cell annotation | `scanpy`, `anndata`, `numpy`, `pandas`, plus local marker/model/reference resources |
| pathway enrichment | Python standard library plus local GMT/CSV gene sets |
| bulk RNA DE | Python standard library plus local counts, metadata, and explicit contrast |
| scvi-tools | `scvi-tools`, `torch`, `scanpy`, `anndata`, optional GPU |
| Nextflow/nf-core | Java 17+, Nextflow, nf-core, git, Singularity/Apptainer or Docker |

## Validation

Local release checks:

```bash
python -m compileall -q plugins scripts tests
python scripts/release/build_plugin_package.py
python scripts/release/check_release.py --plugin-package dist/codex-omics-plugin-v1.0.0.zip
```

Remote validation on `gpu03` completed on 2026-05-18:

```text
result: /home/hywang/codex/codex_omics/data/test/result/registry_router_validation_20260518/
pytest: 43 passed in 36.59s
overall_status: ok
```

See `docs/acceptance-matrix.md` and `docs/remote-validation.md` for details.

Additional `single-cell-preprocess` validation completed on `gpu03` on
2026-05-19:

```text
result: /home/hywang/codex/codex_omics/data/test/result/single_cell_preprocess_skill_20260519/
pytest: 47 passed in 43.13s
overall_status: ok
```

Additional `single-cell-integration` validation completed on `gpu03` on
2026-05-19:

```text
result: /home/hywang/codex/codex_omics/data/test/result/single_cell_integration_skill_20260519/
pytest: 68 passed in 121.48s
overall_status: ok
```

Additional `single-cell-marker-de` validation completed on `gpu03` on
2026-05-19:

```text
result: /home/hywang/codex/codex_omics/data/test/result/single_cell_marker_de_skill_20260519/
pytest: 50 passed in 49.62s
overall_status: ok
```

Additional `single-cell-annotation` validation completed on `gpu03` on
2026-05-19:

```text
result: /home/hywang/codex/codex_omics/data/test/result/single_cell_annotation_skill_20260519/
pytest: 62 passed in 80.92s
overall_status: ok
```

Additional `pathway-enrichment` validation completed on `gpu03` on 2026-05-19:

```text
result: /home/hywang/codex/codex_omics/data/test/result/pathway_enrichment_skill_20260519/
pytest: 53 passed in 50.33s
overall_status: ok
```

Additional `bulk-rna-de` validation completed on `gpu03` on 2026-05-19:

```text
result: /home/hywang/codex/codex_omics/data/test/result/bulk_rna_de_skill_20260519/
pytest: 57 passed in 51.11s
overall_status: ok
```

Additional `scrna-standard-workflow` validation completed on `gpu03` on
2026-05-19:

```text
result: /home/hywang/codex/codex_omics/data/test/result/scrna_standard_workflow_skill_20260519/
pytest: 72 passed in 122.01s
overall_status: ok
```

## Repository Layout

```text
plugins/omics-analysis/
  .codex-plugin/plugin.json
  skill_registry.yaml
  skills/
  scripts/common/
  schemas/
docs/
tests/
scripts/release/
```

## Scope

Codex-Omics helps Codex plan, validate, report, and run approved omics
workflows. It does not guarantee that every dataset, HPC profile, network,
container registry, reference genome, or GPU stack will work without
environment preparation.

Marketplace publication is outside the repository release checks.

## License

MIT
