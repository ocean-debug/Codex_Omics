# nf-core/scrnaseq

Use this reference for single-cell or single-nucleus FASTQ planning with
nf-core/scrnaseq `4.1.0`.

## Samplesheet

The first three columns must be:

```csv
sample,fastq_1,fastq_2
sample1,/abs/path/sample1_R1.fastq.gz,/abs/path/sample1_R2.fastq.gz
```

Optional metadata columns can be merged with `--metadata`, including
`expected_cells`, `seq_center`, `fastq_barcode`, and `sample_type`.

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline scrnaseq --input fastq_dir --out samplesheet.csv --metadata metadata.csv
```

## Command Construction

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline scrnaseq --input samplesheet.csv --outdir results/scrnaseq --profile singularity --aligner cellranger --protocol 10x --genome GRCh38 --dry-run --json
```

Default revision is `4.1.0`. Use `--fasta` and `--gtf` for custom references,
or `--cellranger-index` when running Cell Ranger-compatible workflows.
Additional official pipeline parameters can be passed as repeatable
`--extra-param KEY=VALUE`.

## Key Outputs

- Per-sample aligner outputs from Cell Ranger, STARsolo, simpleaf, or kallisto.
- Count matrices and quality-control summaries.
- MultiQC and pipeline information files.

## Review Points

- Confirm the aligner and protocol match the library chemistry.
- Confirm `expected_cells` and sample metadata before interpreting QC metrics.
- Keep execution planned until references and container availability are known.
