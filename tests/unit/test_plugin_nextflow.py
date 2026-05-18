from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def test_nextflow_samplesheet_generation(tmp_path: Path) -> None:
    (tmp_path / "sample_R1.fastq.gz").write_text("", encoding="utf-8")
    (tmp_path / "sample_R2.fastq.gz").write_text("", encoding="utf-8")
    sheet = tmp_path / "samplesheet.csv"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py",
            "--pipeline",
            "rnaseq",
            "--input",
            str(tmp_path),
            "--out",
            str(sheet),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    with sheet.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["sample"] == "sample"
    assert rows[0]["fastq_1"].endswith("sample_R1.fastq.gz")
    assert rows[0]["fastq_2"].endswith("sample_R2.fastq.gz")


def test_riboseq_samplesheet_generation_allows_single_end(tmp_path: Path) -> None:
    (tmp_path / "ribo_R1.fastq.gz").write_text("", encoding="utf-8")
    sheet = tmp_path / "samplesheet.csv"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py",
            "--pipeline",
            "riboseq",
            "--input",
            str(tmp_path),
            "--out",
            str(sheet),
            "--sample-type",
            "riboseq",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    with sheet.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert reader.fieldnames == ["sample", "fastq_1", "fastq_2", "strandedness", "type"]
    assert rows[0]["sample"] == "ribo"
    assert rows[0]["fastq_2"] == ""
    assert rows[0]["type"] == "riboseq"


def test_riboseq_samplesheet_merges_te_metadata(tmp_path: Path) -> None:
    (tmp_path / "ribo_R1.fastq.gz").write_text("", encoding="utf-8")
    (tmp_path / "rna_R1.fastq.gz").write_text("", encoding="utf-8")
    (tmp_path / "rna_R2.fastq.gz").write_text("", encoding="utf-8")
    metadata = tmp_path / "metadata.csv"
    metadata.write_text(
        "sample,type,treatment,pair,sample_description\n"
        "ribo,riboseq,treated,1,Ribo treated\n"
        "rna,rnaseq,treated,1,RNA treated\n",
        encoding="utf-8",
    )
    sheet = tmp_path / "samplesheet.csv"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py",
            "--pipeline",
            "riboseq",
            "--input",
            str(tmp_path),
            "--out",
            str(sheet),
            "--metadata",
            str(metadata),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    with sheet.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = {row["sample"]: row for row in reader}
    assert reader.fieldnames[:5] == ["sample", "fastq_1", "fastq_2", "strandedness", "type"]
    assert {"treatment", "pair", "sample_description"}.issubset(set(reader.fieldnames or []))
    assert rows["ribo"]["type"] == "riboseq"
    assert rows["rna"]["type"] == "rnaseq"
    assert rows["ribo"]["treatment"] == "treated"
    assert rows["rna"]["pair"] == "1"


def test_riboseq_samplesheet_reports_missing_metadata_as_json_error(tmp_path: Path) -> None:
    (tmp_path / "ribo_R1.fastq.gz").write_text("", encoding="utf-8")
    sheet = tmp_path / "samplesheet.csv"
    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py",
            "--pipeline",
            "riboseq",
            "--input",
            str(tmp_path),
            "--out",
            str(sheet),
            "--metadata",
            str(tmp_path / "missing_metadata.csv"),
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["errors"][0]["error_type"] == "InvalidMetadata"
    assert "does not exist" in payload["errors"][0]["message"]
    assert "Traceback" not in completed.stderr


def test_scrnaseq_samplesheet_merges_metadata(tmp_path: Path) -> None:
    (tmp_path / "sample_R1.fastq.gz").write_text("", encoding="utf-8")
    (tmp_path / "sample_R2.fastq.gz").write_text("", encoding="utf-8")
    metadata = tmp_path / "metadata.csv"
    metadata.write_text("sample,expected_cells,seq_center\nsample,5000,core\n", encoding="utf-8")
    sheet = tmp_path / "samplesheet.csv"

    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py",
            "--pipeline",
            "scrnaseq",
            "--input",
            str(tmp_path),
            "--out",
            str(sheet),
            "--metadata",
            str(metadata),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    with sheet.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert reader.fieldnames[:3] == ["sample", "fastq_1", "fastq_2"]
    assert {"expected_cells", "seq_center"}.issubset(set(reader.fieldnames or []))
    assert rows[0]["expected_cells"] == "5000"
    assert rows[0]["seq_center"] == "core"


