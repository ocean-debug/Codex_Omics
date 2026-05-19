# Remote Validation

Remote validation should use the plugin-local scripts directly.

Default checks:

```bash
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --help
python plugins/omics-analysis/skills/single-cell-preprocess/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-preprocess/scripts/run.py --help
python plugins/omics-analysis/skills/single-cell-integration/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-integration/scripts/run.py --help
python plugins/omics-analysis/skills/single-cell-annotation/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-annotation/scripts/run.py --help
python plugins/omics-analysis/skills/single-cell-marker-de/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-marker-de/scripts/run.py --help
python plugins/omics-analysis/skills/pathway-enrichment/scripts/check_environment.py --json
python plugins/omics-analysis/skills/pathway-enrichment/scripts/run.py --help
python plugins/omics-analysis/skills/bulk-rna-de/scripts/check_environment.py --json
python plugins/omics-analysis/skills/bulk-rna-de/scripts/run.py --help
python plugins/omics-analysis/skills/scrna-standard-workflow/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scrna-standard-workflow/scripts/run.py --help
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/recommend_model.py --input cells.h5ad --task "batch correction" --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --help
python plugins/omics-analysis/skills/nextflow-development/scripts/check_environment.py --json
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --help
python scripts/release/build_plugin_package.py
python scripts/release/check_release.py --plugin-package dist/codex-omics-plugin-v1.0.0.zip
```

Heavy checks are opt-in and require explicit user approval.

## 2026-05-18 registry/router validation

Validated on the user-managed remote workspace:

```text
workdir: /home/hywang/codex/codex_omics/
node: gpu03
cores: 12
environment: source .venv/bin/activate
result: /home/hywang/codex/codex_omics/data/test/result/registry_router_validation_20260518/
```

Checks completed:

```bash
python -m compileall -q plugins scripts tests
python scripts/release/check_release.py
python -m pytest tests -q
```

Smoke coverage included registry loading without PyYAML, router plans for scvi,
QC, report, and new-skill requests, scvi model recommendation, Nextflow
`params.yaml` generation plus parameter audit, MultiQC parsing, and failed
manifest report rendering. Result: `43 passed in 36.59s`, overall status `ok`.

## 2026-05-19 single-cell-preprocess validation

Validated on the same remote workspace:

```text
workdir: /home/hywang/codex/codex_omics/
node: gpu03
cores: 12
environment: source .venv/bin/activate
result: /home/hywang/codex/codex_omics/data/test/result/single_cell_preprocess_skill_20260519/
```

Final rerun summary:

```text
compileall returncode=0
check_release returncode=0
pytest returncode=0
router_preprocess returncode=0
preprocess_dry_run returncode=0
preprocess_approved returncode=0
preprocess_summarize returncode=0
pytest: 47 passed in 43.13s
overall_status: ok
```

The approved synthetic h5ad smoke wrote `preprocessed.h5ad`,
`preprocess_summary.json`, `run_manifest.json`, and `report.md`. The remote
environment lacked `leidenalg`; the skill recorded this as `LeidenSkipped` and
continued with PCA, neighbors, and UMAP.

## 2026-05-19 single-cell-integration validation

Validated on the same remote workspace:

```text
workdir: /home/hywang/codex/codex_omics/
node: gpu03
cores: 12
environment: source .venv/bin/activate
result: /home/hywang/codex/codex_omics/data/test/result/single_cell_integration_skill_20260519/
```

Final summary:

```text
compileall returncode=0
check_release returncode=0
pytest returncode=0
router_integration returncode=0
validate_integration returncode=0
dry_run_integration returncode=0
approved_integration returncode=0
blocked_harmony returncode=0
summarize_integration_retry returncode=0
pytest: 68 passed in 121.48s
overall_status: ok
```

The approved synthetic h5ad smoke wrote `integrated.h5ad`,
`integration_summary.json`, `batch_diagnostics.csv`, `run_manifest.json`, and
`report.md`. The synthetic run integrated 12 cells across two batches using
`scanpy-combat`; Harmony and Scanorama were unavailable in the remote
environment and were recorded as blocked optional backends.

## 2026-05-19 single-cell-marker-de validation

Validated on the same remote workspace:

```text
workdir: /home/hywang/codex/codex_omics/
node: gpu03
cores: 12
environment: source .venv/bin/activate
result: /home/hywang/codex/codex_omics/data/test/result/single_cell_marker_de_skill_20260519/
```

Final rerun summary:

```text
compileall returncode=0
check_release returncode=0
pytest returncode=0
router_marker_de returncode=0
router_report returncode=0
marker_dry_run returncode=0
marker_validate returncode=0
marker_approved returncode=0
marker_summarize returncode=0
pytest: 50 passed in 49.62s
overall_status: ok
```

The approved synthetic h5ad smoke wrote `markers.csv`, `de_summary.json`,
`run_manifest.json`, and `report.md`. The output contained 60 marker rows
across three synthetic Leiden groups, and the top marker genes matched the
group-specific synthetic signal.

## 2026-05-19 single-cell-annotation validation

Validated on the same remote workspace:

```text
workdir: /home/hywang/codex/codex_omics/
node: gpu03
cores: 12
environment: source .venv/bin/activate
result: /home/hywang/codex/codex_omics/data/test/result/single_cell_annotation_skill_20260519/
```

Final summary:

```text
compileall returncode=0
check_release returncode=0
pytest returncode=0
router_annotation returncode=0
annotation_validate returncode=0
annotation_dry_run returncode=0
annotation_approved returncode=0
annotation_blocked_celltypist returncode=0
annotation_summarize returncode=0
pytest: 62 passed in 80.92s
overall_status: ok
```

The approved marker-based synthetic h5ad smoke wrote `annotated.h5ad`,
`annotations.csv`, `annotation_confidence.csv`, `annotation_summary.json`,
`run_manifest.json`, and `report.md`. The output assigned high-confidence
T cell and B cell labels. The CellTypist backend smoke wrote a blocked manifest
with `CellTypistUnavailable` and `MissingCellTypistModel` suggestions instead
of downloading resources.

## 2026-05-19 pathway-enrichment validation

Validated on the same remote workspace:

```text
workdir: /home/hywang/codex/codex_omics/
node: gpu03
cores: 12
environment: source .venv/bin/activate
result: /home/hywang/codex/codex_omics/data/test/result/pathway_enrichment_skill_20260519/
```

Final summary:

```text
compileall returncode=0
check_release returncode=0
pytest returncode=0
router_pathway returncode=0
router_report returncode=0
pathway_validate returncode=0
pathway_dry_run returncode=0
pathway_approved returncode=0
pathway_summarize returncode=0
pytest: 53 passed in 50.33s
overall_status: ok
```

The approved synthetic marker/GMT smoke wrote `enrichment.csv`,
`enrichment_summary.json`, `run_manifest.json`, and `report.md`. The output
contained significant synthetic hits for `Pathway_0` and `Pathway_1`.

## 2026-05-19 bulk-rna-de validation

Validated on the same remote workspace:

```text
workdir: /home/hywang/codex/codex_omics/
node: gpu03
cores: 12
environment: source .venv/bin/activate
result: /home/hywang/codex/codex_omics/data/test/result/bulk_rna_de_skill_20260519/
```

Final summary:

```text
compileall returncode=0
check_release returncode=0
pytest returncode=0
router_bulk returncode=0
bulk_validate returncode=0
bulk_dry_run returncode=0
bulk_approved returncode=0
bulk_summarize returncode=0
pytest: 57 passed in 51.11s
overall_status: ok
```

The approved synthetic count/metadata smoke wrote `de_results.csv`,
`de_summary.json`, `run_manifest.json`, and `report.md`. The output flagged two
synthetic genes in a treatment-vs-control exploratory contrast.

## 2026-05-19 scrna-standard-workflow validation

Validated on the same remote workspace:

```text
workdir: /home/hywang/codex/codex_omics/
node: gpu03
cores: 12
environment: source .venv/bin/activate
result: /home/hywang/codex/codex_omics/data/test/result/scrna_standard_workflow_skill_20260519/
```

Final summary:

```text
compileall returncode=0
check_release returncode=0
pytest returncode=0
router_workflow returncode=0
validate_workflow returncode=0
dry_run_workflow returncode=0
approved_plan_only returncode=0
skip_plan returncode=0
summarize_workflow returncode=0
pytest: 72 passed in 122.01s
overall_status: ok
```

The workflow smoke wrote `workflow_plan.json`, `workflow_plan.md`,
`run_manifest.json`, and `report.md`. The default plan contains seven child
steps from QC through report rendering; the skip-plan smoke confirmed optional
integration, annotation, and enrichment branches can be omitted without
executing child analyses.
