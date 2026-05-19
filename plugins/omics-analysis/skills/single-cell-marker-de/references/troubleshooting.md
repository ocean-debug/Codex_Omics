# Troubleshooting

## Missing Grouping Column

Use `--groupby` with an existing `.obs` column. After preprocessing, `leiden` may be absent if Leiden clustering was skipped or `leidenalg` is unavailable.

## Too Few Cells Per Group

Lower `--min-cells-per-group` only for smoke tests. For real analysis, small groups should usually be merged, removed, or re-clustered.

## Missing Raw Matrix

When `.raw` is absent, the skill uses X or the selected layer. Confirm that the selected matrix is suitable for marker ranking.

## Plot Failures

Plotting is optional. If plot generation fails, the marker table, summary, manifest, and report should still be written.
