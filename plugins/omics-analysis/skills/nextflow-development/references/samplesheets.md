# nf-core Samplesheets

Supported curated samplesheet adapters:

- `rnaseq`: `sample,fastq_1,fastq_2,strandedness`
- `scrnaseq`: `sample,fastq_1,fastq_2`
- `riboseq`: `sample,fastq_1,fastq_2,strandedness,type`
- `spatialvi` raw: `sample,fastq_dir,image,cytaimage,colorizedimage,darkimage,slide,area,manual_alignment,slidefile`
- `spatialvi` processed: `sample,spaceranger_dir`
- `atacseq`: `sample,fastq_1,fastq_2,replicate`
- `sarek`: `patient,sex,status,sample,lane,fastq_1,fastq_2`

FASTQ discovery supports common paired-end naming such as:

- `sample_R1.fastq.gz` / `sample_R2.fastq.gz`
- `sample_1.fq.gz` / `sample_2.fq.gz`
- `sample.R1.fastq.gz` / `sample.R2.fastq.gz`

For `riboseq`, `fastq_2` may be empty for single-end Ribo-seq libraries.
The `type` column must be one of `riboseq`, `rnaseq`, or `tiseq`. Extra
metadata columns such as `treatment`, `pair`, and `sample_description` can be
merged from `--metadata` and are needed for translational efficiency contrasts.

For `scrnaseq`, keep the first three columns fixed and merge optional metadata
such as `expected_cells`, `seq_center`, `fastq_barcode`, and `sample_type` with
`--metadata`.

For `spatialvi`, provide `--metadata`. Raw Visium rows require `fastq_dir` and
at least one of `image`, `cytaimage`, `colorizedimage`, or `darkimage`.
Processed Space Ranger rows require `spaceranger_dir`.
