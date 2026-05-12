---
name: skill-authoring-kit
description: Create new extensible Codex Omics analysis skills that follow this plugin's contracts: SKILL.md, optional references, deterministic scripts, omics_run_spec schema extension, examples, tests, reports, and run manifests. Use when adding spatial transcriptomics, scATAC-seq, proteomics, Ribo-seq, metabolomics, multiomics, or paper-to-workflow omics skills.
---

# Omics Skill Authoring Kit

## Required workflow

1. Define the new omics task, input formats, output contract, safety rules, and expected runtime.
2. Create `plugins/omics-analysis/skills/<new-skill>/SKILL.md` with concise trigger metadata.
3. Implement reusable code under `src/omics_codex/<new_domain>/` and thin wrappers under `plugins/omics-analysis/scripts/<new_domain>/`.
4. Add schema fields or a new schema only when the shared run spec cannot represent the workflow.
5. Add examples and tests that can run on the remote `codex-omics` environment.
6. Ensure every run writes a manifest and report.
7. Bootstrap starter files with `omics-codex skill-template create --name <skill-name> --outdir <dir>` when useful.

## Naming

- Use lowercase hyphen-case for skill names.
- Keep Python package modules underscore_case.
- Do not add notebooks as the primary implementation; notebooks may be generated outputs only.

## When to read references

- Read `references/new-skill-template.md` before creating a new executable omics skill.
