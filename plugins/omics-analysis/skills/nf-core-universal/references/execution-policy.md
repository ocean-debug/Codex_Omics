# nf-core execution policy

Use this reference before running or preparing long Nextflow jobs.

## Default mode

Default to `plan_then_execute` or `command_only` unless the run spec includes:

```yaml
execution:
  approved: true
```

The user must be shown:

- selected pipeline and version;
- input path and samplesheet;
- output directory;
- execution profile such as Docker, Singularity, Apptainer, Conda, or HPC profile;
- command;
- resume strategy;
- expected log locations.

## Modes

- `command_only`: generate command, params, manifest, and report paths. Do not execute.
- `dry_run`: validate config and prepare files. Do not run Nextflow unless the pipeline has a safe dry-run command.
- `test_profile`: run `-profile test,<profile>` when approved.
- `plan_then_execute`: show plan first, then run only after approval.
- `command_and_run`: run after validation when `approved: true`.

## Safety rules

- Do not delete input data.
- Do not overwrite non-empty output directories unless `execution.force: true`.
- Use `-resume` by default.
- Capture stdout/stderr and `.nextflow.log` paths in the manifest when execution occurs.
- Record failures as structured errors, not only free-text logs.

## Resource rules

- Honor `execution.max_cpus`, `execution.max_memory`, and `execution.max_time` when provided.
- For remote HPC runs, use the profile resource wrapper rather than embedding scheduler commands inside the Nextflow command unless the user requests it.
- Do not request larger allocations than the user specified.

## Output verification

Generic verification should check:

- output directory exists;
- `multiqc_report.html` if produced;
- non-empty file count;
- Nextflow exit status and logs if execution occurred.

Curated adapters can add pipeline-specific summaries.
