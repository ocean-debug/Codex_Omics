# Plugin Installation

Codex-Omics is distributed as a plugin-only bundle. The plugin root is:

```text
plugins/omics-analysis/
```

It contains:

```text
.codex-plugin/plugin.json
skills/
scripts/common/
schemas/
```

Load this directory in a Codex environment that supports local plugin loading. No project-level backend CLI is required for basic skill use.

After loading, Codex should read the relevant `SKILL.md` and run that skill's local scripts.
