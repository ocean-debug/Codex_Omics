# Agent Integration

Agents should treat Codex-Omics as a plugin-local skill collection.

Required behavior:

- Read the selected skill's `SKILL.md`.
- Run `scripts/check_environment.py --json` before analysis.
- Use dry-run or planned mode first.
- Ask before installing dependencies or executing long tasks.
- Use `--approved true` only after explicit user approval.
- Keep data local and write outputs under user-controlled directories.

Do not bypass skill-local scripts with one-off analysis code unless the selected skill cannot cover the task.
