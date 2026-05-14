from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


EXCLUDED_PARTS = {".git", ".env", ".venv", "venv", "__pycache__", ".pytest_cache", "tools", "results", "logs"}
EXCLUDED_SUFFIXES = {".pyc", ".h5ad", ".h5", ".mtx", ".gz", ".fastq", ".fq"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Codex Omics standard plugin package.")
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--outdir", default="dist")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    plugin_root = repo_root / "plugins" / "omics-analysis"
    metadata = json.loads((plugin_root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    version = metadata["version"]
    outdir = (repo_root / args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    target = outdir / f"codex-omics-plugin-v{version}.zip"

    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        add_tree(archive, plugin_root, plugin_root)
        for relative in [
            "README.md",
            "LICENSE",
            "docs/plugin-package.md",
            "docs/environment-setup.md",
            "docs/agent-integration.md",
            "AGENTS.md",
        ]:
            source = repo_root / relative
            if source.exists():
                archive.write(source, relative)
        manifest = {
            "package": target.name,
            "plugin": metadata["name"],
            "version": version,
            "entrypoint": ".codex-plugin/plugin.json",
            "install_policy": "diagnose first; install only after explicit user approval",
        }
        archive.writestr("release-manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "ok", "package": str(target), "version": version}, indent=2, sort_keys=True))
    return 0


def add_tree(archive: zipfile.ZipFile, root: Path, base: Path) -> None:
    for path in sorted(root.rglob("*")):
        if path.is_dir() or should_exclude(path):
            continue
        archive.write(path, path.relative_to(base).as_posix())


def should_exclude(path: Path) -> bool:
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return True
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    if path.name.startswith(".env"):
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
