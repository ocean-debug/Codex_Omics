from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    tomllib = None


FORBIDDEN_PARTS = {".git", ".env", ".venv", "venv", "tools", "results", "logs", "src"}
FORBIDDEN_PREFIXES = ("data/test/result/", "src/omics_codex/")
FORBIDDEN_TEXT = "omics-codex"
REQUIRED_PLUGIN_FILES = {
    ".codex-plugin/plugin.json",
    "skills/omics-router/SKILL.md",
    "skills/single-cell-rna-qc/SKILL.md",
    "skills/single-cell-rna-qc/scripts/check_environment.py",
    "skills/single-cell-rna-qc/scripts/qc_analysis.py",
    "skills/scvi-tools/SKILL.md",
    "skills/scvi-tools/scripts/check_environment.py",
    "skills/scvi-tools/scripts/train_model.py",
    "skills/nextflow-development/SKILL.md",
    "skills/nextflow-development/scripts/check_environment.py",
    "skills/nextflow-development/scripts/build_nextflow_command.py",
    "scripts/common/env.py",
    "scripts/common/manifest.py",
    "scripts/common/report.py",
}
P0_HELP_SCRIPTS = [
    "plugins/omics-analysis/skills/single-cell-rna-qc/scripts/qc_analysis.py",
    "plugins/omics-analysis/skills/scvi-tools/scripts/train_model.py",
    "plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Codex-Omics plugin-only release readiness.")
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--plugin-package")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    failures: list[str] = []

    pyproject_version = read_pyproject_version(repo_root / "pyproject.toml")
    plugin = json.loads((repo_root / "plugins" / "omics-analysis" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    versions = {"pyproject": pyproject_version, "plugin": plugin["version"]}
    if len(set(versions.values())) != 1:
        failures.append(f"Version mismatch: {versions}")

    plugin_root = repo_root / "plugins" / "omics-analysis"
    for required in REQUIRED_PLUGIN_FILES:
        if not (plugin_root / required).exists():
            failures.append(f"Missing plugin file: {required}")

    failures.extend(check_no_backend_imports(plugin_root))
    failures.extend(check_help_scripts(repo_root))

    if args.plugin_package:
        failures.extend(check_plugin_zip(Path(args.plugin_package)))

    result = {"status": "failed" if failures else "ok", "versions": versions, "failures": failures}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


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


def check_no_backend_imports(plugin_root: Path) -> list[str]:
    failures: list[str] = []
    for script in plugin_root.rglob("*.py"):
        text = script.read_text(encoding="utf-8")
        if "omics_codex" in text:
            failures.append(f"Plugin script imports backend package: {script.relative_to(plugin_root)}")
    return failures


def check_help_scripts(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for script in P0_HELP_SCRIPTS:
        completed = subprocess.run([sys.executable, script, "--help"], cwd=repo_root, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            failures.append(f"Help command failed for {script}: {completed.stderr}")
    return failures


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
            if name.endswith((".h5ad", ".fastq.gz", ".fq.gz", ".mtx.gz", ".h5")):
                failures.append(f"Plugin package contains large data-like file: {name}")
            if name.endswith((".md", ".py", ".json", ".yaml", ".yml")):
                try:
                    text = archive.read(name).decode("utf-8", errors="replace")
                except Exception:
                    continue
                if FORBIDDEN_TEXT in text:
                    failures.append(f"Plugin package contains removed CLI reference in: {name}")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
