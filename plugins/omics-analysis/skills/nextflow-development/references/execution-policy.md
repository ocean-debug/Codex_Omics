# Nextflow Execution Policy

Real Nextflow execution can be long-running, expensive, and dependent on HPC/container state. Always start with environment checks and command dry-run. Run only after explicit approval with `--approved true`.

Preserve:

- `command.sh`
- stdout/stderr logs
- `.nextflow.log` when available
- `run_manifest.json`
- `report.md`

Common failure classes:

- Java runtime mismatch
- missing Nextflow or nf-core
- missing Singularity/Apptainer/Docker
- pipeline pull or GitHub network failure
- container pull failure
- samplesheet or parameter validation failure
