from __future__ import annotations

from omics_codex.nfcore.samplesheet import infer_sample_from_r1, make_samplesheet, required_columns_for_pipeline, validate_samplesheet


def test_infer_sample_from_r1() -> None:
    assert infer_sample_from_r1("S1_R1.fastq.gz") == "S1"


def test_validate_samplesheet_example() -> None:
    errors = validate_samplesheet("examples/nfcore_rnaseq/samplesheet.csv", ["sample", "fastq_1", "fastq_2"])
    assert errors == []


def test_make_atacseq_samplesheet(tmp_path) -> None:
    fastq = tmp_path / "fastq"
    fastq.mkdir()
    (fastq / "S1_R1.fastq.gz").write_text("", encoding="utf-8")
    (fastq / "S1_R2.fastq.gz").write_text("", encoding="utf-8")
    output = tmp_path / "samplesheet.csv"
    result = make_samplesheet("atacseq", fastq, output)
    assert result["valid"]
    assert result["records"] == 1
    assert validate_samplesheet(output, required_columns_for_pipeline("atacseq")) == []


def test_make_sarek_samplesheet(tmp_path) -> None:
    fastq = tmp_path / "fastq"
    fastq.mkdir()
    (fastq / "Tumor_R1.fastq.gz").write_text("", encoding="utf-8")
    (fastq / "Tumor_R2.fastq.gz").write_text("", encoding="utf-8")
    output = tmp_path / "samplesheet.csv"
    result = make_samplesheet("sarek", fastq, output)
    assert result["valid"]
    assert validate_samplesheet(output, required_columns_for_pipeline("sarek")) == []
