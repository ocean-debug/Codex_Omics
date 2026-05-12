# Schema-driven nf-core parameters

Use this reference when configuring a pipeline that is not covered by a curated adapter, when params validation fails, or when the user asks why a parameter is required.

## Contract

- Treat `nextflow_schema.json` as the source of truth for parameter names, defaults, types, enums, help text, and required fields.
- Do not invent params that are absent from the schema unless the user explicitly provides a Nextflow parameter that is documented elsewhere.
- Keep user-provided values in `nfcore.params` in `omics_run_spec.yaml`.
- Record whether `nfcore.version` is a pinned release or the explicit string `latest`.
- When a schema cannot be fetched, stop at command planning and report `PipelineSchemaMissing` with a suggested fix.

## Parameter workflow

1. Inspect the pipeline name and version from `nfcore.pipeline` and `nfcore.version`.
2. Fetch or locate `nextflow_schema.json` with:

   ```bash
   omics-codex nfcore create-params <pipeline> --version <version> --out params.json
   ```

3. Build a params template from schema defaults.
4. Merge user-provided params from `omics_run_spec.yaml`.
5. Validate params with:

   ```bash
   omics-codex nfcore validate-params --pipeline <pipeline> --version <version> --params params.yaml
   ```

6. Generate the Nextflow command only after validation or with an explicit note that schema validation was unavailable.

## Required handling

- Preserve schema-derived field names exactly.
- Convert Python booleans into Nextflow flags only when true.
- Omit params with null values.
- Quote command arguments safely.
- Keep `--outdir` in params or derive it from `outputs.outdir`.

## Failure modes

- `PipelineSchemaMissing`: network unavailable, wrong pipeline name, or unsupported version.
- `InvalidRunSpec`: required project fields are missing before pipeline-specific validation.
- `InvalidPipelineParams`: schema validation found type, enum, or format errors.

## Notes for implementers

The current implementation builds commands through `omics_codex.nfcore.command.build_nextflow_command`. Schema helpers live in `omics_codex.nfcore.schema_tools`.
