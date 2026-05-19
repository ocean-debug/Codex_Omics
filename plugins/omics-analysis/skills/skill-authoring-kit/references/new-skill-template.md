# New Skill Template

Use this layout:

```text
plugins/omics-analysis/skills/<new-skill>/
  SKILL.md
  scripts/
    check_environment.py
    validate_input.py
    run.py
    summarize.py
  references/
    method.md
    parameters.md
    troubleshooting.md
    output-contract.md
  schemas/
    run.schema.json
  examples/
    minimal.json
```

Script contract:

- `--help`
- `--json`
- `--dry-run`
- `--approved true`
- `--write-manifest`

Use `plugins/omics-analysis/scripts/common/` for shared environment checks, manifest writing, reports, and safe command execution.

## Registry Metadata

Every new skill must be registered in `plugins/omics-analysis/skill_registry.yaml`.
Keep the directory flat under `skills/<skill-id>/` and express the architecture
role with registry metadata:

```yaml
layer: task
domain: single_cell
backends: [scanpy]
composes: []
public_entrypoint: true
maturity: experimental
```

- `task`: user-facing analysis task with stable inputs and outputs.
- `tool_family`: adapter for a complex tool ecosystem.
- `workflow`: composition plan that calls other skills and aggregates manifests.
- `system`: router, report, authoring, or safety infrastructure.
