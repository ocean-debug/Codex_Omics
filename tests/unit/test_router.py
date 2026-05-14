from __future__ import annotations

from omics_codex.router import build_request_spec, build_run_spec, build_template_spec, choose_skill, inspect_input_path, list_templates


def test_router_nfcore() -> None:
    assert choose_skill("Run nf-core/rnaseq on FASTQ files") == "nf-core-universal"
    assert choose_skill("Create a bulk RNA workflow") == "nf-core-universal"


def test_router_scvi() -> None:
    assert choose_skill("Use scVI to integrate batches") == "scvi-universal"


def test_router_scrna_qc() -> None:
    assert choose_skill("QC this h5ad single-cell file") == "single-cell-rna-qc"


def test_router_builds_nfcore_spec() -> None:
    spec = build_run_spec("Run nf-core/atacseq on this ATAC FASTQ directory", input_path="reads")
    assert spec["run"]["skill"] == "nf-core-universal"
    assert spec["nfcore"]["pipeline"] == "atacseq"
    assert spec["nfcore"]["profile"] == "singularity"
    assert spec["execution"]["approved"] is False


def test_router_builds_scanvi_spec() -> None:
    spec = build_run_spec("Use SCANVI for label transfer", input_path="adata.h5ad")
    assert spec["run"]["skill"] == "scvi-universal"
    assert spec["scvi"]["model"] == "SCANVI"
    assert "labels_key" in spec["scvi"]["setup_anndata"]


def test_inspect_input_path_fastq_dir(tmp_path) -> None:
    (tmp_path / "S1_R1.fastq.gz").write_text("", encoding="utf-8")
    (tmp_path / "S1_R2.fastq.gz").write_text("", encoding="utf-8")
    result = inspect_input_path(str(tmp_path))
    assert result["exists"]
    assert result["fastq_files"] == 2
    assert result["fastq_pairs"] == 1


def test_inspect_input_path_10x_mtx_dir(tmp_path) -> None:
    (tmp_path / "matrix.mtx.gz").write_text("", encoding="utf-8")
    result = inspect_input_path(str(tmp_path))
    assert result["type"] == "10x_mtx"
    assert result["has_10x_mtx"]


def test_router_builds_scrna_scvi_workflow_spec() -> None:
    spec = build_request_spec("Run a workflow with QC and scVI integration", input_path="adata.h5ad")
    assert spec["workflow"]["execution"]["approved"] is False
    assert [stage["name"] for stage in spec["workflow"]["stages"]] == ["scrna_qc", "scvi"]
    assert spec["workflow"]["stages"][1]["connect_from"]["stage"] == "scrna_qc"
    assert "doctor" in spec["codex_user_path"]["commands"][0]


def test_bulk_rna_workflow_does_not_route_to_scrna_scvi(tmp_path) -> None:
    (tmp_path / "sample_R1.fastq.gz").write_text("", encoding="utf-8")
    (tmp_path / "sample_R2.fastq.gz").write_text("", encoding="utf-8")

    spec = build_request_spec("Create a bulk RNA workflow", input_path=str(tmp_path), outdir="results/bulk")

    assert spec["workflow"]["name"] == "rnaseq_workflow"
    assert spec["workflow"]["execution"]["approved"] is False
    assert spec["workflow"]["stages"][0]["spec"]["nfcore"]["pipeline"] == "rnaseq"
    assert "bulk" in spec["workflow"]["stages"][0]["spec"]["outputs"]["outdir"]


def test_common_templates_are_safe_by_default() -> None:
    names = {item["name"] for item in list_templates()}
    assert {"bulk-rna", "atac", "scrna-qc", "scrna-qc-scvi", "scvi"} <= names

    bulk = build_template_spec("bulk-rna", outdir="results/bulk")
    assert bulk["workflow"]["execution"]["approved"] is False
    assert bulk["workflow"]["stages"][0]["spec"]["nfcore"]["pipeline"] == "rnaseq"

    scvi = build_template_spec("scvi", input_path="cells.h5ad", outdir="results/scvi")
    assert scvi["execution"]["approved"] is False
    assert scvi["run"]["skill"] == "scvi-universal"


def test_router_generates_nfcore_spec_from_fastq_directory(tmp_path) -> None:
    (tmp_path / "sample_1.fq.gz").write_text("", encoding="utf-8")
    (tmp_path / "sample_2.fq.gz").write_text("", encoding="utf-8")
    (tmp_path / "ref.fa").write_text("", encoding="utf-8")
    (tmp_path / "genes.gtf").write_text("", encoding="utf-8")

    spec = build_run_spec("Analyze these sequencing reads", input_path=str(tmp_path))

    assert spec["run"]["skill"] == "nf-core-universal"
    assert spec["execution"]["approved"] is False
    assert spec["inputs"]["inspection"]["fastq_pairs"] == 1
    assert spec["nfcore"]["profile"] == "singularity"
    assert spec["nfcore"]["params"]["fasta"].endswith("ref.fa")
    assert "Java 17+" in spec["requirements"]["software"][0]


def test_router_generates_scvi_spec_from_h5ad_directory(tmp_path) -> None:
    (tmp_path / "adata.h5ad").write_text("", encoding="utf-8")

    spec = build_run_spec("Create an scVI latent embedding", input_path=str(tmp_path))

    assert spec["run"]["skill"] == "scvi-universal"
    assert spec["inputs"]["inspection"]["h5ad_files"] == 1
    assert spec["inputs"]["path"].endswith("adata.h5ad")
    assert "scvi-tools" in spec["requirements"]["software"][0]
