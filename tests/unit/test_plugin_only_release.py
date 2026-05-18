from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path

from scripts.release.check_release import check_plugin_zip


def test_plugin_scripts_do_not_import_backend_package() -> None:
    for script in Path("plugins/omics-analysis").rglob("*.py"):
        assert "omics_codex" not in script.read_text(encoding="utf-8"), script


def test_skill_reference_links_exist() -> None:
    skill_paths = [
        Path("plugins/omics-analysis/skills/scvi-tools/SKILL.md"),
        Path("plugins/omics-analysis/skills/nextflow-development/SKILL.md"),
    ]
    for skill_path in skill_paths:
        text = skill_path.read_text(encoding="utf-8")
        for reference in re.findall(r"`(references/[^`]+\.md)`", text):
            assert (skill_path.parent / reference).exists(), f"{skill_path}: {reference}"


def test_migrated_alias_skills_are_removed() -> None:
    removed_aliases = ["nf-core-universal", "scvi-universal"]
    for alias in removed_aliases:
        assert not (Path("plugins/omics-analysis/skills") / alias).exists()
    for path in [*Path("examples").rglob("*"), *Path("plugins/omics-analysis").rglob("*")]:
        if path.is_file() and path.suffix in {".md", ".py", ".json", ".yaml", ".yml"}:
            text = path.read_text(encoding="utf-8")
            for alias in removed_aliases:
                assert alias not in text, f"{path}: {alias}"


def test_build_and_check_plugin_package(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/release/build_plugin_package.py", "--outdir", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    package = tmp_path / "codex-omics-plugin-v1.0.0.zip"
    assert package.exists()

    check = subprocess.run(
        [sys.executable, "scripts/release/check_release.py", "--plugin-package", str(package)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert check.returncode == 0, check.stdout + check.stderr
    assert '"status": "ok"' in check.stdout


def test_release_check_rejects_backend_cli_text(tmp_path: Path) -> None:
    package = tmp_path / "bad.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr(".codex-plugin/plugin.json", "{}")
        archive.writestr("skills/single-cell-rna-qc/SKILL.md", "use omics-codex")
    failures = check_plugin_zip(package)
    assert any("removed CLI reference" in failure for failure in failures)


def test_extracted_package_help_runs_without_repo_pythonpath(tmp_path: Path) -> None:
    subprocess.run([sys.executable, "scripts/release/build_plugin_package.py", "--outdir", str(tmp_path)], check=True)
    package = tmp_path / "codex-omics-plugin-v1.0.0.zip"
    extract = tmp_path / "plugin"
    with zipfile.ZipFile(package) as archive:
        archive.extractall(extract)
    script = extract / "skills" / "single-cell-rna-qc" / "scripts" / "qc_analysis.py"
    completed = subprocess.run([sys.executable, str(script), "--help"], cwd=tmp_path, text=True, capture_output=True, check=False)
    assert completed.returncode == 0, completed.stderr
    assert "usage:" in completed.stdout
