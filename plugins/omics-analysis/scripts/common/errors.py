from __future__ import annotations

from typing import Any


def blocker(name: str, message: str, suggested_fix: str, failed_step: str) -> dict[str, Any]:
    return {
        "error_type": name,
        "message": message,
        "suggested_fix": suggested_fix,
        "failed_step": failed_step,
    }


def missing_software(name: str, suggested_fix: str, failed_step: str = "check_environment") -> dict[str, Any]:
    return blocker(
        "MissingSoftware",
        f"Required software is not available: {name}",
        suggested_fix,
        failed_step,
    )


def warning(name: str, message: str, suggested_fix: str) -> dict[str, Any]:
    return {
        "warning_type": name,
        "message": message,
        "suggested_fix": suggested_fix,
    }
