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
