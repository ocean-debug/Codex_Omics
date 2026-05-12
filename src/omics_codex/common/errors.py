from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class OmicsError(Exception):
    error_type: str
    message: str
    suggested_fix: str | None = None
    failed_step: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": "failed",
            "error_type": self.error_type,
            "message": self.message,
        }
        if self.suggested_fix:
            payload["suggested_fix"] = self.suggested_fix
        if self.failed_step:
            payload["failed_step"] = self.failed_step
        return payload


class InputNotFound(OmicsError):
    def __init__(self, path: str, failed_step: str = "validate_input") -> None:
        super().__init__(
            "InputNotFound",
            f"Input path does not exist: {path}",
            "Check the path or generate the required example fixture.",
            failed_step,
        )


class InvalidRunSpec(OmicsError):
    def __init__(self, message: str, suggested_fix: str | None = None) -> None:
        super().__init__("InvalidRunSpec", message, suggested_fix, "validate_run_spec")


class MissingSoftware(OmicsError):
    def __init__(self, name: str, suggested_fix: str | None = None) -> None:
        super().__init__(
            "MissingSoftware",
            f"Required software is not available: {name}",
            suggested_fix or f"Install {name} in the active environment.",
            "inspect_environment",
        )


class ModelUnavailable(OmicsError):
    def __init__(self, model_name: str) -> None:
        super().__init__(
            "ModelUnavailable",
            f"scvi-tools model is not available in this environment: {model_name}",
            "Install a scvi-tools version that provides this model or choose another registered model.",
            "scvi_registry",
        )
