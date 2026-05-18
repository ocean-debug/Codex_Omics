# nf-core/riboseq

Use this reference for Ribo-seq, TI-seq, and translational efficiency planning
with nf-core/riboseq `1.2.0`.

## Samplesheet

The first five columns must be:

```csv
sample,fastq_1,fastq_2,strandedness,type
sample1,/abs/path/sample1_R1.fastq.gz,,auto,riboseq
```

- `sample`: stable sample identifier; repeated runs for one sample share the
  same value.
- `fastq_1`: gzipped FASTQ R1.
- `fastq_2`: gzipped FASTQ R2, or empty for single-end libraries.
- `strandedness`: `auto`, `forward`, `reverse`, or `unstranded`.
- `type`: `riboseq`, `rnaseq`, or `tiseq`.

Generate a basic Ribo-seq sheet:

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline riboseq --input fastq_dir --out samplesheet.csv --sample-type riboseq
```

For translational efficiency, merge metadata by `sample`:

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/generate_samplesheet.py --pipeline riboseq --input fastq_dir --out samplesheet.csv --metadata metadata.csv
```

Metadata may include `type`, `sample_description`, `pair`, and `treatment`.

## Contrasts

Translational efficiency analysis requires a contrasts CSV:

```csv
id,variable,reference,target,batch,pair
treated_vs_control,treatment,control,treated,,pair
```

The `variable` column must name a samplesheet metadata column that separates the
groups. `pair` is optional but should be supplied for matched RNA-seq/Ribo-seq
designs when available.

## Command Construction

```bash
python plugins/omics-analysis/skills/nextflow-development/scripts/build_nextflow_command.py --pipeline riboseq --revision 1.2.0 --input samplesheet.csv --outdir results/riboseq --profile singularity --fasta genome.fa --gtf genes.gtf --contrasts contrasts.csv --singularity-pull-docker-container --dry-run --json
```

Use explicit `--fasta` and `--gtf` for reproducibility when possible. If using
an iGenomes key, review the nf-core/riboseq documentation for annotation age and
identifier caveats before approved execution.

When `depot.galaxyproject.org` is slow, use
`--singularity-pull-docker-container` so nf-core modules switch from depot SIF
URLs to Docker/OCI container names and let Singularity/Apptainer build the local
cache image.

## Key Outputs

- Preprocessing and FastQC/MultiQC reports.
- STAR alignment outputs and logs.
- Ribo-TISH or Ribotricer Ribo-seq QC and ORF prediction outputs.
- riboWaltz P-site offsets and diagnostic plots.
- Salmon quantification tables.
- anota2seq translational efficiency outputs when `--contrasts` is supplied.
- Pipeline info, trace, timeline, and command records.

## Review Points

- Check strandedness inference in MultiQC when using `auto`.
- Confirm sample `type` values before TE analysis; mixed RNA-seq and Ribo-seq
  samples must be clearly distinguished.
- Confirm `treatment` and `pair` metadata before interpreting TE contrasts.
- Treat ORF predictions and translational efficiency results as computational
  outputs that require biological review.
