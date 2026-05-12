from __future__ import annotations

from pathlib import Path

from .errors import InputNotFound, OmicsError


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def plugin_root() -> Path:
    return repo_root() / "plugins" / "omics-analysis"


def resolve_path(path: str | Path, base: str | Path | None = None) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path(base or Path.cwd()) / candidate
    return candidate.resolve()


def require_input(path: str | Path, base: str | Path | None = None) -> Path:
    candidate = resolve_path(path, base)
    if not candidate.exists():
        raise InputNotFound(str(candidate))
    return candidate


def prepare_outdir(path: str | Path, force: bool = False, base: str | Path | None = None) -> Path:
    outdir = resolve_path(path, base)
    if outdir.exists() and any(outdir.iterdir()) and not force:
        # Existing non-empty result dirs are allowed so commands can resume and reports can append.
        return outdir
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir


def assert_not_input_overwrite(input_path: str | Path, output_path: str | Path) -> None:
    if resolve_path(input_path) == resolve_path(output_path):
        raise OmicsError(
            "UnsafeOutputPath",
            "Output path resolves to the input path.",
            "Choose a separate output file or directory.",
            "validate_paths",
        )
