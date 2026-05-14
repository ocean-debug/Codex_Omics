# Plugin Package

The v0.4 standard deliverable is a plugin package:

```text
codex-omics-plugin-v0.4.0.zip
```

It contains plugin metadata, skills, schemas, references, scripts, and minimal documentation. It does not include `.git`, `.env`, virtual environments, project-local tools, caches, results, or large data files.

## Build

```bash
python scripts/release/build_plugin_package.py
python scripts/release/check_release.py --plugin-package dist/codex-omics-plugin-v0.4.0.zip
```

## Load

Unzip the package and load the extracted plugin root in a Codex environment that supports local plugin loading. The plugin root is the directory containing:

```text
.codex-plugin/plugin.json
skills/
schemas/
scripts/
```

## Use

The plugin should guide Codex to call the backend CLI:

```bash
omics-codex doctor --json
omics-codex inspect-data --input /path/to/input
omics-codex template list
omics-codex workflow plan --config workflow.json
```

Long analysis runs require explicit user approval in the generated spec.
