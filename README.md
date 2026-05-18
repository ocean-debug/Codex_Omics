# Codex-Omics

Codex-Omics is a Codex plugin for reproducible omics analysis. It provides
plugin-local skills for single-cell QC, scvi-tools workflows, nf-core/Nextflow
planning, routing, reporting, and skill authoring.

The plugin is the product: load `plugins/omics-analysis/` in Codex and use the
bundled `SKILL.md` files plus local scripts. There is no backend CLI
requirement.

## What It Provides

| Skill | Use for |
|---|---|
| `omics-router` | Choose the right skill from user intent, input inventory, constraints, and registered capabilities. |
| `single-cell-rna-qc` | Validate `.h5ad` or 10x inputs, plan/run QC, write filtered AnnData, plots, manifest, and report. |
| `scvi-tools` | Recommend SCVI/SCANVI/TOTALVI/PEAKVI/MULTIVI, validate AnnData, plan/train approved models, record diagnostics. |
| `nextflow-development` | Generate nf-core samplesheets, build `command.sh` and `params.yaml`, parse MultiQC, run only after approval. |
| `omics-report` | Render seven-section Markdown reports from run manifests. |
| `skill-authoring-kit` | Add new plugin-local bioinformatics skills or extend existing adapters. |

Skills are registered in `plugins/omics-analysis/skill_registry.yaml`, so the
router and release checks can discover scripts, schemas, outputs, approval
rules, examples, and workflow diagrams.

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
| single-cell QC | `scanpy`, `anndata`, `numpy`, `scipy`, `pandas`, plotting libraries |
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
