---
name: nf-core-universal
description: Compatibility alias for the migrated nextflow-development skill. Use nextflow-development for plugin-local nf-core/Nextflow environment checks, samplesheets, command construction, approved execution, manifests, and reports.
---

# nf-core-universal migrated

Use `plugins/omics-analysis/skills/nextflow-development/` instead.

The supported plugin-local entrypoints are:

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/check_environment.py --json
python plugins/omics-analysis/skills/nextflow-development/scripts/detect_data_type.py --input fastq_dir --json
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline rnaseq --input fastq_dir --out samplesheet.csv
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline rnaseq --input samplesheet.csv --outdir results/rnaseq --profile singularity --pull-timeout "4 h" --overwrite-reports --resume --dry-run --json
```

For slow HPC container registries, follow the migrated `nextflow-development` execution policy: increase pull timeout, pre-cache missing Singularity/Apptainer images when needed, and rerun with `-resume` instead of restarting from scratch.
