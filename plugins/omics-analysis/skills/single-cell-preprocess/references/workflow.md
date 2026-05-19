# Workflow

```mermaid
flowchart TD
  A["filtered.h5ad"] --> B["check_environment.py"]
  B --> C["validate_input.py"]
  C --> D["plan.py / dry-run"]
  D --> E{"approved true?"}
  E -- "no" --> F["run_manifest.json + report.md"]
  E -- "yes" --> G["run.py"]
  G --> H["normalize_total + log1p"]
  H --> I["HVG + scale + PCA"]
  I --> J["neighbors + UMAP + Leiden"]
  J --> K["preprocessed.h5ad + preprocess_summary.json"]
  K --> L["run_manifest.json + report.md"]
```
