# nf-core/sarek

Use this reference for WGS or WES FASTQ inputs, germline or somatic variant
calling, tumor-normal analysis, and VCF/BAM output review.

## Samplesheet

Expected columns:

```csv
patient,sex,status,sample,lane,fastq_1,fastq_2
patient1,XX,0,normal,L001,/abs/path/normal_R1.fastq.gz,/abs/path/normal_R2.fastq.gz
patient1,XX,1,tumor,L001,/abs/path/tumor_R1.fastq.gz,/abs/path/tumor_R2.fastq.gz
```

- `patient`: patient or subject identifier.
- `sex`: sample sex metadata when required by the pipeline version.
- `status`: tumor or normal status encoding expected by the pipeline.
- `sample`: sample identifier.
- `lane`: sequencing lane identifier.
- `fastq_1` and `fastq_2`: FASTQ paths.

Generate:

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline sarek --input fastq_dir --out samplesheet.csv
```

## Command Construction

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline sarek --input samplesheet.csv --outdir results/sarek --profile singularity --dry-run --json
```

Use dry-run output to review the command, reference configuration, and resource
expectations before approved execution.

## Common Parameters

- `--genome`: reference key when supported.
- Custom FASTA, known sites, intervals, and annotation resources for nonstandard
  references.
- Variant caller or analysis tool selection when exposed by the pipeline.
- Resource caps for alignment, recalibration, and variant calling.

## Key Outputs

- Recalibrated BAM or CRAM files.
- VCF or gVCF variant calls.
- QC and MultiQC summaries.
- Pipeline info, trace, and report files.

## Review Points

- Confirm WGS versus WES before selecting intervals or capture targets.
- Confirm tumor-normal pairing and status encoding.
- Confirm reference genome compatibility across FASTQ metadata, FASTA, known
  sites, and annotation files.
