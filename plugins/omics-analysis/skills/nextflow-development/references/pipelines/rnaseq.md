# nf-core/rnaseq

Use this reference for bulk RNA-seq FASTQ inputs, gene expression quantification,
QC summaries, and downstream count matrices.

## Samplesheet

Expected columns:

```csv
sample,fastq_1,fastq_2,strandedness
sample1,/abs/path/sample1_R1.fastq.gz,/abs/path/sample1_R2.fastq.gz,auto
```

- `sample`: stable sample identifier.
- `fastq_1`: R1 FASTQ path.
- `fastq_2`: R2 FASTQ path, or empty for single-end data.
- `strandedness`: `auto`, `forward`, `reverse`, or `unstranded`.

Generate:

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline rnaseq --input fastq_dir --out samplesheet.csv
```

## Command Construction

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline rnaseq --input samplesheet.csv --outdir results/rnaseq --profile singularity --dry-run --json
```

Add `--pull-timeout "4 h" --overwrite-reports --resume` for slow HPC container
registries or retries.

## Common Parameters

- `--genome`: reference key when using an iGenomes-supported organism.
- `--fasta` and `--gtf`: custom reference paths when not using a genome key.
- `--aligner`: aligner choice when exposed by the selected pipeline version.
- Resource caps: CPU, memory, and time limits should match the execution site.

## Key Outputs

- MultiQC report for aggregate QC.
- Gene count table for downstream differential expression.
- TPM or normalized expression tables when produced by the selected pipeline.
- Pipeline info, trace, and report files for reproducibility.

## Review Points

- Confirm species and genome build before approved execution.
- Confirm strandedness when automatic detection is not reliable.
- Use output count matrices for downstream DESeq2, edgeR, or similar tools only
  after checking sample metadata and design.
