from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from common.env import detect_python_environment, inspect_gpu  # noqa: E402
from common.install_hints import build_install_plan  # noqa: E402
from common.io import ensure_outdir, write_json, write_text  # noqa: E402


def approved(value: str | bool) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes", "y"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan optional Codex-Omics dependency installation.")
    parser.add_argument("--task", required=True, choices=["scrna_qc", "scvi", "nfcore"])
    parser.add_argument("--project-root", default=Path.cwd())
    parser.add_argument("--output-dir", default="results/install_plan")
    parser.add_argument("--approved", default="false")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    outdir = ensure_outdir(args.output_dir)
    plan = build_install_plan(
        task=args.task,
        python_environment=detect_python_environment(cwd=args.project_root),
        gpu=inspect_gpu(),
        project_root=args.project_root,
    )
    plan["outputs"] = {"plan": str(outdir / "install_plan.json"), "log": str(outdir / "install.log")}

    if args.execute and approved(args.approved) and plan["status"] != "blocked":
        plan["execution"] = execute_supported_actions(plan, outdir)
    else:
        plan["execution"] = {
            "executed": False,
            "reason": "Run with --execute --approved true after reviewing the plan." if args.execute else "Plan-only mode.",
        }

    write_json(outdir / "install_plan.json", plan)
    print(json.dumps(plan, indent=2, sort_keys=True, default=str))
    if plan.get("execution", {}).get("executed"):
        failed = [action for action in plan["execution"].get("actions", []) if action.get("returncode", 0) != 0]
        return 1 if failed else 0
    return 0


def execute_supported_actions(plan: dict[str, Any], outdir: Path) -> dict[str, Any]:
    records = []
    log_lines = []
    for action in plan.get("actions", []):
        if not action.get("can_execute"):
            records.append({"name": action.get("name"), "executed": False, "reason": action.get("reason", "manual review required")})
            continue
        for command in action.get("commands", []):
            argv = shlex.split(command)
            completed = subprocess.run(argv, text=True, capture_output=True, check=False)
            log_lines.extend([f"$ {command}", completed.stdout, completed.stderr])
            records.append({"name": action.get("name"), "command": command, "returncode": completed.returncode})
    write_text(outdir / "install.log", "\n".join(log_lines))
    return {"executed": True, "actions": records}


if __name__ == "__main__":
    raise SystemExit(main())
