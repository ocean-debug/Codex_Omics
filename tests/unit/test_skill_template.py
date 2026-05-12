from __future__ import annotations

from omics_codex.skill_template import create_omics_skill_template


def test_create_omics_skill_template(tmp_path) -> None:
    result = create_omics_skill_template("Spatial Transcriptomics", tmp_path)
    assert result["skill"] == "spatial-transcriptomics"
    assert (tmp_path / "spatial-transcriptomics" / "SKILL.md").exists()
    assert (tmp_path / "spatial-transcriptomics" / "examples" / "omics_run_spec.yaml").exists()
