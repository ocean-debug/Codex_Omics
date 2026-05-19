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
        Path("plugins/omics-analysis/skills/omics-router/SKILL.md"),
        Path("plugins/omics-analysis/skills/omics-report/SKILL.md"),
        Path("plugins/omics-analysis/skills/single-cell-rna-qc/SKILL.md"),
        Path("plugins/omics-analysis/skills/single-cell-preprocess/SKILL.md"),
        Path("plugins/omics-analysis/skills/skill-authoring-kit/SKILL.md"),
    ]
    for skill_path in skill_paths:
        text = skill_path.read_text(encoding="utf-8")
        for reference in re.findall(r"`(references/[^`]+\.md)`", text):
            assert (skill_path.parent / reference).exists(), f"{skill_path}: {reference}"


def test_skill_registry_paths_are_complete() -> None:
    sys.path.insert(0, str(Path("plugins/omics-analysis/scripts")))
    from common.registry import load_skill_registry, validate_registry_paths

    registry = load_skill_registry()
    assert set(registry["skills"]) == {
        "omics-router",
        "nextflow-development",
        "scvi-tools",
        "single-cell-rna-qc",
        "single-cell-preprocess",
        "omics-report",
        "skill-authoring-kit",
    }
    allowed_layers = {"system", "task", "tool_family", "workflow"}
    allowed_domains = {"single_cell", "bulk_rna", "spatial", "multiomics", "reporting", "infrastructure"}
    allowed_maturity = {"experimental", "validated"}
    for entry in registry["skills"].values():
        for key in [
            "skill_id",
            "layer",
            "domain",
            "backends",
            "composes",
            "public_entrypoint",
            "maturity",
            "tasks",
            "input_formats",
            "constraints",
            "scripts",
            "schemas",
            "outputs",
            "approval",
            "reporting",
            "examples",
            "router_keywords",
            "workflow_diagram",
        ]:
            assert key in entry
        assert entry["layer"] in allowed_layers, entry["skill_id"]
        assert entry["domain"] in allowed_domains, entry["skill_id"]
        assert isinstance(entry["backends"], list), entry["skill_id"]
        assert isinstance(entry["composes"], list), entry["skill_id"]
        assert isinstance(entry["public_entrypoint"], bool), entry["skill_id"]
        assert entry["maturity"] in allowed_maturity, entry["skill_id"]
        assert entry["schemas"], entry["skill_id"]
        assert entry["workflow_diagram"], entry["skill_id"]
        assert entry["router_keywords"], entry["skill_id"]
    assert validate_registry_paths(registry) == []


def test_skill_directories_remain_flat() -> None:
    skill_root = Path("plugins/omics-analysis/skills")
    nested_skill_markers = [
        path for path in skill_root.glob("*/*/SKILL.md")
        if path.parent.parent.name not in {"references", "examples", "schemas", "scripts"}
    ]
    assert nested_skill_markers == []


def test_skill_registry_loads_without_pyyaml(monkeypatch) -> None:
    sys.path.insert(0, str(Path("plugins/omics-analysis/scripts")))
    monkeypatch.setitem(sys.modules, "yaml", None)
    from common.registry import load_skill_registry

    registry = load_skill_registry()
    assert "nextflow-development" in registry["skills"]


def test_single_cell_preprocess_registry_contract() -> None:
    sys.path.insert(0, str(Path("plugins/omics-analysis/scripts")))
    from common.registry import load_skill_registry

    entry = load_skill_registry()["skills"]["single-cell-preprocess"]
    assert entry["layer"] == "task"
    assert entry["domain"] == "single_cell"
    assert entry["backends"] == ["scanpy", "anndata"]
    assert entry["public_entrypoint"] is True
    assert "preprocess" in entry["router_keywords"]
    assert entry["approval"]["required_for_execution"] is True


def test_migrated_alias_skills_are_removed() -> None:
    removed_aliases = ["nf-core-universal", "scvi-universal"]
    for alias in removed_aliases:
        assert not (Path("plugins/omics-analysis/skills") / alias).exists()
    for path in [*Path("examples").rglob("*"), *Path("plugins/omics-analysis").rglob("*")]:
        if path.is_file() and path.suffix in {".md", ".py", ".json", ".yaml", ".yml"}:
            text = path.read_text(encoding="utf-8")
            for alias in removed_aliases:
                assert alias not in text, f"{path}: {alias}"


def test_nfcore_adapter_templates_exist_and_cover_required_sections() -> None:
    template = Path("plugins/omics-analysis/skills/nextflow-development/references/nfcore-workflow-adapter-template.md")
    pipeline_template = Path("plugins/omics-analysis/skills/nextflow-development/references/pipelines/_template.md")
    example_dir = Path("examples/nfcore_template")
    assert template.exists()
    assert pipeline_template.exists()
    assert (example_dir / "samplesheet.csv").exists()
    assert (example_dir / "metadata.csv").exists()
    assert (example_dir / "omics_run_spec.yaml").exists()

    template_text = template.read_text(encoding="utf-8")
    for required in ["Official Facts To Collect", "Adapter Changes", "Safety Rules", "Test Checklist"]:
        assert required in template_text
    for required in ["samplesheet", "command", "router", "tests"]:
        assert required in template_text.lower()

    pipeline_text = pipeline_template.read_text(encoding="utf-8")
    for required in ["Samplesheet", "Command Construction", "Key Outputs", "Review Points", "Troubleshooting Notes"]:
        assert required in pipeline_text

    spec_text = (example_dir / "omics_run_spec.yaml").read_text(encoding="utf-8")
    assert "mode: template_only" in spec_text
    assert "approved: false" in spec_text
    assert "replace_me" in spec_text


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
