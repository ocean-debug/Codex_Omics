---
name: nextflow-development
description: Build, dry-run, and execute approved Nextflow or nf-core omics workflows from FASTQ inputs using plugin-local scripts. Use for nf-core/rnaseq, nf-core/atacseq, nf-core/sarek, FASTQ samplesheets, Nextflow command construction, environment checks, execution logs, manifests, reports, and troubleshooting Java, Nextflow, nf-core, Singularity, Apptainer, Docker, git, or pipeline pull failures.
---

# Nextflow Development

Use plugin-local scripts only.

## Workflow

1. Check the environment:
   `python plugins/omics-analysis/skills/nextflow-development/scripts/check_environment.py --json`
2. Detect the input data type when the user provides a directory.
3. Generate a samplesheet for `rnaseq`, `atacseq`, or `sarek` when FASTQ files are present.
4. Build a Nextflow command in dry-run mode.
5. Execute only after explicit user approval with `--approved true`.
6. Preserve `command.sh`, logs, `run_manifest.json`, and `report.md`.

## RNA-seq resume guidance

The validated nf-core/rnaseq path is: check the environment, generate the samplesheet, build the command with the Singularity or Apptainer profile, run only after approval, inspect `run_manifest.json` and `report.md`, then use `-resume` for any retry.

On slow HPC networks, uncached images from `depot.galaxyproject.org` can exceed Nextflow's default container pull timeout. Prefer one of these approaches before retrying:

- Build the command with `--pull-timeout "4 h" --overwrite-reports --resume`.
- Pre-cache the missing Singularity/Apptainer image in the configured Nextflow container cache, then rerun with `-resume`.
- If registry download speed is the only blocker during server acceptance testing, avoid repeated full reruns after confirming the bottleneck.

## Commands

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/check_environment.py --json
python plugins/omics-analysis/skills/nextflow-development/scripts/detect_data_type.py --input fastq_dir --json
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline rnaseq --input fastq_dir --out samplesheet.csv
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline rnaseq --input samplesheet.csv --outdir results/rnaseq --profile singularity --pull-timeout "4 h" --overwrite-reports --resume --dry-run --json
python plugins/omics-analysis/skills/nextflow-development/scripts/run_nextflow.py --config nfcore_run.yaml --approved true
```

## Safety

- Default to dry-run or planned status.
- Require `--approved true` for real Nextflow execution.
- Do not install Java, Nextflow, nf-core, or container tooling without explicit user approval.
- Keep user data local and write outputs only under the requested output directory.

## References

- Read `references/execution-policy.md` before approved execution.
- Read `references/samplesheets.md` when creating or reviewing samplesheets.
