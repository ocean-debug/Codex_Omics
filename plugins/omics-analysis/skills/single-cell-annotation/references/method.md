# Single-cell Annotation Method

This skill provides a user-facing cell type annotation entrypoint.

Supported backend interfaces:

- `marker-based`: local marker reference, approved execution supported.
- `celltypist`: local CellTypist model path, dependency/resource checks only in this release.
- `singler`: local SingleR reference path and R environment checks only in this release.
- `scanvi`: local SCANVI model/reference handoff checks only in this release.

The marker-based backend scores each group from `obs[groupby]` against a local
marker reference. The top label and confidence are assigned to all cells in that
group, then written to a copied `annotated.h5ad`.

Annotations are hypotheses. Review them against marker evidence, QC, batch
structure, and experimental design before biological claims.
