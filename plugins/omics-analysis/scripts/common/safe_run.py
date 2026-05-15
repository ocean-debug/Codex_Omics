from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .io import write_text


def run_command(command: list[str] | str, *, cwd: str | Path | None = None, outdir: str | Path) -> dict[str, Any]:
    target = Path(outdir)
    target.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(command, shell=isinstance(command, str), cwd=cwd, text=True, capture_output=True, check=False)
    stdout_path = target / "stdout.log"
    stderr_path = target / "stderr.log"
    write_text(stdout_path, completed.stdout)
    write_text(stderr_path, completed.stderr)
    return {
        "returncode": completed.returncode,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }
