# Remote Validation

Remote validation should use the plugin-local scripts directly.

Default checks:

```bash
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --help
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
