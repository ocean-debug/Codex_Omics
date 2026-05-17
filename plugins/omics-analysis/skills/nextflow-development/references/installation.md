# Nextflow Environment Installation Checks

Use this reference when `check_environment.py --json` reports missing or
incompatible Java, Nextflow, nf-core, git, or container tooling.

## Required Checks

- Java runtime: Nextflow requires a compatible Java installation.
- Nextflow executable: needed for all nf-core command execution.
- nf-core helper: useful for pipeline validation and local nf-core operations.
- git: required for pulling pipelines and many nf-core workflows.
- Container backend: Singularity, Apptainer, Docker, or another approved profile.

## Plugin Command

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/check_environment.py --json
```

Use the JSON result to report missing tools and install hints. Do not install
Java, Nextflow, nf-core, Docker, Singularity, or Apptainer unless the user
explicitly approves environment mutation.

## Environment Policy

- Prefer the active Python environment or project-local tools when installation
  is approved.
- For unknown or system Python environments, generate a plan rather than
  changing the environment directly.
- On HPC, confirm the intended profile, work directory, queue or node policy,
  and available container cache before expensive runs.

## Before Real Execution

Run command construction in dry-run mode:

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline rnaseq --input samplesheet.csv --outdir results/rnaseq --profile singularity --dry-run --json
```

Only execute after explicit approval with `--approved true`.
