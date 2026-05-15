from __future__ import annotations

import argparse
import inspect
import json

CURATED = ["SCVI", "SCANVI", "TOTALVI", "PEAKVI", "MULTIVI", "SOLO", "AUTOZI", "LDVAE", "DestVI"]


def list_models() -> list[dict[str, object]]:
    try:
        import scvi
    except Exception as exc:
        return [{"name": name, "available": False, "curated": True, "reason": f"scvi-tools unavailable: {exc}"} for name in CURATED]
    discovered = {}
    for name, cls in inspect.getmembers(scvi.model, inspect.isclass):
        if name.startswith("_"):
            continue
        discovered[name] = {
            "name": name,
            "available": True,
            "curated": name in CURATED,
            "module": cls.__module__,
            "has_setup_anndata": hasattr(cls, "setup_anndata"),
            "has_train": hasattr(cls, "train"),
            "has_save": hasattr(cls, "save"),
        }
    for name in CURATED:
        discovered.setdefault(name, {"name": name, "available": False, "curated": True, "reason": "model class not found"})
    return [discovered[name] for name in sorted(discovered)]


def main() -> int:
    parser = argparse.ArgumentParser(description="List installed scvi-tools model classes.")
    parser.add_argument("--config")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--write-manifest", action="store_true")
    parser.parse_args()
    print(json.dumps({"models": list_models()}, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
