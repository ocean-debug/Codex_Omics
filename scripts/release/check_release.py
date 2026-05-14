from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    tomllib = None


FORBIDDEN_PARTS = {".git", ".env", ".venv", "venv", "tools", "results", "logs"}
FORBIDDEN_PREFIXES = ("data/test/result/",)
REQUIRED_PLUGIN_FILES = {
    ".codex-plugin/plugin.json",
    "skills/omics-router/SKILL.md",
    "skills/nf-core-universal/SKILL.md",
    "skills/single-cell-rna-qc/SKILL.md",
    "skills/scvi-universal/SKILL.md",
    "schemas/omics_run_spec.schema.json",
    "schemas/run_manifest.schema.json",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Codex Omics release readiness.")
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--plugin-package")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    failures: list[str] = []

    pyproject_version = read_pyproject_version(repo_root / "pyproject.toml")
    init_version = read_init_version(repo_root / "src" / "omics_codex" / "__init__.py")
    plugin = json.loads((repo_root / "plugins" / "omics-analysis" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    versions = {"pyproject": pyproject_version, "package": init_version, "plugin": plugin["version"]}
    if len(set(versions.values())) != 1:
        failures.append(f"Version mismatch: {versions}")

    for required in REQUIRED_PLUGIN_FILES:
        if not (repo_root / "plugins" / "omics-analysis" / required).exists():
            failures.append(f"Missing plugin file: {required}")

    if args.plugin_package:
        failures.extend(check_plugin_zip(Path(args.plugin_package)))

    result = {"status": "failed" if failures else "ok", "versions": versions, "failures": failures}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


def read_init_version(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            return line.split("=", 1)[1].strip().strip('"')
    return "unknown"


def read_pyproject_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if tomllib is not None:
        return tomllib.loads(text)["project"]["version"]
    in_project = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[project]":
            in_project = True
            continue
        if in_project and stripped.startswith("["):
            break
        if in_project and stripped.startswith("version"):
            return stripped.split("=", 1)[1].strip().strip('"')
    return "unknown"


def check_plugin_zip(path: Path) -> list[str]:
    failures: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        for required in REQUIRED_PLUGIN_FILES:
            if required not in names:
                failures.append(f"Plugin package missing: {required}")
        for name in names:
            normalized = Path(name).as_posix()
            if any(part in FORBIDDEN_PARTS for part in Path(name).parts) or normalized.startswith(FORBIDDEN_PREFIXES):
                failures.append(f"Plugin package contains forbidden path: {name}")
            if name.endswith((".h5ad", ".fastq.gz", ".fq.gz", ".mtx.gz")):
                failures.append(f"Plugin package contains large data-like file: {name}")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
