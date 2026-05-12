from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


NFCORE_REGISTRY_URLS = [
    "https://nf-co.re/pipelines.json",
    "https://raw.githubusercontent.com/nf-core/website/master/public/pipelines.json",
]


def list_pipelines() -> list[dict[str, Any]]:
    from shutil import which

    if which("nf-core"):
        try:
            completed = subprocess.run(
                ["nf-core", "pipelines", "list", "--json"],
                text=True,
                capture_output=True,
                timeout=60,
                check=False,
            )
            if completed.returncode == 0 and completed.stdout.strip():
                parsed = json.loads(completed.stdout)
                return normalize_registry(parsed)
        except Exception:
            pass
    return fetch_registry()


def fetch_registry() -> list[dict[str, Any]]:
    try:
        import requests
    except ImportError:
        return []
    for url in NFCORE_REGISTRY_URLS:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return normalize_registry(response.json())
        except Exception:
            continue
    return []


def normalize_registry(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        items = payload.get("pipelines") or payload.get("remote_workflows") or payload.get("workflows") or []
    else:
        items = payload
    normalized: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, str):
            normalized.append({"name": item})
            continue
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("full_name") or item.get("id")
        if not name:
            continue
        normalized.append(
            {
                "name": str(name).replace("nf-core/", ""),
                "description": item.get("description") or item.get("summary") or "",
                "latest_release": item.get("latest_release") or item.get("latest_version") or item.get("version"),
                "repository": item.get("repository") or item.get("url") or f"https://github.com/nf-core/{str(name).replace('nf-core/', '')}",
                "archived": bool(item.get("archived", False)),
            }
        )
    return normalized


def inspect_pipeline(pipeline: str) -> dict[str, Any]:
    short = pipeline.replace("nf-core/", "")
    for item in list_pipelines():
        if item.get("name") == short:
            return item
    return {
        "name": short,
        "description": "",
        "latest_release": None,
        "repository": f"https://github.com/nf-core/{short}",
        "archived": False,
    }


def write_registry_cache(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(list_pipelines(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
