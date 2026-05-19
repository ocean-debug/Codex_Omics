# nf-core Workflow Adapter Template

Use this checklist when adding a new nf-core pipeline to the existing
`nextflow-development` skill. Do not create a new skill unless the workflow
needs non-Nextflow logic, custom analysis code, or a separate execution model.

## Official Facts To Collect

- Pipeline name, for example `nf-core/<pipeline>`.
- Version or revision to pin by default.
- Official usage, output, and parameter/schema links.
- Required samplesheet columns and any optional metadata columns.
- Required reference inputs and common optional parameters.
- Key outputs that agents should inspect after execution.
- Known caveats, slow container behavior, or resume considerations.

## Adapter Changes

- Add samplesheet behavior to `generate_samplesheet.py`.
  - Preserve required leading columns exactly as documented by nf-core.
  - Merge optional metadata from `--metadata` when useful.
  - Return structured JSON errors instead of tracebacks for invalid metadata.
- Add command behavior to `build_nextflow_command.py`.
  - Add a default revision when the user requested a fixed version.
  - Prefer explicit flags for common parameters.
  - Use repeatable `--extra-param KEY=VALUE` for low-frequency nf-core options.
  - Keep default behavior dry-run/planned.
- Add router keywords in `omics-router/scripts/route_omics.py`.
  - Include the pipeline name and common assay/tool synonyms.
  - Route to `nextflow-development`, not a new skill.
  - Keep the adapter inside the `nextflow-development` tool-family skill unless
    it needs a separate non-Nextflow execution model.
- Add a pipeline reference by copying `references/pipelines/_template.md`.
- Add a minimal example under `examples/nfcore_<pipeline>/`.
- Add unit tests for samplesheet generation, command construction, and routing.

## Safety Rules

- Do not install Java, Nextflow, nf-core, container tools, references, or vendor
  tools from the adapter.
- Do not run real Nextflow by default.
- Do not copy long official documentation into this repository; summarize the
  local workflow contract and link official docs.
- Do not put pipeline-specific logic in unrelated skills.
- Keep outputs under the requested outdir and preserve manifests/reports.

## Test Checklist

- `python -m compileall -q plugins scripts tests`
- `python scripts/release/check_release.py`
- `python -m pytest tests -q` when pytest is available.
- Unit test: generated samplesheet has the exact required leading columns.
- Unit test: command includes the expected `nf-core/<pipeline>` and revision.
- Unit test: router prompt selects `nextflow-development` and the pipeline.
- Unit test: `SKILL.md` reference links still exist.
