from __future__ import annotations

from omics_codex.common.manifest import base_manifest
from omics_codex.common.schema import validate_payload
from omics_codex.report import render_report


def test_base_manifest_validates() -> None:
    manifest = base_manifest(skill="nf-core-universal", status="planned", inputs={}, outputs={})
    assert validate_payload(manifest, "run_manifest") == []
    assert "packages" in manifest["software"]


def test_report_includes_summary() -> None:
    manifest = base_manifest(skill="single-cell-rna-qc", status="completed", inputs={}, outputs={})
    rendered = render_report(manifest, {"qc": {"n_cells": 10}})
    assert "## Summary" in rendered
    assert '"n_cells": 10' in rendered
