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

## RNA-seq resume and container cache policy

For nf-core/rnaseq retries, keep the original work directory and rerun with `-resume`; do not delete work directories or outputs unless the user explicitly requests cleanup. If report, timeline, trace, or DAG files already exist, build the retry command with `--overwrite-reports`.

When a Singularity/Apptainer pull from `depot.galaxyproject.org` times out, first increase the generated pull timeout with `--pull-timeout "4 h"`. If the server network is still the bottleneck, pre-download the missing image once, place it in the configured Nextflow container cache using the cache filename Nextflow expects, and rerun with `-resume`.

For acceptance testing on a user-managed server, do not spend repeated long runs proving a slow remote registry. Once the timeout is classified and the cache workaround is documented, continue from the cached image or stop testing at the user's direction.
