# Parameter Policy

- Default workflow mode is plan-only.
- `--batch-key` defaults to `batch` for integration.
- `--groupby` defaults to `leiden` for annotation and marker detection.
- `--marker-reference` and `--gene-sets` are optional in planning, but must exist before approved child execution.
- Skip flags remove optional branches from the plan without changing child skill behavior.
