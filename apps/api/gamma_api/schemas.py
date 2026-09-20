from __future__ import annotations

from typing import Any, Literal

try:
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover - dependency guard for bare validation environment
    BaseModel = object  # type: ignore[misc,assignment]

    def Field(default: object = None, **_: object) -> object:  # type: ignore[no-redef]
        return default


class SourceCreate(BaseModel):
    source_type: Literal["document", "dataset", "web", "other"]
    origin: dict[str, Any]
    domain: str = Field(min_length=1)
    governance: Literal["public", "deidentified", "governed", "restricted"]
    checksum: str | None = None
    language: str | None = None
    owner: str | None = None
    license: str | None = None
    jurisdiction: str | None = None
    acquisition_time: str | None = None
    ingestion_policy: dict[str, Any] = Field(default_factory=dict)


class SourceResponse(BaseModel):
    source_id: str
    registration_status: Literal["registered"]


class IngestionJobCreate(BaseModel):
    source_id: str
    pipeline_version: str = Field(min_length=1)
    requested_operations: list[str] = Field(min_length=1)
    priority: int = Field(default=5, ge=0, le=10)


class IngestionJobResponse(BaseModel):
    job_id: str
    source_id: str
    pipeline_version: str
    requested_operations: list[str]
    priority: int
    status: str


class ResponseEnvelope(BaseModel):
    data: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    details: dict[str, Any]
    request_id: str | None
    retryable: bool