def test_spatialvi_raw_samplesheet_from_metadata(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.csv"
    metadata.write_text(
        "sample,fastq_dir,image,slide,area,manual_alignment,slidefile\n"
        "visium1,/fastq,/images/tissue.jpg,V19A01,A1,false,\n",
        encoding="utf-8",
    )
    sheet = tmp_path / "spatialvi_raw.csv"

    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py",
            "--pipeline",
            "spatialvi",
            "--input",
            str(tmp_path),
            "--out",
            str(sheet),
            "--metadata",
            str(metadata),
            "--spatial-mode",
            "raw",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["spatial_mode"] == "raw"
    with sheet.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert reader.fieldnames[:10] == ["sample", "fastq_dir", "image", "cytaimage", "colorizedimage", "darkimage", "slide", "area", "manual_alignment", "slidefile"]
    assert rows[0]["sample"] == "visium1"
    assert rows[0]["image"] == "/images/tissue.jpg"


def test_spatialvi_raw_samplesheet_requires_image_metadata(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.csv"
    metadata.write_text("sample,fastq_dir,slide,area\nvisium1,/fastq,V19A01,A1\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py",
            "--pipeline",
            "spatialvi",
            "--input",
            str(tmp_path),
            "--out",
            str(tmp_path / "spatialvi_raw.csv"),
            "--metadata",
            str(metadata),
            "--spatial-mode",
            "raw",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    payload = json.loads(completed.stdout)
    assert payload["errors"][0]["error_type"] == "InvalidMetadata"
    assert "at least one of image" in payload["errors"][0]["message"]


def test_spatialvi_processed_samplesheet_from_metadata(tmp_path: Path) -> None:
    metadata = tmp_path / "metadata.csv"
    metadata.write_text("sample,spaceranger_dir\nvisium1,/spaceranger/outs\n", encoding="utf-8")
    sheet = tmp_path / "spatialvi_processed.csv"

    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py",
            "--pipeline",
            "spatialvi",
            "--input",
            str(tmp_path),
            "--out",
            str(sheet),
            "--metadata",
            str(metadata),
            "--spatial-mode",
            "processed",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["spatial_mode"] == "processed"
    with sheet.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert reader.fieldnames == ["sample", "spaceranger_dir"]
    assert rows[0]["spaceranger_dir"] == "/spaceranger/outs"


def test_nextflow_failure_classifies_container_pull_timeout() -> None:
    script = Path("plugins/omics-analysis/skills/nextflow-development/scripts/run_nextflow.py")
    spec = importlib.util.spec_from_file_location("run_nextflow", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    failure = module.classify_failure(
        """
        Failed to pull singularity image
          status : 143
          hint   : Try and increase singularity.pullTimeout in the config (current is "20m")
          INFO:    Downloading network image
        """
    )

    assert failure["error_type"] == "ContainerPullTimeout"
    assert "pullTimeout" in failure["suggested_fix"]


def test_nextflow_failure_classifies_ribotish_annotation_error_before_historical_pulls() -> None:
    script = Path("plugins/omics-analysis/skills/nextflow-development/scripts/run_nextflow.py")
    spec = importlib.util.spec_from_file_location("run_nextflow", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    failure = module.classify_failure(
        """
        Pulling Singularity image docker://quay.io/biocontainers/samtools:1.21
        Process `NFCORE_RIBOSEQ:RIBOSEQ:RIBOTISH_PREDICT_INDIVIDUAL (A3_Ribo_CNS)` terminated with an error exit status (1)
        Command output:
          Wrong CDS annotation: ENSMMUG00000001060 ENSMMUT00000001510 0 14905 14904
        Command error:
          File "/usr/local/lib/python3.10/site-packages/ribotish/zbio/interval.py", line 299, in cds_region_trans
            thick.sort()
          TypeError: '<' not supported between instances of 'NoneType' and 'int'
        """
    )

    assert failure["error_type"] == "RiboTishAnnotationIncompatibility"
    assert "--skip_ribotish true" in failure["suggested_fix"]


def test_nextflow_command_can_write_pull_timeout_config(tmp_path: Path) -> None:
    sheet = tmp_path / "samplesheet.csv"
    sheet.write_text("sample,fastq_1,fastq_2\ns,a_R1.fastq.gz,a_R2.fastq.gz\n", encoding="utf-8")
    outdir = tmp_path / "plan"

    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py",
            "--pipeline",
            "rnaseq",
            "--input",
            str(sheet),
            "--outdir",
            str(outdir),
            "--profile",
            "singularity",
            "--pull-timeout",
            "4 h",
            "--singularity-pull-docker-container",
            "--overwrite-reports",
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    command = (outdir / "command.sh").read_text(encoding="utf-8")
    config = (outdir / "nextflow.config").read_text(encoding="utf-8")
    assert "-c" in command
    assert "nextflow.config" in command
    assert "pullTimeout = '4 h'" in config
    assert "ext.singularity_pull_docker_container = true" in config
    assert "report { overwrite = true }" in config
    params = (outdir / "params.yaml").read_text(encoding="utf-8")
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert "input:" in params
    assert "outdir:" in params
    assert manifest["outputs"]["params_file"].endswith("params.yaml")
    assert manifest["schema_validation"]["status"] == "not_provided"


def test_riboseq_command_includes_reference_and_contrasts(tmp_path: Path) -> None:
    sheet = tmp_path / "samplesheet.csv"
    sheet.write_text("sample,fastq_1,fastq_2,strandedness,type\ns,a_R1.fastq.gz,,auto,riboseq\n", encoding="utf-8")
    contrasts = tmp_path / "contrasts.csv"
    contrasts.write_text("id,variable,reference,target,batch,pair\nx,treatment,control,treated,,pair\n", encoding="utf-8")
    outdir = tmp_path / "plan"

    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py",
            "--pipeline",
            "riboseq",
            "--input",
            str(sheet),
            "--outdir",
            str(outdir),
            "--profile",
            "singularity",
            "--revision",
            "1.2.0",
            "--fasta",
            "genome.fa",
            "--gtf",
            "genes.gtf",
            "--contrasts",
            str(contrasts),
            "--skip-ribotish",
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    command = (outdir / "command.sh").read_text(encoding="utf-8")
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert "nf-core/riboseq" in command
    assert "-r 1.2.0" in command
    assert "--fasta genome.fa" in command
    assert "--gtf genes.gtf" in command
    assert "--contrasts" in command
    assert "--skip_ribotish true" in command
    assert manifest["parameters"]["revision"] == "1.2.0"
    assert manifest["inputs"]["contrasts"] == str(contrasts)
    assert manifest["parameters"]["skip_ribotish"] is True
    assert (outdir / "params.yaml").exists()


def test_skip_ribotish_is_rejected_for_non_riboseq_pipeline(tmp_path: Path) -> None:
    sheet = tmp_path / "samplesheet.csv"
    sheet.write_text("sample,fastq_1,fastq_2\ns,a_R1.fastq.gz,a_R2.fastq.gz\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py",
            "--pipeline",
            "rnaseq",
            "--input",
            str(sheet),
            "--outdir",
            str(tmp_path / "plan"),
            "--skip-ribotish",
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "--skip-ribotish is only supported with --pipeline riboseq" in completed.stderr


def test_scrnaseq_command_defaults_revision_and_accepts_aligner_protocol(tmp_path: Path) -> None:
    sheet = tmp_path / "samplesheet.csv"
    sheet.write_text("sample,fastq_1,fastq_2\ns,a_R1.fastq.gz,a_R2.fastq.gz\n", encoding="utf-8")
    outdir = tmp_path / "plan"

    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py",
            "--pipeline",
            "scrnaseq",
            "--input",
            str(sheet),
            "--outdir",
            str(outdir),
            "--aligner",
            "cellranger",
            "--protocol",
            "10x",
            "--cellranger-index",
            "/refs/cellranger",
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    command = (outdir / "command.sh").read_text(encoding="utf-8")
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert "nf-core/scrnaseq" in command
    assert "-r 4.1.0" in command
    assert "--aligner cellranger" in command
    assert "--protocol 10x" in command
    assert "--cellranger_index /refs/cellranger" in command
    assert manifest["parameters"]["revision"] == "4.1.0"


def test_spatialvi_command_defaults_dev_and_accepts_spaceranger_options(tmp_path: Path) -> None:
    sheet = tmp_path / "samplesheet.csv"
    sheet.write_text("sample,spaceranger_dir\nvisium1,/outs\n", encoding="utf-8")
    outdir = tmp_path / "plan"

    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py",
            "--pipeline",
            "spatialvi",
            "--input",
            str(sheet),
            "--outdir",
            str(outdir),
            "--spaceranger-reference",
            "/refs/spaceranger",
            "--spaceranger-probeset",
            "/refs/probes.csv",
            "--hd-bin-size",
            "8",
            "--skip-integration",
            "--skip-downstream",
            "--extra-param",
            "custom_flag=value",
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    command = (outdir / "command.sh").read_text(encoding="utf-8")
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert "nf-core/spatialvi" in command
    assert "-r dev" in command
    assert "--spaceranger_reference /refs/spaceranger" in command
    assert "--spaceranger_probeset /refs/probes.csv" in command
    assert "--hd_bin_size 8" in command
    assert "--skip_integration true" in command
    assert "--skip_downstream true" in command
    assert "--custom_flag value" in command
    assert manifest["parameters"]["revision"] == "dev"
    assert manifest["parameters"]["extra_params"] == {"custom_flag": "value"}
    assert (outdir / "params.yaml").read_text(encoding="utf-8").count("custom_flag") == 1


def test_nextflow_command_inspects_local_pipeline_schema(tmp_path: Path) -> None:
    sheet = tmp_path / "samplesheet.csv"
    sheet.write_text("sample,fastq_1,fastq_2\ns,a_R1.fastq.gz,a_R2.fastq.gz\n", encoding="utf-8")
    schema = tmp_path / "nextflow_schema.json"
    schema.write_text(json.dumps({"type": "object", "properties": {"input": {}, "outdir": {}, "aligner": {}}}), encoding="utf-8")
    outdir = tmp_path / "plan"

    completed = subprocess.run(
        [
            sys.executable,
            "plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py",
            "--pipeline",
            "scrnaseq",
            "--input",
            str(sheet),
            "--outdir",
            str(outdir),
            "--aligner",
            "cellranger",
            "--pipeline-schema",
            str(schema),
            "--dry-run",
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    manifest = json.loads((outdir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_validation"]["status"] == "ok"
    assert "aligner" in manifest["schema_validation"]["declared_parameters"]


def test_multiqc_summary_handles_present_and_missing_data(tmp_path: Path) -> None:
    script = Path("plugins/omics-analysis/skills/nextflow-development/scripts/summarize_multiqc.py")
    spec = importlib.util.spec_from_file_location("summarize_multiqc", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    missing = module.summarize_multiqc(tmp_path)
    assert missing["status"] == "missing"

    data_dir = tmp_path / "nfcore_out" / "multiqc" / "multiqc_data"
    data_dir.mkdir(parents=True)
    (data_dir / "multiqc_data.json").write_text(
        json.dumps({"report_general_stats_data": [{"sample1": {"x": 1}}], "report_saved_raw_data": {"fastqc_data": {}}}),
        encoding="utf-8",
    )
    present = module.summarize_multiqc(tmp_path)
    assert present["status"] == "ok"
    assert present["summary"]["samples_in_general_stats"] == 1


def test_nextflow_failure_adds_auto_fix_plan() -> None:
    script = Path("plugins/omics-analysis/skills/nextflow-development/scripts/run_nextflow.py")
    spec = importlib.util.spec_from_file_location("run_nextflow", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    failure = module.classify_failure("unknown parameter --foo")
    assert failure["error_type"] == "InvalidPipelineParameters"
    assert failure["auto_fix_plan"]
