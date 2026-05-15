# Remote Validation

Remote validation should use the plugin-local scripts directly.

Default checks:

```bash
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/check_environment.py --json
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --help
python plugins/omics-analysis/skills/scvi-tools/scripts/check_environment.py --json
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --help
python plugins/omics-analysis/skills/nextflow-development/scripts/check_environment.py --json
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --help
python scripts/release/build_plugin_package.py
python scripts/release/check_release.py --plugin-package dist/codex-omics-plugin-v1.0.0.zip
```

Heavy checks are opt-in and require explicit user approval.
