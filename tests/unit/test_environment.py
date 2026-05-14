from __future__ import annotations

from pathlib import Path

from omics_codex.common.environment import detect_python_environment_type, doctor_environment, install_command_templates
from omics_codex.common.schema import validate_payload


def test_detects_conda_environment(tmp_path: Path) -> None:
    detected = detect_python_environment_type(
        {"CONDA_PREFIX": "/envs/codex", "CONDA_DEFAULT_ENV": "codex"},
        tmp_path,
    )
    assert detected["environment_type"] == "conda"
    assert detected["environment_manager"] == "conda"


def test_detects_uv_project_venv(tmp_path: Path) -> None:
    (tmp_path / "uv.lock").write_text("", encoding="utf-8")
    detected = detect_python_environment_type({"VIRTUAL_ENV": str(tmp_path / ".venv")}, tmp_path)
    assert detected["environment_type"] == "uv"
    assert detected["environment_manager"] == "uv"


def test_detects_standard_project_venv(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    detected = detect_python_environment_type({"VIRTUAL_ENV": str(tmp_path / ".venv")}, tmp_path)
    assert detected["environment_type"] == "venv"
    assert detected["environment_manager"] == "pip"


def test_install_templates_match_environment_types() -> None:
    assert install_command_templates("uv")["scvi"][0].startswith("uv pip")
    assert "mamba install" in install_command_templates("conda")["nfcore"][0]
    assert install_command_templates("venv")["scvi"][0].startswith("python -m pip")
    assert "No install command" in install_command_templates("system")["scvi"][0]


def test_doctor_reports_install_policy() -> None:
    payload = doctor_environment("scrna_qc")
    assert payload["install_policy"]["approval_required"] is True
    assert "python_environment" in payload
    assert "scrna_qc" in payload["task_status"]


def test_schema_loads_without_repo_plugin_root(monkeypatch) -> None:
    monkeypatch.setenv("CODEX_OMICS_PLUGIN_ROOT", "/definitely/not/a/plugin")
    errors = validate_payload(
        {
            "run": {"name": "demo", "type": "scrna_qc", "skill": "single-cell-rna-qc"},
            "inputs": {},
            "outputs": {"outdir": "results/demo"},
        },
        "omics_run_spec",
    )
    assert errors == []
