# Pathway Enrichment Method

This skill performs lightweight over-representation analysis from a marker table or gene list.

Default method:

1. Load genes from `markers.csv`, a DE table, or a plain text gene list.
2. Split genes by `group` when the column is present.
3. Keep the top `N` genes per group.
4. Load local gene sets from GMT or CSV/TSV.
5. Run a hypergeometric test for each group and term.
6. Apply Benjamini-Hochberg correction.
7. Write enrichment tables, manifest, and report.

The skill does not download external pathway databases.
