from __future__ import annotations

from omics_codex.router import build_run_spec, choose_skill, inspect_input_path


def test_router_nfcore() -> None:
    assert choose_skill("Run nf-core/rnaseq on FASTQ files") == "nf-core-universal"


def test_router_scvi() -> None:
    assert choose_skill("Use scVI to integrate batches") == "scvi-universal"


def test_router_scrna_qc() -> None:
    assert choose_skill("QC this h5ad single-cell file") == "single-cell-rna-qc"


def test_router_builds_nfcore_spec() -> None:
    spec = build_run_spec("Run nf-core/atacseq on this ATAC FASTQ directory", input_path="reads")
    assert spec["run"]["skill"] == "nf-core-universal"
    assert spec["nfcore"]["pipeline"] == "atacseq"
    assert spec["execution"]["approved"] is False


def test_router_builds_scanvi_spec() -> None:
    spec = build_run_spec("Use SCANVI for label transfer", input_path="adata.h5ad")
    assert spec["run"]["skill"] == "scvi-universal"
    assert spec["scvi"]["model"] == "SCANVI"
    assert "labels_key" in spec["scvi"]["setup_anndata"]


def test_inspect_input_path_fastq_dir(tmp_path) -> None:
    (tmp_path / "S1_R1.fastq.gz").write_text("", encoding="utf-8")
    result = inspect_input_path(str(tmp_path))
    assert result["exists"]
    assert result["fastq_files"] == 1
