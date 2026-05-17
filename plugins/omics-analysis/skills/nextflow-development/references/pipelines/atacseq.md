# nf-core/atacseq

Use this reference for bulk ATAC-seq FASTQ inputs, chromatin accessibility QC,
peak calling, bigWig tracks, and MultiQC summaries.

## Samplesheet

Expected columns:

```csv
sample,fastq_1,fastq_2,replicate
control,/abs/path/control_R1.fastq.gz,/abs/path/control_R2.fastq.gz,1
```

- `sample`: biological sample or condition name.
- `fastq_1`: R1 FASTQ path.
- `fastq_2`: R2 FASTQ path, or empty for single-end data.
- `replicate`: replicate number for the sample.

Generate:

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline atacseq --input fastq_dir --out samplesheet.csv
```

## Command Construction

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline atacseq --input samplesheet.csv --outdir results/atacseq --profile singularity --dry-run --json
```

Use `--resume` for retries after environment or container fixes.

## Common Parameters

- `--genome`: reference key for supported organisms.
- Custom reference paths when a standard genome key is not appropriate.
- Resource caps for alignment, peak calling, and QC processes.

## Key Outputs

- MultiQC report.
- Peak calls, usually narrowPeak-style outputs.
- bigWig coverage tracks.
- Alignment and QC summaries.
- Pipeline info, trace, and report files.

## Review Points

- Confirm genome build and blacklist compatibility.
- Confirm replicate structure before generating the samplesheet.
- Treat peak files as computational results that require downstream biological
  review and sample-level QC inspection.
