# Nextflow Troubleshooting

Use this reference when nf-core command construction or approved execution
fails. Start from the generated `run_manifest.json`, `report.md`, `command.sh`,
stderr/stdout logs, and `.nextflow.log` when present.

## Common Failure Classes

- Java runtime missing or incompatible.
- Nextflow or nf-core missing.
- Container backend missing or blocked.
- Pipeline pull or GitHub network failure.
- Samplesheet validation failure.
- Container pull timeout.
- Existing reports blocking a resumed run.

## Container Pull Timeout

Symptoms:

- `.nextflow.log` shows a long image download from `depot.galaxyproject.org`.
- Execution exits after the default pull timeout.
- Manifest or report classifies the issue as a container pull timeout.

Actions:

- Rebuild the command with `--pull-timeout "4 h"` when the network is slow.
- Add `--singularity-pull-docker-container` to make nf-core modules use their
  Docker/OCI container names instead of `depot.galaxyproject.org` Singularity
  URLs when `task.ext.singularity_pull_docker_container` is implemented.
- Add `--overwrite-reports` if report, timeline, trace, or DAG files already
  exist.
- Use `--resume` to continue from the existing work directory.
- If the remote registry is the bottleneck, pre-cache the missing image in the
  configured Singularity or Apptainer cache using the filename Nextflow expects.

## Resume Policy

- Keep the original work directory for retries.
- Prefer `-resume` over restarting from scratch.
- Do not delete outputs, `.nextflow` state, or container caches unless the user
  explicitly asks for cleanup.

## Samplesheet Problems

Actions:

- Regenerate the samplesheet with `generate_samplesheet.py`.
- Compare the columns with `references/samplesheets.md` and the pipeline page
  under `references/pipelines/`.
- Use absolute paths for FASTQ files when running on remote or HPC systems.

## Evidence to Preserve

- `command.sh`
- stdout and stderr logs
- `.nextflow.log`
- `run_manifest.json`
- `report.md`
- MultiQC report or key pipeline output inventory when available
