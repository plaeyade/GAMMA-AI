from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GammaError(Exception):
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    retryable: bool = False

    def to_response(self, request_id: str | None = None) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "request_id": request_id,
            "retryable": self.retryable,
        }


class NotFoundError(GammaError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} was not found.",
            details={"identifier": identifier},
            retryable=False,
        )


class ConflictError(GammaError):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(code=code, message=message, details=details or {}, retryable=False)
