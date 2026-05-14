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


def test_report_extracts_nfcore_and_scvi_key_sections() -> None:
    nfcore_manifest = base_manifest(
        skill="nf-core-universal",
        status="completed",
        inputs={},
        outputs={"outdir": "results/rna", "manifest": "results/rna/run_manifest.json", "report": "results/rna/report.md"},
        parameters={"nfcore": {"pipeline": "rnaseq", "profile": "singularity"}, "execution": {"max_cpus": 12}},
    )
    nfcore_report = render_report(nfcore_manifest, {"verification": {"multiqc_reports": ["multiqc_report.html"]}})
    assert "## Methods Summary" in nfcore_report
    assert "MultiQC" in nfcore_report
    assert "rnaseq" in nfcore_report

    scvi_manifest = base_manifest(
        skill="scvi-universal",
        status="completed",
        inputs={},
        outputs={"outdir": "results/scvi", "trained_h5ad": "results/scvi/trained.h5ad"},
        parameters={"scvi": {"model": "SCVI", "train": {"max_epochs": 2}, "downstream": {"latent_key": "X_scvi"}}},
    )
    scvi_report = render_report(scvi_manifest, {})
    assert "Latent key" in scvi_report
    assert "X_scvi" in scvi_report
