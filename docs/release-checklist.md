# Release Checklist

Before release:

```bash
python -m compileall -q plugins scripts tests
python plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py --help
python plugins/omics-analysis/skills/single-cell-preprocess/scripts/run.py --help
python plugins/omics-analysis/skills/scvi-tools/scripts/recommend_model.py --help
python plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py --help
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --help
python plugins/omics-analysis/skills/omics-router/scripts/route_omics.py --help
python plugins/omics-analysis/skills/omics-report/scripts/render_report.py --help
python plugins/omics-analysis/scripts/common/install_planner.py --help
python scripts/release/build_plugin_package.py
python scripts/release/check_release.py --plugin-package dist/codex-omics-plugin-v1.0.0.zip
```

Confirm:

- P0 scripts do not import the removed backend package.
- Plugin package does not include private paths, caches, tools, results, virtual environments, or large data.
- P0 scripts support `--help`, `--json`, `--dry-run`, `--approved`, and `--write-manifest`.
- Long-running execution requires explicit approval.
- Registry entries reference existing scripts, schemas, examples, router keywords, and workflow diagrams.
- Reports render the seven required sections and preserve errors, warnings, commands, interpretation, and suggested fixes.
