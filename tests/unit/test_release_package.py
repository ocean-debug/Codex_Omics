from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

from scripts.release.check_release import check_plugin_zip


def test_build_plugin_package(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/release/build_plugin_package.py", "--outdir", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    package = tmp_path / "codex-omics-plugin-v0.4.0.zip"
    assert package.exists()
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
    assert ".codex-plugin/plugin.json" in names
    assert "skills/omics-router/SKILL.md" in names
    assert "schemas/omics_run_spec.schema.json" in names
    assert not any(name.startswith(".git/") or name.startswith("tools/") for name in names)


def test_check_release_package(tmp_path: Path) -> None:
    subprocess.run([sys.executable, "scripts/release/build_plugin_package.py", "--outdir", str(tmp_path)], check=True)
    package = tmp_path / "codex-omics-plugin-v0.4.0.zip"
    completed = subprocess.run(
        [sys.executable, "scripts/release/check_release.py", "--plugin-package", str(package)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert '"status": "ok"' in completed.stdout


def test_check_release_package_rejects_result_directory(tmp_path: Path) -> None:
    package = tmp_path / "bad-plugin.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr(".codex-plugin/plugin.json", "{}")
        archive.writestr("data/test/result/report.json", "{}")

    failures = check_plugin_zip(package)

    assert any("data/test/result/report.json" in failure for failure in failures)
