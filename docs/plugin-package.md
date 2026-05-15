# Plugin Package

Build the plugin package:

```bash
python scripts/release/build_plugin_package.py
python scripts/release/check_release.py --plugin-package dist/codex-omics-plugin-v1.0.0.zip
```

The package contains plugin metadata, skills, local scripts, common runtime helpers, schemas, references, examples, and minimal documentation.

It excludes `.git`, `.env`, virtual environments, project-local tools, caches, results, and large data files.

The package is valid only when P0 skill scripts can run `--help` without installing this repository as a Python package.
