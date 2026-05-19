# Single-cell Marker DE Method

This skill ranks marker genes for groups in a preprocessed AnnData object.

Default method:

1. Load a preprocessed `.h5ad`.
2. Validate that the grouping column exists in `.obs`.
3. Check that at least two groups contain enough cells.
4. Run `scanpy.tl.rank_genes_groups`.
5. Export a long-form marker table with one row per group/gene.
6. Write a JSON summary and seven-section report.

The skill does not mutate the source h5ad file.
